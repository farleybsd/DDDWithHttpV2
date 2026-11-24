"""Base dos contratos JSON da API (requests, responses e DTOs).

No C# o System.Text.Json já converte ``ApoliceId`` -> ``apoliceId``. No Python os atributos são
snake_case (``apolice_id``), então pedimos ao Pydantic para usar camelCase no JSON.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ModeloApi(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,  # apolice_id <-> "apoliceId" no JSON
        validate_by_name=True,  # aceita também apolice_id=... ao criar no código
        validate_by_alias=True,  # aceita "apoliceId" vindo do JSON
        serialize_by_alias=True,  # ao gerar JSON, usa "apoliceId"
    )
