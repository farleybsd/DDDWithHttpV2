from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class PeriodoVigencia:
    inicio: date
    fim: date

    # __post_init__ roda logo depois do __init__ gerado pelo dataclass: é onde validamos.
    def __post_init__(self) -> None:
        if self.fim < self.inicio:
            raise ValueError("A data de fim da vigência não pode ser anterior à data de início.")

    def esta_vigente_em(self, data: date) -> bool:
        # Comparação encadeada: equivale a inicio <= data && data <= fim.
        return self.inicio <= data <= self.fim
