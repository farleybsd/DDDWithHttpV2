from uuid import UUID

from seguros.domain.sinistros.aggregates.sinistros.sinistro import Sinistro


class InMemorySinistroRepository:
    def __init__(self) -> None:
        self._sinistros: dict[UUID, Sinistro] = {}

    async def adicionar(self, sinistro: Sinistro) -> None:
        self._sinistros[sinistro.id] = sinistro

    async def obter_por_id(self, id: UUID) -> Sinistro | None:
        return self._sinistros.get(id)

    async def listar_por_apolice(self, apolice_id: UUID) -> list[Sinistro]:
        # O .Where(...).OrderByDescending(...) do LINQ.
        return sorted(
            (s for s in self._sinistros.values() if s.apolice_id == apolice_id),
            key=lambda s: s.data_registro,
            reverse=True,
        )
