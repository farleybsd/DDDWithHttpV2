"""POST /sinistros com o contexto de Apólices SIMULADO — cobre 201/404/422 e a resiliência."""

import asyncio
import uuid

import httpx
import pytest

from tests.integration.apoio import assert_problema, json_ok, subir_api

APOLICE_ID = str(uuid.uuid4())

APOLICE_VIGENTE_COM_COLISAO = {
    "id": APOLICE_ID,
    "numero": "AP-0001",
    "segurado": {"nome": "Ana Souza", "documento": "111.111.111-11"},
    "vigencia": {"inicio": "2026-01-01", "fim": "2026-12-31"},
    "coberturas": [{"tipo": "Colisao", "limiteIndenizacao": 50000}],
}


def request_valido(**alteracoes) -> dict:
    # {**a, **b} junta dois dicionários; os valores de b sobrescrevem os de a.
    return {
        "apoliceId": APOLICE_ID,
        "dataOcorrencia": "2026-06-01",
        "tipoCobertura": "Colisao",
        "descricao": "Colisão na Av. Paulista",
        **alteracoes,
    }


def sem_circuito(s):
    """Não deixa o circuit breaker interferir em testes de retry/timeout."""
    s.http_resilience.retry.base_delay_segundos = 0.01
    s.http_resilience.circuit_breaker.minimum_throughput = 1000


async def test_201_quando_apolice_vigente_e_com_cobertura():
    async with subir_api(lambda _: json_ok(APOLICE_VIGENTE_COM_COLISAO)) as api:
        resposta = await api.cliente.post("/sinistros", json=request_valido())

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["apoliceId"] == APOLICE_ID
    assert corpo["status"] == "Registrado"


async def test_404_quando_apolice_nao_existe():
    async with subir_api(lambda _: httpx.Response(404)) as api:
        resposta = await api.cliente.post("/sinistros", json=request_valido())

    assert resposta.status_code == 404
    assert_problema(resposta, "apolice-nao-encontrada")


async def test_422_quando_apolice_nao_possui_a_cobertura():
    async with subir_api(lambda _: json_ok(APOLICE_VIGENTE_COM_COLISAO)) as api:
        resposta = await api.cliente.post("/sinistros", json=request_valido(tipoCobertura="Roubo"))

    assert resposta.status_code == 422
    problema = assert_problema(resposta, "cobertura-nao-contratada")
    assert problema["tipoCobertura"] == "Roubo"


async def test_recupera_via_retry_apos_duas_falhas_transitorias():
    tentativas = 0

    def responder(_):
        nonlocal tentativas  # "nonlocal" permite alterar a variável da função de fora
        tentativas += 1
        return httpx.Response(503) if tentativas <= 2 else json_ok(APOLICE_VIGENTE_COM_COLISAO)

    def ajustar(s):
        sem_circuito(s)
        s.http_resilience.retry.max_retry_attempts = 3

    async with subir_api(responder, ajustar_settings=ajustar) as api:
        resposta = await api.cliente.post("/sinistros", json=request_valido())

    assert resposta.status_code == 201
    assert api.apolices.numero_de_chamadas == 3


async def test_abre_o_circuito_quando_falhas_persistem():
    def ajustar(s):
        s.http_resilience.retry.max_retry_attempts = 1
        s.http_resilience.retry.base_delay_segundos = 0.01
        s.http_resilience.circuit_breaker.minimum_throughput = 2
        s.http_resilience.circuit_breaker.failure_ratio = 0.5
        s.http_resilience.circuit_breaker.break_duration_segundos = 5

    async with subir_api(lambda _: httpx.Response(503), ajustar_settings=ajustar) as api:
        primeira = await api.cliente.post("/sinistros", json=request_valido())
        assert primeira.status_code == 503
        assert api.apolices.numero_de_chamadas == 2  # 1 tentativa + 1 retry

        segunda = await api.cliente.post("/sinistros", json=request_valido())
        assert segunda.status_code == 503
        assert api.apolices.numero_de_chamadas == 2  # circuito aberto: nem chamou de novo
        assert_problema(segunda, "apolices-api-indisponivel")


async def test_503_quando_consulta_excede_o_timeout():
    async def lento(_):
        await asyncio.sleep(2)
        return json_ok(APOLICE_VIGENTE_COM_COLISAO)

    def ajustar(s):
        sem_circuito(s)
        s.http_resilience.timeout_segundos = 0.2
        s.http_resilience.retry.max_retry_attempts = 1

    async with subir_api(lento, ajustar_settings=ajustar) as api:
        resposta = await api.cliente.post("/sinistros", json=request_valido())

    assert resposta.status_code == 503
    assert api.apolices.numero_de_chamadas == 2


async def test_503_quando_falha_de_rede():
    def sem_rede(request):
        raise httpx.ConnectError("conexão recusada", request=request)

    async with subir_api(sem_rede, ajustar_settings=sem_circuito) as api:
        resposta = await api.cliente.post("/sinistros", json=request_valido())

    assert resposta.status_code == 503
    assert_problema(resposta, "apolices-api-indisponivel")


@pytest.mark.parametrize(
    ("base_url", "prefixo_esperado"),
    [
        ("http://localhost:5200", "http://localhost:5200/apolices/"),
        ("https://apolices.qas.seguros.example/", "https://apolices.qas.seguros.example/apolices/"),
        ("https://gateway.qas.seguros.example/apolices-api", "https://gateway.qas.seguros.example/apolices-api/apolices/"),
    ],
)
async def test_monta_a_url_a_partir_do_endereco_do_ambiente(base_url, prefixo_esperado):
    def ajustar(s):
        s.services_settings.apolices_uri = base_url

    async with subir_api(lambda _: httpx.Response(404), ajustar_settings=ajustar) as api:
        await api.cliente.post("/sinistros", json=request_valido())

    assert api.apolices.urls == [f"{prefixo_esperado}{APOLICE_ID}"]
