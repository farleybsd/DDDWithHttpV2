from uuid import UUID

from seguros.common.result import Result
from seguros.domain.apolices.aggregates.apolices.apolice import Apolice
from seguros.domain.apolices.aggregates.apolices.apolice_repository import ApoliceRepository
from seguros.domain.apolices.aggregates.apolices.erros_de_apolice import ErrosDeApolice
from seguros.domain.apolices.contracts.apolice_response import (
    ApoliceResponse,
    CoberturaResponse,
    SeguradoResponse,
    VigenciaResponse,
)


class Handler:
    """Caso de uso: consultar uma apólice. Recebe as dependências pelo construtor (como no C#)."""

    def __init__(self, repository: ApoliceRepository) -> None:
        self._repository = repository

    async def handle(self, id: UUID) -> Result[ApoliceResponse]:
        apolice = await self._repository.obter_por_id(id)
        if apolice is None:
            return Result.failure(ErrosDeApolice.nao_encontrada(id))

        return Result.success(mapear(apolice))


def mapear(apolice: Apolice) -> ApoliceResponse:
    return ApoliceResponse(
        id=apolice.id,
        numero=apolice.numero,
        segurado=SeguradoResponse(nome=apolice.segurado.nome, documento=apolice.segurado.documento),
        vigencia=VigenciaResponse(inicio=apolice.vigencia.inicio, fim=apolice.vigencia.fim),
        # "list comprehension": o .Select(...).ToList() do LINQ.
        coberturas=[
            CoberturaResponse(tipo=str(c.tipo), limite_indenizacao=float(c.limite_indenizacao))
            for c in apolice.coberturas
        ],
    )
