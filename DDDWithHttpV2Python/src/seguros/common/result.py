"""Result: sucesso com um valor OU falha com um Erro (equivale ao Result.cs).

``class Result[T]`` é a sintaxe de genéricos do Python 3.12+ (igual a ``Result<T>`` no C#).
Python não tem conversão implícita (``return erro;`` no C#), então usamos
``Result.failure(erro)`` explicitamente.
"""

from dataclasses import dataclass
from typing import cast

from seguros.common.erro import Erro


@dataclass(frozen=True, slots=True)
class Result[T]:
    _value: T | None = None
    error: Erro | None = None

    @property
    def is_success(self) -> bool:
        return self.error is None

    @property
    def is_failure(self) -> bool:
        return not self.is_success

    @property
    def value(self) -> T:
        """O valor do sucesso. Acessar em uma falha é bug de programação."""
        if self.error is not None:
            raise ValueError(f"Result em falha ({self.error.codigo}) não tem valor.")
        return cast(T, self._value)

    # @classmethod recebe a própria classe (cls) — é o jeito Python de "static factory".
    @classmethod
    def success(cls, value: T) -> "Result[T]":
        return cls(_value=value)

    @classmethod
    def failure(cls, error: Erro) -> "Result[T]":
        return cls(error=error)
