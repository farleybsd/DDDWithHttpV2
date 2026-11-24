"""Vocabulário PRÓPRIO do contexto de Sinistros.

Existe uma "cópia" em Apólices de propósito: os contextos não compartilham tipos. A tradução
entre os dois vocabulários acontece no adaptador HTTP (camada anticorrupção).
"""

from enum import StrEnum
from typing import Self


class TipoCobertura(StrEnum):
    COLISAO = "Colisao"
    ROUBO = "Roubo"
    INCENDIO = "Incendio"
    DANOS_TERCEIROS = "DanosTerceiros"

    @classmethod
    def de_texto(cls, texto: str) -> Self | None:
        """Converte ignorando maiúsculas/minúsculas (o ``Enum.TryParse(..., ignoreCase: true)``).
        Devolve None se o texto não for um tipo conhecido."""
        for membro in cls:
            if membro.value.casefold() == texto.strip().casefold():
                return membro
        return None

    @classmethod
    def nomes(cls) -> list[str]:
        return [m.value for m in cls]
