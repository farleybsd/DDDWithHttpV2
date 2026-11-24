from typing import Protocol
from uuid import UUID

from seguros.domain.sinistros.aggregates.sinistros.sinistro import Sinistro


class SinistroRepository(Protocol):
    async def adicionar(self, sinistro: Sinistro) -> None: ...

    async def obter_por_id(self, id: UUID) -> Sinistro | None: ...

    async def listar_por_apolice(self, apolice_id: UUID) -> list[Sinistro]: ...
