"""Apoio para os testes de integração (o SegurosApiFactory + ScriptedHttpMessageHandler +
ProblemaAssert do C#).

Sobe a aplicação inteira (os dois contextos) em memória, sem abrir porta nenhuma. Dois modos para
a chamada HTTP Sinistros -> Apólices:

* ``responder`` informado: Apólices é SIMULADO por um ``httpx.MockTransport`` (sucesso, 404,
  falhas, lentidão). O pipeline de resiliência real continua ativo por cima dele.
* ``responder`` omitido: a requisição é entregue à própria aplicação (``httpx.ASGITransport``),
  ou seja, chega de verdade aos endpoints do contexto de Apólices — só que sem socket.

Uma aplicação nova é criada por teste para que o estado do circuit breaker nunca vaze.
"""

import inspect
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import httpx
from fastapi import FastAPI

from seguros.common.settings import Settings, carregar_settings
from seguros.main import criar_app

type Responder = Callable[[httpx.Request], httpx.Response | Awaitable[httpx.Response]]


@dataclass
class ApolicesSimulado:
    """Conta as chamadas e guarda as URLs — para os testes verificarem retry, circuito etc."""

    responder: Responder
    numero_de_chamadas: int = 0
    urls: list[str] = field(default_factory=list)

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        self.numero_de_chamadas += 1
        self.urls.append(str(request.url))
        resposta = self.responder(request)
        if inspect.isawaitable(resposta):  # aceita responder normal ou "async def"
            resposta = await resposta
        return resposta


@dataclass
class ApiEmTeste:
    cliente: httpx.AsyncClient
    app: FastAPI
    apolices: ApolicesSimulado | None


@asynccontextmanager
async def subir_api(
    responder: Responder | None = None,
    *,
    ajustar_settings: Callable[[Settings], None] | None = None,
    ajustar_app: Callable[[FastAPI], None] | None = None,
    ambiente: str = "development",
) -> AsyncIterator[ApiEmTeste]:
    settings = carregar_settings(ambiente)
    if ajustar_settings:
        ajustar_settings(settings)

    simulado = ApolicesSimulado(responder) if responder else None

    def transporte(app: FastAPI) -> httpx.AsyncBaseTransport:
        return httpx.MockTransport(simulado) if simulado else httpx.ASGITransport(app=app)

    app = criar_app(settings, transporte)
    if ajustar_app:
        ajustar_app(app)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as cliente:
        yield ApiEmTeste(cliente, app, simulado)

    for cliente_interno in app.state.clientes_http:
        await cliente_interno.aclose()


def json_ok(corpo: dict) -> httpx.Response:
    return httpx.Response(200, json=corpo)


def assert_problema(resposta: httpx.Response, codigo_esperado: str) -> dict:
    """Verifica o contrato RFC 9457 e devolve o corpo para asserções adicionais."""
    assert resposta.headers["content-type"].startswith("application/problem+json")
    problema = resposta.json()
    assert problema["status"] == resposta.status_code
    assert problema["type"] == f"https://seguros.example/problemas/{codigo_esperado}"
    assert problema["code"] == codigo_esperado
    assert problema["title"].strip()
    assert problema["instance"].strip()
    assert problema["traceId"].strip()
    return problema
