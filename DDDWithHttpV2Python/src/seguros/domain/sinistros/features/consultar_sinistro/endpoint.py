"""GET /sinistros/{id}"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request

from seguros.common.erros.erro_para_http import MEDIA_TYPE_PROBLEMA, para_problema
from seguros.domain.sinistros.aggregates.sinistros.sinistro_repository import SinistroRepository
from seguros.domain.sinistros.contracts.sinistro_response import SinistroResponse
from seguros.domain.sinistros.features.consultar_sinistro.handler import Handler
from seguros.domain.sinistros.infrastructure.dependencias import obter_sinistro_repository

router = APIRouter(tags=["Sinistros"])


def obter_handler(
    repository: Annotated[SinistroRepository, Depends(obter_sinistro_repository)],
) -> Handler:
    return Handler(repository)


@router.get(
    "/sinistros/{id}",
    response_model=SinistroResponse,
    summary="Consulta um sinistro pelo identificador",
    description="Retorna os dados de um sinistro previamente registrado.",
    responses={
        404: {
            "description": "Nenhum sinistro foi encontrado com o Id informado (code: sinistro-nao-encontrado)",
            "content": {MEDIA_TYPE_PROBLEMA: {}},
        }
    },
)
async def consultar_sinistro(
    request: Request,
    id: Annotated[UUID, Path(description="Identificador do sinistro")],
    handler: Annotated[Handler, Depends(obter_handler)],
):
    resultado = await handler.handle(id)
    if resultado.is_failure:
        return para_problema(resultado.error, request)
    return resultado.value
