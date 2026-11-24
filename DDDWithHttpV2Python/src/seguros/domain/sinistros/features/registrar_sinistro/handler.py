import logging
from typing import assert_never

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
from seguros.domain.sinistros.aggregates.sinistros.tipo_cobertura import TipoCobertura
from seguros.domain.sinistros.contracts.sinistro_response import SinistroResponse
from seguros.domain.sinistros.features.registrar_sinistro.request import Request

logger = logging.getLogger(__name__)


class Handler:
    def __init__(self, apolices_api_client: ApolicesApiClient, repository: SinistroRepository) -> None:
        self._apolices = apolices_api_client
        self._repository = repository

    async def handle(self, request: Request) -> Result[SinistroResponse]:
        consulta = await self._apolices.consultar_apolice(request.apolice_id)

        # "match" é o pattern matching do Python (o "switch" com tipos do C#).
        match consulta:
            case NaoEncontrada():
                return Result.failure(ErrosDeSinistro.apolice_nao_encontrada(request.apolice_id))  # 404

            case Indisponivel(motivo):
                logger.warning(
                    "Sinistro não registrado: API de Apólices indisponível para a apólice %s. Motivo: %s",
                    request.apolice_id, motivo,
                )
                return Result.failure(ErrosDeSinistro.APOLICES_API_INDISPONIVEL)  # 503

            case Encontrada(apolice):
                return await self._registrar(request, apolice)  # 201 / 422

            case _:
                # Se um dia surgir um 4º resultado e ninguém tratar, o type checker acusa aqui.
                assert_never(consulta)

    async def _registrar(self, request: Request, apolice: ApoliceReferenciada) -> Result[SinistroResponse]:
        tipo_cobertura = TipoCobertura.de_texto(request.tipo_cobertura)  # já validado no Request

        registro = Sinistro.registrar(
            request.apolice_id, request.data_ocorrencia, tipo_cobertura, request.descricao, apolice
        )
        if registro.is_failure:
            return Result.failure(registro.error)

        sinistro = registro.value
        await self._repository.adicionar(sinistro)
        return Result.success(mapear(sinistro))


def mapear(sinistro: Sinistro) -> SinistroResponse:
    return SinistroResponse(
        id=sinistro.id,
        apolice_id=sinistro.apolice_id,
        data_ocorrencia=sinistro.data_ocorrencia,
        tipo_cobertura=str(sinistro.tipo_cobertura),
        descricao=sinistro.descricao,
        status=str(sinistro.status),
        data_registro=sinistro.data_registro,
    )
