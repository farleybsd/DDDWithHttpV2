"""GET /sinistros/{id}/apolice"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request

from seguros.common.erros.erro_para_http import MEDIA_TYPE_PROBLEMA, para_problema
from seguros.domain.sinistros.aggregates.sinistros.apolices_api_client import ApolicesApiClient
from seguros.domain.sinistros.aggregates.sinistros.sinistro_repository import SinistroRepository
from seguros.domain.sinistros.contracts.apolice_do_sinistro_response import ApoliceDoSinistroResponse
from seguros.domain.sinistros.features.consultar_apolice_do_sinistro.handler import Handler
from seguros.domain.sinistros.infrastructure.dependencias import (
    obter_apolices_api_client,
    obter_sinistro_repository,
)

router = APIRouter(tags=["Sinistros"])

_PROBLEMA = {MEDIA_TYPE_PROBLEMA: {}}


def obter_handler(
    repository: Annotated[SinistroRepository, Depends(obter_sinistro_repository)],
    apolices: Annotated[ApolicesApiClient, Depends(obter_apolices_api_client)],
) -> Handler:
    return Handler(repository, apolices)


@router.get(
    "/sinistros/{id}/apolice",
    response_model=ApoliceDoSinistroResponse,
    summary="Consulta a apólice vinculada a um sinistro",
    description="Busca em tempo real, na API de Apólices, os dados da apólice associada ao sinistro "
    "e indica se ela estava vigente e possuía a cobertura na data da ocorrência.",
    responses={
        404: {"description": "Sinistro não encontrado (code: sinistro-nao-encontrado), ou a apólice vinculada não foi encontrada (code: apolice-nao-encontrada)", "content": _PROBLEMA},
        503: {"description": "A API de Apólices está indisponível no momento (code: apolices-api-indisponivel)", "content": _PROBLEMA},
    },
)
async def consultar_apolice_do_sinistro(
    request: Request,
    id: Annotated[UUID, Path(description="Identificador do sinistro")],
    handler: Annotated[Handler, Depends(obter_handler)],
):
    resultado = await handler.handle(id)
    if resultado.is_failure:
        return para_problema(resultado.error, request)
    return resultado.value
