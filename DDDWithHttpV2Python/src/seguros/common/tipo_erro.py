"""Classe de um erro esperado, na linguagem do domínio (equivale ao TipoErro.cs).

O domínio não conhece HTTP: a tradução de cada tipo para um status code acontece em um único
lugar (``common/erros/erro_para_http.py``).
"""

from enum import Enum, auto


class TipoErro(Enum):
    # auto() gera os valores 1, 2, 3... — só nos importa o nome, como num enum do C#.
    VALIDACAO = auto()
    NAO_ENCONTRADO = auto()
    CONFLITO = auto()
    REGRA_DE_NEGOCIO = auto()
    INDISPONIVEL = auto()
