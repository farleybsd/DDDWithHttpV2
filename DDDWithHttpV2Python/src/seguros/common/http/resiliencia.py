"""Pipeline de resiliência para as chamadas HTTP entre contextos (o papel do Polly no C#).

Escrito "na mão" de propósito, para aprender: cada estratégia é uma classe pequena.

Ordem (mais externo -> mais interno), igual ao projeto C#:
    Limite de concorrência -> Retry -> Circuit Breaker -> Timeout por tentativa -> rede

O ``TransporteResiliente`` é um *transport* do httpx — o equivalente a um ``DelegatingHandler``
do HttpClient: fica entre o cliente e a rede e pode decidir repetir, recusar ou cortar a chamada.

Use apenas para chamadas idempotentes (consultas), já que o retry as repete.
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx

from seguros.common.settings import CircuitBreakerSettings, HttpResilienceSettings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------------------------
# Exceções de resiliência (equivalem a RateLimiterRejectedException, BrokenCircuitException e
# TimeoutRejectedException do Polly). O adaptador HTTP as traduz para "Indisponivel".
# ---------------------------------------------------------------------------------------------
class ErroDeResiliencia(Exception):
    """Base: a chamada foi recusada/interrompida pelo pipeline, não pela outra ponta."""


class LimiteDeConcorrenciaExcedido(ErroDeResiliencia):
    pass


class CircuitoAberto(ErroDeResiliencia):
    pass


class TempoLimiteExcedido(ErroDeResiliencia):
    pass


def eh_status_transitorio(status: int) -> bool:
    """5xx, 408 e 429 valem nova tentativa. 404 é resposta de negócio e NÃO entra no retry."""
    return status >= 500 or status in (408, 429)


# ---------------------------------------------------------------------------------------------
# 1) Limite de concorrência
# ---------------------------------------------------------------------------------------------
class LimitadorDeConcorrencia:
    """No máximo ``permitidas`` chamadas em andamento + ``fila`` aguardando. Acima disso a chamada
    é recusada na hora, em vez de a aplicação sobrecarregar a si mesma."""

    def __init__(self, permitidas: int, fila: int) -> None:
        self._semaforo = asyncio.Semaphore(permitidas)
        self._capacidade = permitidas + fila
        self._ocupados = 0  # em andamento + na fila

    # @asynccontextmanager transforma um gerador em algo usável com "async with".
    @asynccontextmanager
    async def reservar(self) -> AsyncIterator[None]:
        if self._ocupados >= self._capacidade:
            raise LimiteDeConcorrenciaExcedido("Limite de chamadas simultâneas atingido.")
        self._ocupados += 1
        try:
            async with self._semaforo:  # espera na "fila" até haver vaga
                yield
        finally:
            self._ocupados -= 1


# ---------------------------------------------------------------------------------------------
# 3) Circuit breaker
# ---------------------------------------------------------------------------------------------
class DisjuntorDeCircuito:
    """Se a proporção de falhas na janela de amostragem passar do limite, o circuito ABRE e as
    chamadas são recusadas sem ir à rede durante ``break_duration``. Depois disso fica
    MEIO-ABERTO: deixa passar uma chamada de teste; se der certo FECHA, se falhar ABRE de novo."""

    def __init__(
        self,
        nome: str,
        config: CircuitBreakerSettings,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._nome = nome
        self._config = config
        self._relogio = relogio
        self._amostras: deque[tuple[float, bool]] = deque()  # (instante, sucesso?)
        self._aberto_ate: float | None = None
        self._testando = False

    def antes_da_chamada(self) -> None:
        if self._aberto_ate is None:
            return  # FECHADO
        if self._relogio() < self._aberto_ate or self._testando:
            raise CircuitoAberto(f"Circuito '{self._nome}' aberto.")
        self._testando = True  # MEIO-ABERTO: esta é a chamada de teste
        logger.info("[%s] Circuito MEIO-ABERTO: enviando chamada de teste.", self._nome)

    def registrar(self, sucesso: bool) -> None:
        agora = self._relogio()

        if self._testando:
            self._testando = False
            if sucesso:
                self._aberto_ate = None
                self._amostras.clear()
                logger.info("[%s] Circuito FECHADO.", self._nome)
            else:
                self._abrir(agora)
            return

        self._amostras.append((agora, sucesso))
        inicio_da_janela = agora - self._config.sampling_duration_segundos
        while self._amostras and self._amostras[0][0] < inicio_da_janela:
            self._amostras.popleft()

        total = len(self._amostras)
        falhas = sum(1 for _, ok in self._amostras if not ok)
        if total >= self._config.minimum_throughput and falhas / total >= self._config.failure_ratio:
            self._abrir(agora)

    def _abrir(self, agora: float) -> None:
        self._aberto_ate = agora + self._config.break_duration_segundos
        self._amostras.clear()
        logger.warning(
            "[%s] Circuito ABERTO por %ss.", self._nome, self._config.break_duration_segundos
        )


# ---------------------------------------------------------------------------------------------
# O transport que junta tudo
# ---------------------------------------------------------------------------------------------
class TransporteResiliente(httpx.AsyncBaseTransport):
    def __init__(
        self,
        nome: str,
        interno: httpx.AsyncBaseTransport,
        config: HttpResilienceSettings,
    ) -> None:
        self._nome = nome
        self._interno = interno
        self._config = config
        self._limitador = LimitadorDeConcorrencia(
            config.concurrency_limiter.permit_limit, config.concurrency_limiter.queue_limit
        )
        self._disjuntor = DisjuntorDeCircuito(nome, config.circuit_breaker)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        # 1) Limite de concorrência: vale para a chamada inteira, incluindo retentativas.
        async with self._limitador.reservar():
            return await self._com_retry(request)

    async def _com_retry(self, request: httpx.Request) -> httpx.Response:
        # 2) Retry. CircuitoAberto NÃO é capturado aqui: com o circuito aberto não adianta repetir.
        maximo = self._config.retry.max_retry_attempts
        tentativa = 0
        while True:
            try:
                resposta = await self._tentar(request)
                if not eh_status_transitorio(resposta.status_code) or tentativa >= maximo:
                    return resposta
                motivo = f"status {resposta.status_code}"
                await resposta.aclose()
            except (httpx.TransportError, TempoLimiteExcedido) as erro:
                if tentativa >= maximo:
                    raise
                motivo = type(erro).__name__

            tentativa += 1
            espera = self._config.retry.base_delay_segundos * 2 ** (tentativa - 1)  # exponencial
            logger.warning(
                "[%s] Retentativa %d/%d de %s %s em %.2fs (motivo: %s).",
                self._nome, tentativa, maximo, request.method, request.url, espera, motivo,
            )
            await asyncio.sleep(espera)

    async def _tentar(self, request: httpx.Request) -> httpx.Response:
        # 3) Circuit breaker em volta de 4) timeout por tentativa.
        self._disjuntor.antes_da_chamada()
        try:
            resposta = await asyncio.wait_for(self._enviar(request), self._config.timeout_segundos)
        except TimeoutError:
            self._disjuntor.registrar(sucesso=False)
            raise TempoLimiteExcedido(
                f"Sem resposta em {self._config.timeout_segundos}s."
            ) from None
        except httpx.TransportError:
            self._disjuntor.registrar(sucesso=False)
            raise

        self._disjuntor.registrar(sucesso=not eh_status_transitorio(resposta.status_code))
        return resposta

    async def _enviar(self, request: httpx.Request) -> httpx.Response:
        resposta = await self._interno.handle_async_request(request)
        await resposta.aread()  # lê o corpo dentro do timeout
        return resposta

    async def aclose(self) -> None:
        await self._interno.aclose()
