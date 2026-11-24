"""POST /sinistros"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import Request as HttpRequest

from seguros.common.erros.erro_para_http import MEDIA_TYPE_PROBLEMA, para_problema
from seguros.domain.sinistros.aggregates.sinistros.apolices_api_client import ApolicesApiClient
from seguros.domain.sinistros.aggregates.sinistros.sinistro_repository import SinistroRepository
from seguros.domain.sinistros.contracts.sinistro_response import SinistroResponse
from seguros.domain.sinistros.features.registrar_sinistro.handler import Handler
from seguros.domain.sinistros.features.registrar_sinistro.request import Request
from seguros.domain.sinistros.infrastructure.dependencias import (
    obter_apolices_api_client,
    obter_sinistro_repository,
)

router = APIRouter(tags=["Sinistros"])

_PROBLEMA = {MEDIA_TYPE_PROBLEMA: {}}


def obter_handler(
    apolices: Annotated[ApolicesApiClient, Depends(obter_apolices_api_client)],
    repository: Annotated[SinistroRepository, Depends(obter_sinistro_repository)],
) -> Handler:
    return Handler(apolices, repository)


@router.post(
    "/sinistros",
    status_code=201,
    response_model=SinistroResponse,
    summary="Registra um novo sinistro",
    description="Cria um sinistro vinculado a uma apólice, validando em tempo real junto à API "
    "de Apólices que ela estava vigente na data da ocorrência e que possui a cobertura informada.",
    responses={
        400: {"description": "Um ou mais campos são inválidos (code: validacao)", "content": _PROBLEMA},
        404: {"description": "A apólice informada não foi encontrada na API de Apólices (code: apolice-nao-encontrada)", "content": _PROBLEMA},
        422: {"description": "A apólice não estava vigente na data (code: apolice-fora-de-vigencia) ou não possui a cobertura solicitada (code: cobertura-nao-contratada)", "content": _PROBLEMA},
        503: {"description": "A API de Apólices está indisponível no momento (code: apolices-api-indisponivel)", "content": _PROBLEMA},
    },
)
async def registrar_sinistro(
    http: HttpRequest,
    request: Request,  # o FastAPI lê e valida o corpo JSON porque o tipo é um modelo Pydantic
    handler: Annotated[Handler, Depends(obter_handler)],
):
    resultado = await handler.handle(request)
    if resultado.is_failure:
        return para_problema(resultado.error, http)
    return resultado.value
