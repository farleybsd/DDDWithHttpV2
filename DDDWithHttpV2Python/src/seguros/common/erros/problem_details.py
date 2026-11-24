"""Garante que TODO erro sai como ``application/problem+json`` (RFC 9457).

Junta o que no C# estava em ``AddProblemDetailsRfc9457``, ``UseProblemDetailsRfc9457`` e
``GlobalExceptionHandler``:

* erros inesperados (exceções)  -> 500 ``erro-interno``, sem vazar detalhes;
* erros de validação do corpo    -> 400 ``validacao``, com os erros de cada campo em ``errors``;
* rotas inexistentes (404/405)   -> ProblemDetails em vez de corpo vazio/HTML.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic.alias_generators import to_camel
from starlette.exceptions import HTTPException as StarletteHTTPException

from seguros.common.erros.erro_para_http import (
    BASE_TIPOS,
    CODIGO_ERRO_INTERNO,
    CODIGO_VALIDACAO,
    resposta_problema,
)

logger = logging.getLogger(__name__)

# Mensagens em português para os erros "de tipo" que o Pydantic gera sozinho.
_MENSAGENS_PADRAO = {
    "missing": "Campo obrigatório.",
    "uuid_parsing": "Deve ser um identificador (UUID) válido.",
    "uuid_type": "Deve ser um identificador (UUID) válido.",
    "date_parsing": "Deve ser uma data válida no formato AAAA-MM-DD.",
    "date_from_datetime_parsing": "Deve ser uma data válida no formato AAAA-MM-DD.",
    "date_type": "Deve ser uma data válida no formato AAAA-MM-DD.",
    "string_type": "Deve ser um texto.",
    "json_invalid": "O corpo da requisição não é um JSON válido.",
    "model_attributes_type": "O corpo da requisição deve ser um objeto JSON.",
}


def _mensagem(erro: dict) -> str:
    # Erros lançados pelos nossos validadores (raise ValueError("...")) chegam como "value_error";
    # a mensagem original fica em ctx["error"].
    if erro["type"] == "value_error" and "error" in erro.get("ctx", {}):
        return str(erro["ctx"]["error"])
    return _MENSAGENS_PADRAO.get(erro["type"], erro["msg"])


def _nome_do_campo(loc: tuple) -> str:
    # loc é algo como ("body", "apoliceId") ou ("path", "id"). Quando o campo nem veio no JSON,
    # o Pydantic usa o nome Python ("apolice_id"); to_camel deixa sempre como no contrato JSON.
    partes = [to_camel(str(p)) for p in loc if p not in ("body", "path", "query")]
    return ".".join(partes) or "body"


def adicionar_problem_details(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def tratar_validacao(request: Request, exc: RequestValidationError):
        erros: dict[str, list[str]] = {}
        for erro in exc.errors():
            erros.setdefault(_nome_do_campo(erro["loc"]), []).append(_mensagem(erro))

        return resposta_problema(
            request,
            status=400,
            tipo=BASE_TIPOS + CODIGO_VALIDACAO,
            titulo="Um ou mais campos são inválidos",
            detalhe="Corrija os campos listados em 'errors' e envie a requisição novamente.",
            extensoes={"code": CODIGO_VALIDACAO, "errors": erros},
        )

    @app.exception_handler(StarletteHTTPException)
    async def tratar_http(request: Request, exc: StarletteHTTPException):
        # "about:blank" é o type padrão da RFC 9457 quando o title é só a frase do status.
        return resposta_problema(
            request,
            status=exc.status_code,
            tipo="about:blank",
            titulo=HTTPStatus(exc.status_code).phrase,
        )

    @app.middleware("http")
    async def tratar_erro_inesperado(request: Request, call_next):
        """Último recurso (o GlobalExceptionHandler): a exceção completa vai para o log; o
        cliente recebe um 500 genérico com o traceId. Mensagem e stack trace nunca são expostos."""
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
            return resposta_problema(
                request,
                status=500,
                tipo=BASE_TIPOS + CODIGO_ERRO_INTERNO,
                titulo="Erro interno",
                detalhe="Erro inesperado. Informe o traceId ao suporte.",
                extensoes={"code": CODIGO_ERRO_INTERNO},
            )
