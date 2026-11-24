"""Erro esperado (equivale ao Erro.cs).

Faz parte do negócio e o cliente consegue agir sobre ele. Viaja como valor dentro de um
``Result``, nunca como exceção.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from seguros.common.tipo_erro import TipoErro


# @dataclass gera __init__, __repr__ e __eq__ a partir dos campos anotados.
# frozen=True deixa o objeto imutável (como um "record" do C#).
# slots=True economiza memória e impede criar atributos por engano.
@dataclass(frozen=True, slots=True)
class Erro:
    codigo: str
    """Identificador estável e publicado do erro. Nunca muda: mudou o significado, crie outro."""

    titulo: str
    """Resumo fixo por código. Dados da ocorrência não entram aqui."""

    detalhe: str
    """Explicação desta ocorrência, para humanos. Clientes não devem fazer parse dele."""

    tipo: TipoErro
    """Classe do erro, usada para escolher o status HTTP."""

    metadados: Mapping[str, Any] | None = None
    """Dados estruturados da ocorrência, expostos como extensões do ProblemDetails."""
