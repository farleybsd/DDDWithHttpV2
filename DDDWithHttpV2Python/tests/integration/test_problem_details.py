"""Contrato de erros RFC 9457 para o que não vem de um caso de uso: exceções, validação e rotas
inexistentes. Rodam em "production", onde vazar detalhes internos realmente importa."""

import uuid

import httpx
import pytest
from pydantic import ValidationError

from seguros.common.settings import Settings
from tests.integration.apoio import assert_problema, subir_api


class RepositorioQueFalha:
    async def _falhar(self, *_):
        raise RuntimeError("Host=db-prod;Password=segredo123")

    adicionar = obter_por_id = listar_por_apolice = _falhar


async def test_erro_inesperado_nao_vaza_detalhes_internos():
    def trocar_repositorio(app):
        app.state.sinistro_repository = RepositorioQueFalha()

    async with subir_api(lambda _: httpx.Response(404), ajustar_app=trocar_repositorio, ambiente="production") as api:
        resposta = await api.cliente.get(f"/sinistros/{uuid.uuid4()}")

    assert resposta.status_code == 500
    assert_problema(resposta, "erro-interno")
    assert "segredo" not in resposta.text
    assert "RuntimeError" not in resposta.text
    assert "RepositorioQueFalha" not in resposta.text


async def test_erro_de_validacao_retorna_problema_com_os_campos():
    async with subir_api(lambda _: httpx.Response(404), ambiente="production") as api:
        resposta = await api.cliente.post(
            "/sinistros",
            json={
                "apoliceId": "00000000-0000-0000-0000-000000000000",
                "dataOcorrencia": "2026-06-01",
                "tipoCobertura": "Inexistente",
                "descricao": "",
            },
        )

    assert resposta.status_code == 400
    erros = assert_problema(resposta, "validacao")["errors"]
    assert erros["apoliceId"] == ["O identificador da apólice é obrigatório."]
    assert "tipoCobertura" in erros
    assert "descricao" in erros
    assert api.apolices.numero_de_chamadas == 0  # nem chegou a chamar Apólices


async def test_campos_ausentes_aparecem_em_camel_case():
    async with subir_api(lambda _: httpx.Response(404)) as api:
        resposta = await api.cliente.post("/sinistros", json={"tipoCobertura": "Colisao"})

    erros = assert_problema(resposta, "validacao")["errors"]
    assert sorted(erros) == ["apoliceId", "dataOcorrencia", "descricao"]


async def test_data_no_futuro_e_invalida():
    async with subir_api(lambda _: httpx.Response(404)) as api:
        resposta = await api.cliente.post(
            "/sinistros",
            json={"apoliceId": str(uuid.uuid4()), "dataOcorrencia": "2999-01-01", "tipoCobertura": "Colisao", "descricao": "x"},
        )

    assert resposta.status_code == 400
    assert assert_problema(resposta, "validacao")["errors"]["dataOcorrencia"] == [
        "A data de ocorrência não pode estar no futuro."
    ]


async def test_rota_inexistente_retorna_problem_details():
    async with subir_api(lambda _: httpx.Response(404), ambiente="production") as api:
        resposta = await api.cliente.get("/rota-que-nao-existe")

    assert resposta.status_code == 404
    assert resposta.headers["content-type"].startswith("application/problem+json")


def test_aplicacao_nao_sobe_sem_endereco_de_apolices_valido(monkeypatch):
    # monkeypatch altera variáveis de ambiente só durante este teste.
    monkeypatch.setenv("SERVICES_SETTINGS__APOLICES_URI", "nao-e-uma-url")
    with pytest.raises(ValidationError):
        Settings()
