import uuid
from datetime import date
from decimal import Decimal

from seguros.domain.apolices.aggregates.apolices.apolice import Apolice
from seguros.domain.apolices.aggregates.apolices.cobertura import Cobertura
from seguros.domain.apolices.aggregates.apolices.periodo_vigencia import PeriodoVigencia
from seguros.domain.apolices.aggregates.apolices.segurado import Segurado
from seguros.domain.apolices.aggregates.apolices.tipo_cobertura import TipoCobertura

SEGURADO = Segurado("Ana Souza", "111.111.111-11")
VIGENCIA = PeriodoVigencia(date(2026, 1, 1), date(2026, 12, 31))
COLISAO = Cobertura(TipoCobertura.COLISAO, Decimal("50000"))
ROUBO = Cobertura(TipoCobertura.ROUBO, Decimal("30000"))


def criar(numero="AP-0001", coberturas=(COLISAO,)):
    return Apolice.criar(uuid.uuid4(), numero, SEGURADO, VIGENCIA, coberturas)


def test_criar_tem_sucesso_quando_dados_validos():
    assert criar().is_success


def test_criar_falha_quando_numero_vazio():
    resultado = criar(numero="")
    assert resultado.is_failure
    assert resultado.error.codigo == "apolice-numero-obrigatorio"


def test_criar_falha_quando_sem_coberturas():
    resultado = criar(coberturas=[])
    assert resultado.is_failure
    assert resultado.error.codigo == "apolice-sem-cobertura"


def test_possui_cobertura_contratada():
    assert criar(coberturas=[COLISAO, ROUBO]).value.possui_cobertura(TipoCobertura.ROUBO)


def test_nao_possui_cobertura_nao_contratada():
    assert not criar().value.possui_cobertura(TipoCobertura.INCENDIO)


def test_esta_vigente_em_delega_para_periodo_de_vigencia():
    apolice = criar().value
    assert apolice.esta_vigente_em(date(2026, 6, 1))
    assert not apolice.esta_vigente_em(date(2024, 6, 1))
