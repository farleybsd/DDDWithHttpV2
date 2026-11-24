"""Registro das dependências e rotas do contexto de Apólices (o ``AddApolicesModule()``).

Este contexto não conhece nenhum outro.
"""

from fastapi import FastAPI

from seguros.domain.apolices.features.consultar_apolice import endpoint as consultar_apolice
from seguros.domain.apolices.features.listar_apolices import endpoint as listar_apolices
from seguros.domain.apolices.infrastructure.in_memory_apolice_repository import (
    InMemoryApoliceRepository,
)


def adicionar_modulo_apolices(app: FastAPI) -> FastAPI:
    # Repositório em memória: precisa viver enquanto a aplicação viver (o AddSingleton).
    app.state.apolice_repository = InMemoryApoliceRepository()

    app.include_router(listar_apolices.router)
    app.include_router(consultar_apolice.router)
    return app
