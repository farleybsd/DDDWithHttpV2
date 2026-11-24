from seguros.domain.apolices.aggregates.apolices.apolice_repository import ApoliceRepository
from seguros.domain.apolices.contracts.apolice_response import ApoliceResponse
from seguros.domain.apolices.features.consultar_apolice.handler import mapear


class Handler:
    def __init__(self, repository: ApoliceRepository) -> None:
        self._repository = repository

    async def handle(self) -> list[ApoliceResponse]:
        apolices = await self._repository.obter_todas()
        return [mapear(a) for a in apolices]
