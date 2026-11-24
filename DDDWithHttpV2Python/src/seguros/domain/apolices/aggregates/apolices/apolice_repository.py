from typing import Protocol
from uuid import UUID

from seguros.domain.apolices.aggregates.apolices.apolice import Apolice


class ApoliceRepository(Protocol):
    """A "interface" do repositório (o IApoliceRepository).

    ``Protocol`` é tipagem estrutural: qualquer classe que tenha estes métodos serve, sem
    precisar herdar daqui (como "duck typing" verificado pelo type checker).
    O ``...`` no corpo significa "sem implementação".
    """

    async def obter_por_id(self, id: UUID) -> Apolice | None: ...

    async def obter_todas(self) -> list[Apolice]: ...
