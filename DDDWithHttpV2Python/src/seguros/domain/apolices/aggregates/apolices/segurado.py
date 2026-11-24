from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Segurado:
    """Value object: imutável e comparado pelos valores (o ``sealed record`` do C#)."""

    nome: str
    documento: str
