"""Cria o cliente HTTP que um contexto usa para falar com outro (equivale ao
``AddContextHttpClient<,>`` do ContextHttpClientExtensions.cs).

O endereço vem de ``ServicesSettings`` e o pipeline de resiliência de ``HttpResilienceSettings``.
"""

import httpx

from seguros.common.http.resiliencia import TransporteResiliente
from seguros.common.settings import HttpResilienceSettings, com_barra_final


def criar_cliente_http_de_contexto(
    *,
    nome_do_pipeline: str,
    endereco_do_contexto: str,
    resiliencia: HttpResilienceSettings,
    transporte: httpx.AsyncBaseTransport | None = None,
) -> httpx.AsyncClient:
    """``transporte`` é o "handler primário" (a rede de verdade, por padrão). Os testes trocam
    só ele, mantendo o pipeline de resiliência por cima — como o
    ``ConfigurePrimaryHttpMessageHandler`` do C#."""
    return httpx.AsyncClient(
        base_url=com_barra_final(endereco_do_contexto),
        transport=TransporteResiliente(
            nome_do_pipeline,
            transporte or httpx.AsyncHTTPTransport(),
            resiliencia,
        ),
        # O timeout de cada tentativa é controlado pelo pipeline; este é só uma rede de segurança.
        timeout=httpx.Timeout(30.0),
    )
