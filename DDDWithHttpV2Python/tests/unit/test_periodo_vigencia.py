from datetime import date

import pytest

from seguros.domain.apolices.aggregates.apolices.periodo_vigencia import PeriodoVigencia

PERIODO = PeriodoVigencia(date(2026, 1, 1), date(2026, 12, 31))


def test_esta_vigente_em_data_dentro_do_periodo():
    assert PERIODO.esta_vigente_em(date(2026, 6, 15))


# parametrize roda o mesmo teste com cada valor (o [Theory] + [InlineData] do xUnit).
@pytest.mark.parametrize("data", [date(2026, 1, 1), date(2026, 12, 31)])
def test_esta_vigente_nas_bordas_do_periodo(data):
    assert PERIODO.esta_vigente_em(data)


def test_nao_esta_vigente_antes_do_inicio():
    assert not PERIODO.esta_vigente_em(date(2025, 12, 31))


def test_nao_esta_vigente_depois_do_fim():
    assert not PERIODO.esta_vigente_em(date(2027, 1, 1))


def test_construtor_lanca_erro_quando_fim_anterior_ao_inicio():
    # pytest.raises é o Assert.Throws.
    with pytest.raises(ValueError):
        PeriodoVigencia(date(2026, 12, 31), date(2026, 1, 1))
