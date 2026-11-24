from uuid import UUID

from seguros.common.result import Result
from seguros.domain.sinistros.aggregates.sinistros.erros_de_sinistro import ErrosDeSinistro
from seguros.domain.sinistros.aggregates.sinistros.sinistro_repository import SinistroRepository
from seguros.domain.sinistros.contracts.sinistro_response import SinistroResponse
from seguros.domain.sinistros.features.registrar_sinistro.handler import mapear


class Handler:
    def __init__(self, repository: SinistroRepository) -> None:
        self._repository = repository

    async def handle(self, id: UUID) -> Result[SinistroResponse]:
        sinistro = await self._repository.obter_por_id(id)
        if sinistro is None:
            return Result.failure(ErrosDeSinistro.sinistro_nao_encontrado(id))
        return Result.success(mapear(sinistro))
