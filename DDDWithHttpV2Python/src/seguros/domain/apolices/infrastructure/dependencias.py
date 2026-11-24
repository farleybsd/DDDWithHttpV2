"""Funções que o ``Depends(...)`` dos endpoints usa para obter as dependências do contexto.

Os objetos "singleton" (que vivem enquanto a aplicação viver) ficam em ``app.state``, guardados
pelo módulo do contexto (``apolices_module.py``). Ficam num arquivo separado do módulo para
evitar import circular (módulo importa endpoints, endpoints importam isto).
"""

from fastapi import Request

from seguros.domain.apolices.aggregates.apolices.apolice_repository import ApoliceRepository


def obter_apolice_repository(request: Request) -> ApoliceRepository:
    return request.app.state.apolice_repository
