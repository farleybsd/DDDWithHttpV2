from uuid import UUID

from seguros.domain.sinistros.aggregates.sinistros.sinistro_repository import SinistroRepository
from seguros.domain.sinistros.contracts.sinistro_response import SinistroResponse
from seguros.domain.sinistros.features.registrar_sinistro.handler import mapear


class Handler:
    def __init__(self, repository: SinistroRepository) -> None:
        self._repository = repository

    async def handle(self, apolice_id: UUID) -> list[SinistroResponse]:
        sinistros = await self._repository.listar_por_apolice(apolice_id)
        return [mapear(s) for s in sinistros]
