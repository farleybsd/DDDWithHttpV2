"""Corpo do POST /sinistros — o Request.cs + Validator.cs do C# juntos.

No Python, as regras do FluentValidation viram ``@field_validator`` do Pydantic. Se alguma falhar,
o FastAPI nem chama o endpoint e responde 400 ``validacao`` (ver common/erros/problem_details.py).
"""

from datetime import UTC, date, datetime
from uuid import UUID

from pydantic import Field, field_validator

from seguros.common.modelo_api import ModeloApi
from seguros.domain.sinistros.aggregates.sinistros.tipo_cobertura import TipoCobertura

_UUID_VAZIO = UUID(int=0)  # o Guid.Empty


class Request(ModeloApi):
    # Field(description=...) aparece no Swagger (o RequestParam do Summary.cs).
    # validate_default=True faz o validador rodar mesmo se o campo não vier no JSON.
    apolice_id: UUID | None = Field(
        default=None, validate_default=True,
        description="Identificador da apólice à qual o sinistro se refere",
    )
    data_ocorrencia: date | None = Field(
        default=None, validate_default=True,
        description="Data em que o sinistro ocorreu (não pode ser futura)",
    )
    tipo_cobertura: str = Field(
        default="", validate_default=True,
        description="Tipo de cobertura acionada (deve existir na apólice)",
    )
    descricao: str = Field(
        default="", validate_default=True,
        description="Descrição do ocorrido, até 500 caracteres",
    )

    @field_validator("apolice_id")
    @classmethod
    def _validar_apolice_id(cls, valor: UUID | None) -> UUID | None:
        if valor is None or valor == _UUID_VAZIO:
            raise ValueError("O identificador da apólice é obrigatório.")
        return valor

    @field_validator("data_ocorrencia")
    @classmethod
    def _validar_data_ocorrencia(cls, valor: date | None) -> date | None:
        if valor is None:
            raise ValueError("A data de ocorrência é obrigatória.")
        if valor > datetime.now(UTC).date():
            raise ValueError("A data de ocorrência não pode estar no futuro.")
        return valor

    @field_validator("tipo_cobertura")
    @classmethod
    def _validar_tipo_cobertura(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("O tipo de cobertura é obrigatório.")
        if TipoCobertura.de_texto(valor) is None:
            nomes = ", ".join(TipoCobertura.nomes())
            raise ValueError(f"O tipo de cobertura deve ser um dos seguintes: {nomes}.")
        return valor

    @field_validator("descricao")
    @classmethod
    def _validar_descricao(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("A descrição do sinistro é obrigatória.")
        if len(valor) > 500:
            raise ValueError("A descrição do sinistro deve ter no máximo 500 caracteres.")
        return valor
