"""Funções usadas pelo ``Depends(...)`` dos endpoints de Sinistros (ver ``sinistros_module.py``)."""

from fastapi import Request

from seguros.domain.sinistros.aggregates.sinistros.apolices_api_client import ApolicesApiClient
from seguros.domain.sinistros.aggregates.sinistros.sinistro_repository import SinistroRepository


def obter_sinistro_repository(request: Request) -> SinistroRepository:
    return request.app.state.sinistro_repository


def obter_apolices_api_client(request: Request) -> ApolicesApiClient:
    return request.app.state.apolices_api_client
