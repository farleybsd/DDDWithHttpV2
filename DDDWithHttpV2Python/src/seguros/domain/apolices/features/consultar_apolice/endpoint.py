"""GET /apolices/{id} — o Endpoint.cs + Summary.cs do C# juntos.

No FastAPI a documentação do Swagger (summary, description, responses) vai no próprio decorator.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request

from seguros.common.erros.erro_para_http import MEDIA_TYPE_PROBLEMA, para_problema
from seguros.domain.apolices.aggregates.apolices.apolice_repository import ApoliceRepository
from seguros.domain.apolices.contracts.apolice_response import ApoliceResponse
from seguros.domain.apolices.features.consultar_apolice.handler import Handler
from seguros.domain.apolices.infrastructure.dependencias import obter_apolice_repository

router = APIRouter(tags=["Apolices"])


# Depends(...) é a injeção de dependência do FastAPI: a cada requisição ele chama esta função,
# que por sua vez recebe o repositório de outra dependência.
def obter_handler(
    repository: Annotated[ApoliceRepository, Depends(obter_apolice_repository)],
) -> Handler:
    return Handler(repository)


@router.get(
    "/apolices/{id}",
    response_model=ApoliceResponse,
    summary="Consulta uma apólice pelo identificador",
    description="Retorna os dados completos de uma apólice de seguro "
    "(segurado, vigência e coberturas) a partir do seu Id.",
    responses={
        404: {
            "description": "Nenhuma apólice foi encontrada com o Id informado (code: apolice-nao-encontrada)",
            "content": {MEDIA_TYPE_PROBLEMA: {}},
        }
    },
)
async def consultar_apolice(
    request: Request,
    id: Annotated[UUID, Path(description="Identificador da apólice")],
    handler: Annotated[Handler, Depends(obter_handler)],
):
    resultado = await handler.handle(id)
    if resultado.is_failure:
        return para_problema(resultado.error, request)
    return resultado.value
