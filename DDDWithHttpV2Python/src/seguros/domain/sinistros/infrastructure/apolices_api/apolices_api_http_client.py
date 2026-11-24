"""ADAPTADOR HTTP da porta ``ApolicesApiClient`` — a camada anticorrupção.

Chama os endpoints públicos do contexto de Apólices por HTTP, mesmo os dois rodando no mesmo
processo. É o ÚNICO ponto que conhece o formato do JSON de Apólices (``ApoliceApiDto``).
"""

import logging
from uuid import UUID

import httpx
from pydantic import ValidationError

from seguros.common.http.resiliencia import (
    CircuitoAberto,
    LimiteDeConcorrenciaExcedido,
    TempoLimiteExcedido,
)
from seguros.domain.sinistros.aggregates.sinistros.apolice_consulta_resultado import (
    ApoliceConsultaResultado,
    Encontrada,
    Indisponivel,
    NaoEncontrada,
)
from seguros.domain.sinistros.aggregates.sinistros.apolice_referenciada import ApoliceReferenciada
from seguros.domain.sinistros.aggregates.sinistros.tipo_cobertura import TipoCobertura
from seguros.domain.sinistros.infrastructure.apolices_api.apolice_api_dto import ApoliceApiDto

logger = logging.getLogger(__name__)


class ApolicesApiHttpClient:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client

    async def consultar_apolice(self, apolice_id: UUID) -> ApoliceConsultaResultado:
        try:
            # Rota relativa (sem barra inicial): o endereço base vem do ambiente
            # (SERVICES_SETTINGS__APOLICES_URI) e pode conter um caminho.
            resposta = await self._http.get(f"apolices/{apolice_id}")
        except TempoLimiteExcedido:
            logger.warning("Tempo limite excedido ao consultar a apólice %s.", apolice_id)
            return Indisponivel("Tempo limite excedido ao consultar a API de Apólices.")
        except LimiteDeConcorrenciaExcedido:
            logger.warning(
                "Limite de chamadas simultâneas a Apólices atingido — apólice %s recusada.", apolice_id
            )
            return Indisponivel("Limite de chamadas simultâneas à API de Apólices atingido.")
        except CircuitoAberto:
            logger.warning(
                "Circuito aberto para a API de Apólices — apólice %s não foi consultada.", apolice_id
            )
            return Indisponivel("API de Apólices temporariamente indisponível (circuito aberto).")
        except httpx.HTTPError:
            logger.warning("Falha de comunicação com a API de Apólices (apólice %s).", apolice_id, exc_info=True)
            return Indisponivel("Falha de comunicação com a API de Apólices.")

        if resposta.status_code == 404:
            return NaoEncontrada()  # resposta de negócio

        if not resposta.is_success:
            logger.warning(
                "Consulta à API de Apólices retornou %s para a apólice %s.", resposta.status_code, apolice_id
            )
            return Indisponivel(f"Resposta inesperada da API de Apólices: {resposta.status_code}.")

        try:
            dto = ApoliceApiDto.model_validate_json(resposta.content)
        except ValidationError:
            logger.warning("Resposta inválida da API de Apólices (apólice %s).", apolice_id, exc_info=True)
            return Indisponivel("Resposta inválida da API de Apólices.")

        return Encontrada(self._traduzir(dto))

    @staticmethod
    def _traduzir(dto: ApoliceApiDto) -> ApoliceReferenciada:
        """DTO (vocabulário de Apólices) -> ApoliceReferenciada (vocabulário de Sinistros).
        Se Apólices mudar sua representação, só este método muda. Tipos de cobertura que
        Sinistros não conhece são ignorados: não há como abrir sinistro para eles mesmo."""
        coberturas = (TipoCobertura.de_texto(c.tipo) for c in dto.coberturas)
        return ApoliceReferenciada(
            apolice_id=dto.id,
            vigencia_inicio=dto.vigencia.inicio,
            vigencia_fim=dto.vigencia.fim,
            coberturas=tuple(c for c in coberturas if c is not None),
        )
