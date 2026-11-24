"""Ponto de entrada da aplicação (o Program.cs).

``criar_app()`` é uma *fábrica*: monta uma aplicação nova a cada chamada. O uvicorn a chama na
subida (``--factory``) e os testes a chamam com configurações e transportes próprios (o papel do
WebApplicationFactory do C#).

Para rodar:
    uvicorn seguros.main:criar_app --factory --app-dir src --port 5200
"""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from seguros.common.erros.problem_details import adicionar_problem_details
from seguros.common.settings import Settings, carregar_settings
from seguros.domain.apolices.infrastructure.apolices_module import adicionar_modulo_apolices
from seguros.domain.sinistros.infrastructure.sinistros_module import adicionar_modulo_sinistros


@asynccontextmanager
async def _ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """O que vem antes do ``yield`` roda na subida; o que vem depois, no desligamento."""
    yield
    for cliente in app.state.clientes_http:
        await cliente.aclose()


def criar_app(
    settings: Settings | None = None,
    transporte_apolices: Callable[[FastAPI], httpx.AsyncBaseTransport] | None = None,
) -> FastAPI:
    # Lê config/*.env + variáveis de ambiente e valida. URL inválida -> erro aqui, a app nem sobe.
    settings = settings or carregar_settings()
    logging.basicConfig(level=settings.nivel_log.upper(), format="%(levelname)s: %(name)s - %(message)s")

    app = FastAPI(
        title="Seguros API",
        version="v1",
        description="DDD em uma única API, com os contextos de Apólices e Sinistros conversando por HTTP.",
        docs_url="/swagger",
        openapi_url="/openapi/v1.json",
        lifespan=_ciclo_de_vida,
    )
    app.state.settings = settings
    app.state.clientes_http = []

    adicionar_problem_details(app)

    # Cada bounded context registra as próprias dependências e rotas no seu módulo.
    adicionar_modulo_apolices(app)
    adicionar_modulo_sinistros(
        app,
        settings,
        transporte_apolices(app) if transporte_apolices else None,
    )
    return app
