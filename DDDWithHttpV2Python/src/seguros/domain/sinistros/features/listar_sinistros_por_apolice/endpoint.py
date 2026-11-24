"""GET /apolices/{apolice_id}/sinistros

A rota começa com /apolices, mas pertence ao contexto de Sinistros: quem sabe quais sinistros uma
apólice tem é Sinistros (Apólices nem sabe que sinistros existem).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path

from seguros.domain.sinistros.aggregates.sinistros.sinistro_repository import SinistroRepository
from seguros.domain.sinistros.contracts.sinistro_response import SinistroResponse
from seguros.domain.sinistros.features.listar_sinistros_por_apolice.handler import Handler
from seguros.domain.sinistros.infrastructure.dependencias import obter_sinistro_repository

router = APIRouter(tags=["Sinistros"])


def obter_handler(
    repository: Annotated[SinistroRepository, Depends(obter_sinistro_repository)],
) -> Handler:
    return Handler(repository)


@router.get(
    "/apolices/{apolice_id}/sinistros",
    response_model=list[SinistroResponse],
    summary="Lista os sinistros de uma apólice",
    description="Retorna todos os sinistros registrados para a apólice informada.",
)
async def listar_sinistros_por_apolice(
    apolice_id: Annotated[UUID, Path(description="Identificador da apólice")],
    handler: Annotated[Handler, Depends(obter_handler)],
):
    return await handler.handle(apolice_id)
