"""Os dados de uma apólice obtidos via HTTP, já no vocabulário de Sinistros.

É o resultado da tradução do contrato externo (DTO) — nenhum tipo do contexto de Apólices é
referenciado aqui.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from seguros.domain.sinistros.aggregates.sinistros.tipo_cobertura import TipoCobertura


@dataclass(frozen=True, slots=True)
class ApoliceReferenciada:
    apolice_id: UUID
    vigencia_inicio: date
    vigencia_fim: date
    coberturas: tuple[TipoCobertura, ...]

    def esta_vigente_em(self, data: date) -> bool:
        return self.vigencia_inicio <= data <= self.vigencia_fim

    def possui_cobertura(self, tipo: TipoCobertura) -> bool:
        return tipo in self.coberturas
