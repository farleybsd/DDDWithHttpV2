"""Resultado da consulta à API de Apólices, no vocabulário de Sinistros.

Distingue "apólice não existe" (resposta de negócio -> 404) de "serviço indisponível" (falha de
infraestrutura -> 503). No C# era um ``abstract record`` com três ``sealed record`` dentro; no
Python são três dataclasses e uma *união de tipos*. Quem usa faz ``match consulta: case ...``.
"""

from dataclasses import dataclass

from seguros.domain.sinistros.aggregates.sinistros.apolice_referenciada import ApoliceReferenciada


@dataclass(frozen=True, slots=True)
class Encontrada:
    apolice: ApoliceReferenciada


@dataclass(frozen=True, slots=True)
class NaoEncontrada:
    pass


@dataclass(frozen=True, slots=True)
class Indisponivel:
    motivo: str


# "type X = A | B | C" (Python 3.12+): um apelido para "qualquer um destes três tipos".
type ApoliceConsultaResultado = Encontrada | NaoEncontrada | Indisponivel
