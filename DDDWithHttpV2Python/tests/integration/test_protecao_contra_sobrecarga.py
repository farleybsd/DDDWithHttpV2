"""Proteções das chamadas internas contra a aplicação sobrecarregar a si mesma: retry reduzido ou
desligado e limite de chamadas simultâneas."""

import asyncio
import uuid

import httpx

from tests.integration.apoio import assert_problema, json_ok, subir_api
from tests.integration.test_registrar_sinistro import APOLICE_VIGENTE_COM_COLISAO, request_valido


async def test_com_retry_padrao_faz_no_maximo_uma_retentativa():
    def ajustar(s):  # sem mexer no max_retry_attempts: vale o config/base.env (1)
        s.http_resilience.retry.base_delay_segundos = 0.01
        s.http_resilience.circuit_breaker.minimum_throughput = 1000

    async with subir_api(lambda _: httpx.Response(503), ajustar_settings=ajustar) as api:
        resposta = await api.cliente.post("/sinistros", json=request_valido())

    assert resposta.status_code == 503
    assert api.apolices.numero_de_chamadas == 2


async def test_com_retry_zero_nao_retenta():
    def ajustar(s):
        s.http_resilience.retry.max_retry_attempts = 0
        s.http_resilience.circuit_breaker.minimum_throughput = 1000

    async with subir_api(lambda _: httpx.Response(503), ajustar_settings=ajustar) as api:
        resposta = await api.cliente.post("/sinistros", json=request_valido())

    assert resposta.status_code == 503
    assert api.apolices.numero_de_chamadas == 1


async def test_acima_do_limite_de_concorrencia_recusa_na_hora_com_503():
    liberar = asyncio.Event()  # o TaskCompletionSource do C#
    primeira_chegou = asyncio.Event()

    async def segura_a_primeira(_):
        primeira_chegou.set()
        await liberar.wait()  # ocupa o único "lugar" até o teste liberar
        return json_ok(APOLICE_VIGENTE_COM_COLISAO)

    def ajustar(s):
        s.http_resilience.concurrency_limiter.permit_limit = 1
        s.http_resilience.concurrency_limiter.queue_limit = 0
        s.http_resilience.timeout_segundos = 10
        s.http_resilience.circuit_breaker.minimum_throughput = 1000

    async with subir_api(segura_a_primeira, ajustar_settings=ajustar) as api:
        # create_task dispara a 1ª requisição em paralelo, sem esperar terminar.
        primeira = asyncio.create_task(api.cliente.post("/sinistros", json=request_valido()))
        await asyncio.wait_for(primeira_chegou.wait(), timeout=5)

        segunda = await api.cliente.post("/sinistros", json=request_valido())

        assert segunda.status_code == 503
        assert_problema(segunda, "apolices-api-indisponivel")
        assert api.apolices.numero_de_chamadas == 1  # a 2ª nem saiu (nem retentou)

        liberar.set()
        assert (await primeira).status_code == 201


async def test_consultar_apolice_do_sinistro_503_quando_apolices_cai_depois():
    """Registra com Apólices no ar e consulta com ele fora: 503 sem perder o sinistro."""
    no_ar = True

    def responder(_):
        return json_ok(APOLICE_VIGENTE_COM_COLISAO) if no_ar else httpx.Response(500)

    def ajustar(s):
        s.http_resilience.retry.max_retry_attempts = 0
        s.http_resilience.circuit_breaker.minimum_throughput = 1000

    async with subir_api(responder, ajustar_settings=ajustar) as api:
        sinistro = (await api.cliente.post("/sinistros", json=request_valido())).json()
        no_ar = False

        resposta = await api.cliente.get(f"/sinistros/{sinistro['id']}/apolice")
        ainda_existe = await api.cliente.get(f"/sinistros/{sinistro['id']}")
        inexistente = await api.cliente.get(f"/sinistros/{uuid.uuid4()}/apolice")

    assert_problema(resposta, "apolices-api-indisponivel")
    assert ainda_existe.status_code == 200
    assert_problema(inexistente, "sinistro-nao-encontrado")
