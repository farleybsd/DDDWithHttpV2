"""Espelha o contrato JSON de GET /apolices/{id}.

É uma CÓPIA do contrato, e não um import de ``ApoliceResponse``: Sinistros não pode depender de
tipos do contexto de Apólices. Campos extras no JSON são ignorados (padrão do Pydantic), então
Apólices pode acrescentar campos sem quebrar Sinistros.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from seguros.common.modelo_api import ModeloApi


class SeguradoApiDto(ModeloApi):
    nome: str
    documento: str


class VigenciaApiDto(ModeloApi):
    inicio: date
    fim: date


class CoberturaApiDto(ModeloApi):
    tipo: str
    limite_indenizacao: Decimal


class ApoliceApiDto(ModeloApi):
    id: UUID
    numero: str
    segurado: SeguradoApiDto
    vigencia: VigenciaApiDto
    coberturas: list[CoberturaApiDto]
