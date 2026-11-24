"""GET /apolices"""

from typing import Annotated

from fastapi import APIRouter, Depends

from seguros.domain.apolices.aggregates.apolices.apolice_repository import ApoliceRepository
from seguros.domain.apolices.contracts.apolice_response import ApoliceResponse
from seguros.domain.apolices.features.listar_apolices.handler import Handler
from seguros.domain.apolices.infrastructure.dependencias import obter_apolice_repository

router = APIRouter(tags=["Apolices"])


def obter_handler(
    repository: Annotated[ApoliceRepository, Depends(obter_apolice_repository)],
) -> Handler:
    return Handler(repository)


@router.get(
    "/apolices",
    response_model=list[ApoliceResponse],
    summary="Lista todas as apólices cadastradas",
    description="Retorna a coleção completa de apólices de seguro cadastradas, sem paginação.",
)
async def listar_apolices(handler: Annotated[Handler, Depends(obter_handler)]):
    return await handler.handle()
