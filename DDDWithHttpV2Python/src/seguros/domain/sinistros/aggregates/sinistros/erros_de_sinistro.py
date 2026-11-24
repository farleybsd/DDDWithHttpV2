"""Catálogo dos erros esperados do contexto de Sinistros (códigos publicados, nunca renomear)."""

from datetime import date
from typing import ClassVar
from uuid import UUID

from seguros.common.erro import Erro
from seguros.common.tipo_erro import TipoErro
from seguros.domain.sinistros.aggregates.sinistros.tipo_cobertura import TipoCobertura


class ErrosDeSinistro:
    @staticmethod
    def sinistro_nao_encontrado(sinistro_id: UUID) -> Erro:
        return Erro(
            codigo="sinistro-nao-encontrado",
            titulo="Sinistro não encontrado",
            detalhe=f"Nenhum sinistro foi encontrado com o Id '{sinistro_id}'.",
            tipo=TipoErro.NAO_ENCONTRADO,
            metadados={"sinistroId": sinistro_id},
        )

    @staticmethod
    def apolice_nao_encontrada(apolice_id: UUID) -> Erro:
        return Erro(
            codigo="apolice-nao-encontrada",
            titulo="Apólice não encontrada",
            detalhe=f"A apólice '{apolice_id}' não foi encontrada na API de Apólices.",
            tipo=TipoErro.NAO_ENCONTRADO,
            metadados={"apoliceId": apolice_id},
        )

    @staticmethod
    def apolice_fora_de_vigencia(data_ocorrencia: date, vigencia_inicio: date, vigencia_fim: date) -> Erro:
        return Erro(
            codigo="apolice-fora-de-vigencia",
            titulo="Apólice fora de vigência",
            # f-string com formato de data: o {data:yyyy-MM-dd} do C#.
            detalhe=f"A apólice não estava vigente em {data_ocorrencia:%Y-%m-%d}.",
            tipo=TipoErro.REGRA_DE_NEGOCIO,
            metadados={
                "dataOcorrencia": data_ocorrencia,
                "vigenciaInicio": vigencia_inicio,
                "vigenciaFim": vigencia_fim,
            },
        )

    @staticmethod
    def cobertura_nao_contratada(tipo_cobertura: TipoCobertura) -> Erro:
        return Erro(
            codigo="cobertura-nao-contratada",
            titulo="Cobertura não contratada",
            detalhe=f"A apólice não possui a cobertura '{tipo_cobertura}'.",
            tipo=TipoErro.REGRA_DE_NEGOCIO,
            metadados={"tipoCobertura": str(tipo_cobertura)},
        )

    DESCRICAO_OBRIGATORIA: ClassVar[Erro] = Erro(
        codigo="sinistro-descricao-obrigatoria",
        titulo="Descrição do sinistro obrigatória",
        detalhe="A descrição do sinistro é obrigatória.",
        tipo=TipoErro.VALIDACAO,
    )

    APOLICES_API_INDISPONIVEL: ClassVar[Erro] = Erro(
        codigo="apolices-api-indisponivel",
        titulo="API de Apólices indisponível",
        detalhe="Não foi possível consultar a API de Apólices no momento. Tente novamente em instantes.",
        tipo=TipoErro.INDISPONIVEL,
    )
    """A API de Apólices não respondeu (timeout, circuito aberto, falha de rede ou 5xx). O motivo
    técnico fica só no log: o cliente recebe um texto fixo."""
