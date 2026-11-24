"""Dado um sinistro registrado, consulta AO VIVO a API de Apólices para devolver a apólice dele.

Este contexto guarda só o identificador da apólice, nunca uma cópia dos dados de Apólices.
"""

import logging
from typing import assert_never
from uuid import UUID

from seguros.common.result import Result
from seguros.domain.sinistros.aggregates.sinistros.apolice_consulta_resultado import (
    Encontrada,
    Indisponivel,
    NaoEncontrada,
)
from seguros.domain.sinistros.aggregates.sinistros.apolice_referenciada import ApoliceReferenciada
from seguros.domain.sinistros.aggregates.sinistros.apolices_api_client import ApolicesApiClient
from seguros.domain.sinistros.aggregates.sinistros.erros_de_sinistro import ErrosDeSinistro
from seguros.domain.sinistros.aggregates.sinistros.sinistro import Sinistro
from seguros.domain.sinistros.aggregates.sinistros.sinistro_repository import SinistroRepository
from seguros.domain.sinistros.contracts.apolice_do_sinistro_response import ApoliceDoSinistroResponse

logger = logging.getLogger(__name__)


class Handler:
    def __init__(self, repository: SinistroRepository, apolices_api_client: ApolicesApiClient) -> None:
        self._repository = repository
        self._apolices = apolices_api_client

    async def handle(self, sinistro_id: UUID) -> Result[ApoliceDoSinistroResponse]:
        sinistro = await self._repository.obter_por_id(sinistro_id)
        if sinistro is None:
            return Result.failure(ErrosDeSinistro.sinistro_nao_encontrado(sinistro_id))

        consulta = await self._apolices.consultar_apolice(sinistro.apolice_id)

        match consulta:
            case Encontrada(apolice):
                return Result.success(_mapear(sinistro, apolice))

            case NaoEncontrada():
                logger.warning(
                    "O sinistro %s referencia a apólice %s, que não existe mais na API de Apólices.",
                    sinistro.id, sinistro.apolice_id,
                )
                return Result.failure(ErrosDeSinistro.apolice_nao_encontrada(sinistro.apolice_id))

            case Indisponivel(motivo):
                logger.warning(
                    "Apólice do sinistro %s não consultada: API de Apólices indisponível. Motivo: %s",
                    sinistro.id, motivo,
                )
                return Result.failure(ErrosDeSinistro.APOLICES_API_INDISPONIVEL)

            case _:
                assert_never(consulta)


def _mapear(sinistro: Sinistro, apolice: ApoliceReferenciada) -> ApoliceDoSinistroResponse:
    return ApoliceDoSinistroResponse(
        sinistro_id=sinistro.id,
        apolice_id=apolice.apolice_id,
        data_ocorrencia=sinistro.data_ocorrencia,
        tipo_cobertura=str(sinistro.tipo_cobertura),
        vigencia_inicio=apolice.vigencia_inicio,
        vigencia_fim=apolice.vigencia_fim,
        coberturas=[str(c) for c in apolice.coberturas],
        vigente_na_data_ocorrencia=apolice.esta_vigente_em(sinistro.data_ocorrencia),
        possui_cobertura_do_sinistro=apolice.possui_cobertura(sinistro.tipo_cobertura),
    )
