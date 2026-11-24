"""Catálogo dos erros esperados do contexto de Apólices.

Cada ``codigo`` é publicado (aparece no ``type`` e no ``code`` do ProblemDetails) e não pode ser
renomeado: mudou o significado, crie um código novo e mantenha o antigo.
"""

from typing import ClassVar
from uuid import UUID

from seguros.common.erro import Erro
from seguros.common.tipo_erro import TipoErro


class ErrosDeApolice:
    # @staticmethod: função "pendurada" na classe, sem self nem cls (o "public static" do C#).
    @staticmethod
    def nao_encontrada(apolice_id: UUID) -> Erro:
        return Erro(
            codigo="apolice-nao-encontrada",
            titulo="Apólice não encontrada",
            detalhe=f"Nenhuma apólice foi encontrada com o Id '{apolice_id}'.",
            tipo=TipoErro.NAO_ENCONTRADO,
            metadados={"apoliceId": apolice_id},
        )

    # ClassVar: atributo da classe (o "static readonly" do C#), não de cada instância.
    NUMERO_OBRIGATORIO: ClassVar[Erro] = Erro(
        codigo="apolice-numero-obrigatorio",
        titulo="Número da apólice obrigatório",
        detalhe="O número da apólice é obrigatório.",
        tipo=TipoErro.VALIDACAO,
    )

    SEM_COBERTURA: ClassVar[Erro] = Erro(
        codigo="apolice-sem-cobertura",
        titulo="Apólice sem cobertura",
        detalhe="A apólice deve ter ao menos uma cobertura.",
        tipo=TipoErro.REGRA_DE_NEGOCIO,
    )
