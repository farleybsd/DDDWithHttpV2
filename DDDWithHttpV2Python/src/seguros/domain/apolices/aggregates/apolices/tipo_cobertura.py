from enum import StrEnum


class TipoCobertura(StrEnum):
    """StrEnum: cada membro É uma string. ``str(TipoCobertura.COLISAO) == "Colisao"``, que é o
    texto publicado no contrato JSON (o ``.ToString()`` do enum no C#)."""

    COLISAO = "Colisao"
    ROUBO = "Roubo"
    INCENDIO = "Incendio"
    DANOS_TERCEIROS = "DanosTerceiros"
