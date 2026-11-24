from datetime import date, datetime
from uuid import UUID

from seguros.common.modelo_api import ModeloApi


class SinistroResponse(ModeloApi):
    id: UUID
    apolice_id: UUID
    data_ocorrencia: date
    tipo_cobertura: str
    descricao: str
    status: str
    data_registro: datetime
