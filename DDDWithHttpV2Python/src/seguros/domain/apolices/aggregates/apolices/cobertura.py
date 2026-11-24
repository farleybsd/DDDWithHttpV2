from dataclasses import dataclass
from decimal import Decimal

from seguros.domain.apolices.aggregates.apolices.tipo_cobertura import TipoCobertura


@dataclass(frozen=True, slots=True)
class Cobertura:
    tipo: TipoCobertura
    # Decimal (e não float) para dinheiro: Decimal("0.1") + Decimal("0.2") == Decimal("0.3").
    limite_indenizacao: Decimal
