import uuid
from datetime import UTC, date, datetime
from uuid import UUID

from seguros.common.result import Result
from seguros.domain.sinistros.aggregates.sinistros.apolice_referenciada import ApoliceReferenciada
from seguros.domain.sinistros.aggregates.sinistros.erros_de_sinistro import ErrosDeSinistro
from seguros.domain.sinistros.aggregates.sinistros.status_sinistro import StatusSinistro
from seguros.domain.sinistros.aggregates.sinistros.tipo_cobertura import TipoCobertura


class Sinistro:
    """Raiz do agregado de Sinistros. Crie sempre por ``Sinistro.registrar(...)``."""

    def __init__(
        self,
        id: UUID,
        apolice_id: UUID,
        data_ocorrencia: date,
        tipo_cobertura: TipoCobertura,
        descricao: str,
        status: StatusSinistro,
        data_registro: datetime,
    ) -> None:
        self._id = id
        self._apolice_id = apolice_id
        self._data_ocorrencia = data_ocorrencia
        self._tipo_cobertura = tipo_cobertura
        self._descricao = descricao
        self._status = status
        self._data_registro = data_registro

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def apolice_id(self) -> UUID:
        return self._apolice_id

    @property
    def data_ocorrencia(self) -> date:
        return self._data_ocorrencia

    @property
    def tipo_cobertura(self) -> TipoCobertura:
        return self._tipo_cobertura

    @property
    def descricao(self) -> str:
        return self._descricao

    @property
    def status(self) -> StatusSinistro:
        return self._status

    @property
    def data_registro(self) -> datetime:
        return self._data_registro

    @classmethod
    def registrar(
        cls,
        apolice_id: UUID,
        data_ocorrencia: date,
        tipo_cobertura: TipoCobertura,
        descricao: str,
        apolice: ApoliceReferenciada,
    ) -> Result["Sinistro"]:
        """Registra um sinistro validando, a partir dos dados já consultados da API de Apólices,
        que a apólice estava vigente na data da ocorrência e possui a cobertura solicitada."""
        if not descricao or not descricao.strip():
            return Result.failure(ErrosDeSinistro.DESCRICAO_OBRIGATORIA)

        if not apolice.esta_vigente_em(data_ocorrencia):
            return Result.failure(
                ErrosDeSinistro.apolice_fora_de_vigencia(
                    data_ocorrencia, apolice.vigencia_inicio, apolice.vigencia_fim
                )
            )

        if not apolice.possui_cobertura(tipo_cobertura):
            return Result.failure(ErrosDeSinistro.cobertura_nao_contratada(tipo_cobertura))

        return Result.success(
            cls(
                id=uuid.uuid4(),  # o Guid.NewGuid()
                apolice_id=apolice_id,
                data_ocorrencia=data_ocorrencia,
                tipo_cobertura=tipo_cobertura,
                descricao=descricao,
                status=StatusSinistro.REGISTRADO,
                data_registro=datetime.now(UTC),  # o DateTime.UtcNow
            )
        )
