import uuid
from datetime import date

from seguros.domain.sinistros.aggregates.sinistros.apolice_referenciada import ApoliceReferenciada
from seguros.domain.sinistros.aggregates.sinistros.sinistro import Sinistro
from seguros.domain.sinistros.aggregates.sinistros.status_sinistro import StatusSinistro
from seguros.domain.sinistros.aggregates.sinistros.tipo_cobertura import TipoCobertura

APOLICE_ID = uuid.uuid4()


# *coberturas recebe qualquer quantidade de argumentos (o "params" do C#).
def apolice_vigente_com(*coberturas: TipoCobertura) -> ApoliceReferenciada:
    return ApoliceReferenciada(APOLICE_ID, date(2026, 1, 1), date(2026, 12, 31), coberturas)


def test_registrar_tem_sucesso_quando_apolice_vigente_e_com_cobertura():
    resultado = Sinistro.registrar(
        APOLICE_ID, date(2026, 6, 1), TipoCobertura.COLISAO, "Colisão na Av. Paulista",
        apolice_vigente_com(TipoCobertura.COLISAO),
    )

    assert resultado.is_success
    assert resultado.value.status == StatusSinistro.REGISTRADO


def test_registrar_falha_quando_apolice_fora_de_vigencia():
    resultado = Sinistro.registrar(
        APOLICE_ID, date(2025, 6, 1), TipoCobertura.COLISAO, "Fora do período",
        apolice_vigente_com(TipoCobertura.COLISAO),
    )

    assert resultado.is_failure
    assert resultado.error.codigo == "apolice-fora-de-vigencia"


def test_registrar_falha_quando_apolice_nao_possui_a_cobertura():
    resultado = Sinistro.registrar(
        APOLICE_ID, date(2026, 6, 1), TipoCobertura.ROUBO, "Furto do veículo",
        apolice_vigente_com(TipoCobertura.INCENDIO),
    )

    assert resultado.is_failure
    assert resultado.error.codigo == "cobertura-nao-contratada"


def test_registrar_falha_quando_descricao_vazia():
    resultado = Sinistro.registrar(
        APOLICE_ID, date(2026, 6, 1), TipoCobertura.COLISAO, "   ",
        apolice_vigente_com(TipoCobertura.COLISAO),
    )

    assert resultado.is_failure
    assert resultado.error.codigo == "sinistro-descricao-obrigatoria"


def test_tipo_cobertura_de_texto_ignora_maiusculas():
    assert TipoCobertura.de_texto("colisao") is TipoCobertura.COLISAO
    assert TipoCobertura.de_texto("Inexistente") is None
