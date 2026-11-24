"""Tradução de erros para respostas RFC 9457 ``application/problem+json`` (equivale ao ErroParaHttp.cs).

É o único lugar que conhece a política de status HTTP.
"""

import uuid
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from seguros.common.erro import Erro
from seguros.common.tipo_erro import TipoErro

BASE_TIPOS = "https://seguros.example/problemas/"
"""Prefixo do membro ``type``. O ``type`` completo é este prefixo + o código do erro."""

CODIGO_ERRO_INTERNO = "erro-interno"
CODIGO_VALIDACAO = "validacao"
MEDIA_TYPE_PROBLEMA = "application/problem+json"

# Um dicionário faz o papel do "switch expression" do C#.
_STATUS_POR_TIPO: dict[TipoErro, int] = {
    TipoErro.VALIDACAO: 400,
    TipoErro.NAO_ENCONTRADO: 404,
    TipoErro.CONFLITO: 409,
    TipoErro.REGRA_DE_NEGOCIO: 422,
    TipoErro.INDISPONIVEL: 503,
}


def para_status_code(tipo: TipoErro) -> int:
    return _STATUS_POR_TIPO.get(tipo, 500)


def obter_trace_id(request: Request) -> str:
    """Id que liga a resposta de erro ao log. Gerado uma vez por requisição e guardado nela."""
    if not hasattr(request.state, "trace_id"):
        request.state.trace_id = uuid.uuid4().hex
    return request.state.trace_id


def resposta_problema(
    request: Request,
    *,  # o "*" obriga os parâmetros seguintes a serem passados por nome
    status: int,
    tipo: str,
    titulo: str,
    detalhe: str | None = None,
    extensoes: dict[str, Any] | None = None,
) -> JSONResponse:
    corpo: dict[str, Any] = {
        "type": tipo,
        "title": titulo,
        "status": status,
        "detail": detalhe,
        "instance": request.url.path,
    }
    corpo.update(extensoes or {})
    corpo.setdefault("traceId", obter_trace_id(request))

    # jsonable_encoder converte UUID, date, Decimal... em tipos que o JSON entende.
    return JSONResponse(
        status_code=status,
        content=jsonable_encoder({k: v for k, v in corpo.items() if v is not None}),
        media_type=MEDIA_TYPE_PROBLEMA,
    )


def para_problema(erro: Erro, request: Request) -> JSONResponse:
    """Monta o ProblemDetails de um erro esperado (o ``erro.ParaProblema()`` do C#)."""
    extensoes: dict[str, Any] = {"code": erro.codigo, **(erro.metadados or {})}
    return resposta_problema(
        request,
        status=para_status_code(erro.tipo),
        tipo=BASE_TIPOS + erro.codigo,
        titulo=erro.titulo,
        detalhe=erro.detalhe,
        extensoes=extensoes,
    )
