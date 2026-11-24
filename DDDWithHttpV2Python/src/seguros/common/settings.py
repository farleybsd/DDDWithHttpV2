"""Configurações tipadas (equivale a ServicesSettings.cs + HttpResilienceSettings.cs + AddSettings).

Ordem de carga (o último vence), como no ASP.NET Core:
    config/base.env  ->  config/<ambiente>.env  ->  config/local.env  ->  variáveis de ambiente

O ambiente vem da variável ``AMBIENTE`` (development, qas, production), equivalente ao
``ASPNETCORE_ENVIRONMENT``. Se ``SERVICES_SETTINGS__APOLICES_URI`` não for uma URL http(s)
absoluta, ``carregar_settings()`` lança erro e a aplicação nem sobe (como o ``ValidateOnStart``).
"""

import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Path(__file__) é este arquivo; .parents[3] sobe até a raiz do projeto (src/seguros/common -> raiz).
RAIZ_DO_PROJETO = Path(__file__).resolve().parents[3]
PASTA_CONFIG = RAIZ_DO_PROJETO / "config"


def eh_url_http_absoluta(url: str) -> bool:
    partes = urlparse(url)
    return partes.scheme in ("http", "https") and bool(partes.netloc)


def com_barra_final(url: str) -> str:
    """Garante a barra final: sem ela, um endereço com caminho (ex.: ``https://gateway/seguros``)
    perderia esse caminho ao combinar com a rota relativa."""
    return url if url.endswith("/") else url + "/"


class ServicesSettings(BaseModel):
    """Endereço HTTP de cada bounded context. Para extrair Apólices para outro serviço, basta
    trocar o endereço aqui — nenhum código de Sinistros muda."""

    # validate_default=True: valida mesmo quando o valor não foi informado (o padrão "").
    apolices_uri: str = Field(default="", validate_default=True)

    @field_validator("apolices_uri")
    @classmethod
    def _validar_apolices_uri(cls, valor: str) -> str:
        if not eh_url_http_absoluta(valor):
            raise ValueError(
                "'services_settings.apolices_uri' precisa ser uma URL http(s) absoluta. Defina-a "
                "em config/<ambiente>.env ou na variável de ambiente SERVICES_SETTINGS__APOLICES_URI."
            )
        return valor


class ConcurrencyLimiterSettings(BaseModel):
    permit_limit: int = Field(default=50, ge=1)
    """Chamadas simultâneas permitidas."""
    queue_limit: int = Field(default=10, ge=0)
    """Chamadas que podem aguardar na fila quando o limite é atingido. 0 = recusa na hora."""


class RetrySettings(BaseModel):
    max_retry_attempts: int = Field(default=1, ge=0)
    """Retentativas após a primeira chamada. 0 desliga o retry."""
    base_delay_segundos: float = Field(default=0.5, ge=0)


class CircuitBreakerSettings(BaseModel):
    failure_ratio: float = Field(default=0.5, gt=0, le=1)
    sampling_duration_segundos: float = 10
    minimum_throughput: int = Field(default=4, ge=1)
    break_duration_segundos: float = 15


class HttpResilienceSettings(BaseModel):
    """Parâmetros do pipeline de resiliência das chamadas HTTP entre contextos."""

    timeout_segundos: float = Field(default=2, gt=0)
    # default_factory cria um objeto novo para cada instância (nunca use um objeto mutável
    # como valor padrão direto — ele seria compartilhado entre todas as instâncias).
    concurrency_limiter: ConcurrencyLimiterSettings = Field(default_factory=ConcurrencyLimiterSettings)
    retry: RetrySettings = Field(default_factory=RetrySettings)
    circuit_breaker: CircuitBreakerSettings = Field(default_factory=CircuitBreakerSettings)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",  # HTTP_RESILIENCE__RETRY__MAX_RETRY_ATTEMPTS -> .http_resilience.retry...
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ambiente: str = "development"
    nivel_log: str = "INFO"
    services_settings: ServicesSettings = Field(default_factory=ServicesSettings)
    http_resilience: HttpResilienceSettings = Field(default_factory=HttpResilienceSettings)


def carregar_settings(ambiente: str | None = None) -> Settings:
    ambiente = (ambiente or os.getenv("AMBIENTE") or "development").lower()
    arquivos = (
        PASTA_CONFIG / "base.env",
        PASTA_CONFIG / f"{ambiente}.env",
        PASTA_CONFIG / "local.env",  # opcional; arquivos inexistentes são ignorados
    )
    return Settings(_env_file=arquivos, ambiente=ambiente)
