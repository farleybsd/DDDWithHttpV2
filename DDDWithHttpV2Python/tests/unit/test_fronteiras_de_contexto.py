"""Os dois contextos vivem no mesmo pacote, então nada impede que um importe o outro. Este teste
faz esse papel: nenhum arquivo de um contexto pode importar módulos do outro. A única forma de
Sinistros saber algo de Apólices é pelo contrato HTTP.

No C# o teste usava reflexão (só olhava assinaturas). Aqui usamos o módulo ``ast`` para ler o
código-fonte e achar TODOS os imports — inclusive os de dentro de funções.
"""

import ast
from pathlib import Path

import pytest

PASTA_DOMAIN = Path(__file__).resolve().parents[2] / "src" / "seguros" / "domain"


def imports_do_arquivo(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            modulos.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            modulos.add(no.module)
    return modulos


@pytest.mark.parametrize(
    ("origem", "proibido"),
    [("sinistros", "seguros.domain.apolices"), ("apolices", "seguros.domain.sinistros")],
)
def test_contexto_nao_importa_o_outro_contexto(origem, proibido):
    violacoes = [
        f"{arquivo.relative_to(PASTA_DOMAIN)} -> {modulo}"
        for arquivo in (PASTA_DOMAIN / origem).rglob("*.py")  # rglob = busca recursiva
        for modulo in imports_do_arquivo(arquivo)
        if modulo == proibido or modulo.startswith(proibido + ".")
    ]

    assert not violacoes, "Referências entre contextos:\n" + "\n".join(violacoes)


def test_a_verificacao_realmente_encontra_arquivos():
    # Protege contra o teste acima passar "de graça" por causa de um caminho errado.
    assert list((PASTA_DOMAIN / "sinistros").rglob("*.py"))
