from datetime import date
from uuid import UUID

from seguros.common.modelo_api import ModeloApi


class ApoliceDoSinistroResponse(ModeloApi):
    """Dados da apólice vinculada a um sinistro, obtidos em tempo real da API de Apólices. Os dois
    últimos campos são conclusões do domínio de Sinistros (não vêm prontos da API externa)."""

    sinistro_id: UUID
    apolice_id: UUID
    data_ocorrencia: date
    tipo_cobertura: str
    vigencia_inicio: date
    vigencia_fim: date
    coberturas: list[str]
    vigente_na_data_ocorrencia: bool
    possui_cobertura_do_sinistro: bool
