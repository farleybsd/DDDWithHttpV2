"""Registro das dependências e rotas do contexto de Sinistros (o ``AddSinistrosModule()``),
incluindo o cliente HTTP que ele usa para falar com o contexto de Apólices."""

import httpx
from fastapi import FastAPI

from seguros.common.http.context_http_client import criar_cliente_http_de_contexto
from seguros.common.settings import Settings
from seguros.domain.sinistros.features.consultar_apolice_do_sinistro import (
    endpoint as consultar_apolice_do_sinistro,
)
from seguros.domain.sinistros.features.consultar_sinistro import endpoint as consultar_sinistro
from seguros.domain.sinistros.features.listar_sinistros_por_apolice import (
    endpoint as listar_sinistros_por_apolice,
)
from seguros.domain.sinistros.features.registrar_sinistro import endpoint as registrar_sinistro
from seguros.domain.sinistros.infrastructure.apolices_api.apolices_api_http_client import (
    ApolicesApiHttpClient,
)
from seguros.domain.sinistros.infrastructure.in_memory_sinistro_repository import (
    InMemorySinistroRepository,
)


def adicionar_modulo_sinistros(
    app: FastAPI,
    settings: Settings,
    transporte_apolices: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    app.state.sinistro_repository = InMemorySinistroRepository()

    # Sinistros -> Apólices: comunicação por HTTP, mesmo estando no mesmo processo.
    cliente_http = criar_cliente_http_de_contexto(
        nome_do_pipeline="sinistros-para-apolices",
        endereco_do_contexto=settings.services_settings.apolices_uri,
        resiliencia=settings.http_resilience,
        transporte=transporte_apolices,
    )
    app.state.clientes_http.append(cliente_http)  # fechado no desligamento (main.py)
    app.state.apolices_api_client = ApolicesApiHttpClient(cliente_http)

    app.include_router(registrar_sinistro.router)
    app.include_router(consultar_sinistro.router)
    app.include_router(listar_sinistros_por_apolice.router)
    app.include_router(consultar_apolice_do_sinistro.router)
    return app
