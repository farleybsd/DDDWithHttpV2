"""Repositório em memória com dados fictícios fixos, pensados para exercitar os cenários de
Sinistros (vigente com cobertura, expirada, vigente sem cobertura de Roubo)."""

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from uuid import UUID

from seguros.domain.apolices.aggregates.apolices.apolice import Apolice
from seguros.domain.apolices.aggregates.apolices.cobertura import Cobertura
from seguros.domain.apolices.aggregates.apolices.periodo_vigencia import PeriodoVigencia
from seguros.domain.apolices.aggregates.apolices.segurado import Segurado
from seguros.domain.apolices.aggregates.apolices.tipo_cobertura import TipoCobertura


class InMemoryApoliceRepository:
    # Não herda de ApoliceRepository: por ser um Protocol, basta ter os mesmos métodos.

    def __init__(self) -> None:
        # Um dict comum basta: o asyncio roda num único thread, então não precisamos do
        # ConcurrentDictionary do C#.
        self._apolices: dict[UUID, Apolice] = {a.id: a for a in _criar_dados_ficticios()}

    async def obter_por_id(self, id: UUID) -> Apolice | None:
        return self._apolices.get(id)

    async def obter_todas(self) -> list[Apolice]:
        return sorted(self._apolices.values(), key=lambda a: a.numero)


# Função geradora: cada "yield" entrega um item (o "yield return" do C#).
def _criar_dados_ficticios() -> Iterator[Apolice]:
    yield Apolice.criar(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        numero="AP-0001",
        segurado=Segurado("Ana Souza", "111.111.111-11"),
        vigencia=PeriodoVigencia(date(2026, 1, 1), date(2026, 12, 31)),
        coberturas=[
            Cobertura(TipoCobertura.COLISAO, Decimal("50000")),
            Cobertura(TipoCobertura.ROUBO, Decimal("30000")),
            Cobertura(TipoCobertura.INCENDIO, Decimal("40000")),
        ],
    ).value

    yield Apolice.criar(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        numero="AP-0002",
        segurado=Segurado("Bruno Lima", "222.222.222-22"),
        vigencia=PeriodoVigencia(date(2024, 1, 1), date(2024, 12, 31)),
        coberturas=[Cobertura(TipoCobertura.COLISAO, Decimal("20000"))],
    ).value

    yield Apolice.criar(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        numero="AP-0003",
        segurado=Segurado("Carla Dias", "333.333.333-33"),
        vigencia=PeriodoVigencia(date(2026, 6, 1), date(2027, 5, 31)),
        coberturas=[
            Cobertura(TipoCobertura.INCENDIO, Decimal("15000")),
            Cobertura(TipoCobertura.DANOS_TERCEIROS, Decimal("10000")),
        ],
    ).value
