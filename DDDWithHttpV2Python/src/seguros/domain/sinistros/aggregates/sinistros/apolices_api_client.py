from typing import Protocol
from uuid import UUID

from seguros.domain.sinistros.aggregates.sinistros.apolice_consulta_resultado import (
    ApoliceConsultaResultado,
)


class ApolicesApiClient(Protocol):
    """PORTA definida pelo domínio de Sinistros para consultar a API de Apólices (o
    IApolicesApiClient). Diz O QUE Sinistros precisa; a implementação que fala HTTP (o adaptador)
    fica em ``infrastructure/apolices_api``."""

    async def consultar_apolice(self, apolice_id: UUID) -> ApoliceConsultaResultado: ...
