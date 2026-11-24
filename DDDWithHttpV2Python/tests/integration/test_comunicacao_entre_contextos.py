"""Sem nenhum stub: Sinistros faz GET /apolices/{id} e quem responde são os endpoints REAIS de
Apólices desta mesma aplicação, com os dados fictícios do repositório em memória."""

import uuid

from tests.integration.apoio import assert_problema, subir_api

APOLICE_VIGENTE = "11111111-1111-1111-1111-111111111111"
APOLICE_EXPIRADA = "22222222-2222-2222-2222-222222222222"
APOLICE_SEM_ROUBO = "33333333-3333-3333-3333-333333333333"


def corpo(apolice_id: str, data: str, cobertura: str) -> dict:
    return {"apoliceId": apolice_id, "dataOcorrencia": data, "tipoCobertura": cobertura, "descricao": "Sinistro de teste"}


async def test_registrar_sinistro_consulta_o_contexto_de_apolices_por_http():
    async with subir_api() as api:
        registro = await api.cliente.post("/sinistros", json=corpo(APOLICE_VIGENTE, "2026-06-01", "Colisao"))
        assert registro.status_code == 201
        sinistro = registro.json()

        resposta = await api.cliente.get(f"/sinistros/{sinistro['id']}/apolice")

        assert resposta.status_code == 200
        apolice = resposta.json()
        assert apolice["apoliceId"] == APOLICE_VIGENTE
        assert apolice["vigenciaInicio"] == "2026-01-01"
        assert apolice["vigenciaFim"] == "2026-12-31"
        assert apolice["coberturas"] == ["Colisao", "Roubo", "Incendio"]
        assert apolice["vigenteNaDataOcorrencia"] is True
        assert apolice["possuiCoberturaDoSinistro"] is True

        listagem = await api.cliente.get(f"/apolices/{APOLICE_VIGENTE}/sinistros")
        assert [s["id"] for s in listagem.json()] == [sinistro["id"]]


async def test_retorna_422_quando_apolice_do_outro_contexto_esta_expirada():
    async with subir_api() as api:
        resposta = await api.cliente.post("/sinistros", json=corpo(APOLICE_EXPIRADA, "2026-06-01", "Colisao"))

    assert resposta.status_code == 422
    assert_problema(resposta, "apolice-fora-de-vigencia")


async def test_retorna_422_quando_apolice_do_outro_contexto_nao_tem_a_cobertura():
    async with subir_api() as api:
        resposta = await api.cliente.post("/sinistros", json=corpo(APOLICE_SEM_ROUBO, "2026-06-15", "Roubo"))

    assert resposta.status_code == 422
    assert_problema(resposta, "cobertura-nao-contratada")


async def test_retorna_404_quando_o_contexto_de_apolices_responde_404():
    async with subir_api() as api:
        resposta = await api.cliente.post("/sinistros", json=corpo(str(uuid.uuid4()), "2026-06-01", "Colisao"))

    assert resposta.status_code == 404
    assert_problema(resposta, "apolice-nao-encontrada")


async def test_endpoints_de_apolices():
    async with subir_api() as api:
        todas = await api.cliente.get("/apolices")
        uma = await api.cliente.get(f"/apolices/{APOLICE_VIGENTE}")
        nenhuma = await api.cliente.get(f"/apolices/{uuid.uuid4()}")

    assert [a["numero"] for a in todas.json()] == ["AP-0001", "AP-0002", "AP-0003"]
    assert uma.json()["coberturas"][0] == {"tipo": "Colisao", "limiteIndenizacao": 50000.0}
    assert_problema(nenhuma, "apolice-nao-encontrada")
