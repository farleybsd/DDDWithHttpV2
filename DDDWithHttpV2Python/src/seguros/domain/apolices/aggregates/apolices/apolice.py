from collections.abc import Iterable
from datetime import date
from uuid import UUID

from seguros.common.result import Result
from seguros.domain.apolices.aggregates.apolices.cobertura import Cobertura
from seguros.domain.apolices.aggregates.apolices.erros_de_apolice import ErrosDeApolice
from seguros.domain.apolices.aggregates.apolices.periodo_vigencia import PeriodoVigencia
from seguros.domain.apolices.aggregates.apolices.segurado import Segurado
from seguros.domain.apolices.aggregates.apolices.tipo_cobertura import TipoCobertura


class Apolice:
    """Raiz do agregado de Apólices.

    Python não tem construtor privado: por convenção, crie sempre por ``Apolice.criar(...)``,
    que valida as regras. Atributos com "_" na frente são "privados" por convenção, e as
    @property expõem só leitura (o ``{ get; }`` do C#).
    """

    def __init__(
        self,
        id: UUID,
        numero: str,
        segurado: Segurado,
        vigencia: PeriodoVigencia,
        coberturas: tuple[Cobertura, ...],
    ) -> None:
        self._id = id
        self._numero = numero
        self._segurado = segurado
        self._vigencia = vigencia
        self._coberturas = coberturas  # tupla = lista imutável (o IReadOnlyList)

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def numero(self) -> str:
        return self._numero

    @property
    def segurado(self) -> Segurado:
        return self._segurado

    @property
    def vigencia(self) -> PeriodoVigencia:
        return self._vigencia

    @property
    def coberturas(self) -> tuple[Cobertura, ...]:
        return self._coberturas

    @classmethod
    def criar(
        cls,
        id: UUID,
        numero: str,
        segurado: Segurado,
        vigencia: PeriodoVigencia,
        coberturas: Iterable[Cobertura],
    ) -> Result["Apolice"]:
        if not numero or not numero.strip():  # o string.IsNullOrWhiteSpace
            return Result.failure(ErrosDeApolice.NUMERO_OBRIGATORIO)

        lista_coberturas = tuple(coberturas)
        if not lista_coberturas:  # tupla vazia é "falsa"
            return Result.failure(ErrosDeApolice.SEM_COBERTURA)

        return Result.success(cls(id, numero, segurado, vigencia, lista_coberturas))

    def esta_vigente_em(self, data: date) -> bool:
        return self._vigencia.esta_vigente_em(data)

    def possui_cobertura(self, tipo: TipoCobertura) -> bool:
        # any(...) com um "generator expression" é o .Any(c => ...) do LINQ.
        return any(c.tipo == tipo for c in self._coberturas)
