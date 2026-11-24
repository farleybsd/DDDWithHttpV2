"""Contrato HTTP público do contexto de Apólices (o que vai no JSON de GET /apolices/{id})."""

from datetime import date
from uuid import UUID

from seguros.common.modelo_api import ModeloApi


class SeguradoResponse(ModeloApi):
    nome: str
    documento: str


class VigenciaResponse(ModeloApi):
    inicio: date
    fim: date


class CoberturaResponse(ModeloApi):
    tipo: str
    # float no JSON (número), como o decimal do C#. Com Decimal o Pydantic geraria uma string.
    limite_indenizacao: float


class ApoliceResponse(ModeloApi):
    id: UUID
    numero: str
    segurado: SeguradoResponse
    vigencia: VigenciaResponse
    coberturas: list[CoberturaResponse]
