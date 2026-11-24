# Seguros V2 em Python: DDD em uma única API, contextos conversando por HTTP

Esta é a reescrita em **Python** do projeto [`DDDWithHttpV2`](../DDDWithHttpV2) (C# / .NET). O
objetivo é **aprender Python** refazendo um projeto que você já conhece. As regras de negócio, as
rotas, os contratos JSON e os códigos de erro são os mesmos da versão C#.

Este documento tem três partes:

1. **Preparar o ambiente** (Python, ambiente virtual e pacotes)
2. **Mapa C# → Python** (o que equivale a quê)
3. **Passo a passo**: a ordem em que você deve refazer os arquivos, o que aprender em cada um e
   como conferir que funcionou antes de seguir

> Dica: a pasta já tem a versão pronta. Para aprender de verdade, crie uma pasta vazia (por
> exemplo `SegurosPythonEstudo/`) e refaça os arquivos nela, seguindo a ordem abaixo. Consulte a
> versão pronta quando travar e compare com o arquivo `.cs` original.

---

## 1. Preparar o ambiente

### 1.1 Pré-requisitos

| Ferramenta | Para quê | Como conferir |
|---|---|---|
| **Python 3.12 ou mais novo** | a linguagem (o projeto usa `class Result[T]` e `type X = ...`, que só existem a partir do 3.12) | `python --version` |
| **VS Code** + extensão **Python** (Microsoft) | editor, autocomplete, depuração | — |
| Extensão **REST Client** (opcional) | executar o `http/seguros.http` | — |

### 1.2 Criar o ambiente virtual (venv)

O **ambiente virtual** é uma pasta (`.venv/`) com um Python e pacotes só deste projeto. Faz o
papel do `packages`/NuGet por projeto do .NET: o que você instala aqui não afeta o resto da
máquina.

No **PowerShell**, dentro da pasta `DDDWithHttpV2Python`:

```powershell
python -m venv .venv                 # cria o ambiente virtual (só uma vez)
.\.venv\Scripts\Activate.ps1         # ativa (toda vez que abrir um terminal novo)
```

Com o ambiente ativo, o prompt mostra `(.venv)`. Se o PowerShell bloquear o script de ativação,
rode uma vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

No VS Code: `Ctrl+Shift+P` → **Python: Select Interpreter** → escolha o `.venv`.

### 1.3 Instalar os pacotes

```powershell
python -m pip install --upgrade pip
pip install -r requirements-dev.txt      # pacotes da aplicação + pacotes de teste
```

| Pacote | Equivale no .NET a | Para que serve aqui |
|---|---|---|
| `fastapi` | ASP.NET Core + FastEndpoints | rotas, injeção de dependência (`Depends`), validação do corpo e Swagger automático |
| `uvicorn[standard]` | Kestrel | o servidor web que executa a aplicação |
| `pydantic` | records + System.Text.Json + FluentValidation | modelos dos contratos JSON e validação dos campos |
| `pydantic-settings` | `appsettings.{Ambiente}.json` + `IOptions<T>` | configuração tipada lida de `config/*.env` e de variáveis de ambiente |
| `httpx` | `HttpClient` | o cliente HTTP assíncrono que faz Sinistros → Apólices |
| `pytest` *(dev)* | xUnit | framework de testes |
| `pytest-asyncio` *(dev)* | (o xUnit já aceita `async Task`) | permite escrever testes `async def` |

**Não tem Polly**: a resiliência (retry, circuit breaker, timeout, limite de concorrência) foi
escrita à mão em `common/http/resiliencia.py`, porque é ótima para aprender `async`/`await`,
classes e exceções. Em projeto real, existem pacotes como `tenacity` (retry) e `aiobreaker`
(circuit breaker).

Para conferir: `pip list` deve mostrar os pacotes acima.

### 1.4 Rodar e testar

```powershell
# testes (equivale ao dotnet test)
python -m pytest              # todos
python -m pytest -v           # mostrando o nome de cada teste
python -m pytest tests/unit   # só os unitários

# aplicação (equivale ao dotnet run) — http://localhost:5200/swagger
uvicorn seguros.main:criar_app --factory --app-dir src --port 5200
# use --reload para reiniciar sozinho quando salvar um arquivo
```

* `--app-dir src`: o pacote `seguros` está dentro de `src/`
* `--factory`: `criar_app` é uma função que **cria** a aplicação (ver `main.py`)

Para os acentos aparecerem certos nos logs do Windows, rode antes `$env:PYTHONUTF8 = "1"`.

---

## 2. Mapa C# → Python

### 2.1 Arquivos

| C# (`DDDWithHttpV2/src/Seguros`) | Python (`src/seguros`) |
|---|---|
| `Seguros.csproj` | `requirements.txt`, `requirements-dev.txt`, `pyproject.toml` |
| `appsettings.json` / `appsettings.Development.json` / ... | `config/base.env` / `config/development.env` / ... |
| `Program.cs` | `main.py` |
| `Bootstrap/ServiceExtensions.cs` (`AddSettings`) | `common/settings.py` (`carregar_settings`) |
| `Common/Result.cs`, `Erro.cs`, `TipoErro.cs` | `common/result.py`, `erro.py`, `tipo_erro.py` |
| `Common/Erros/ErroParaHttp.cs` | `common/erros/erro_para_http.py` |
| `Common/Erros/GlobalExceptionHandler.cs` + `ProblemDetails*Extensions.cs` | `common/erros/problem_details.py` |
| `Common/Settings/*.cs` | `common/settings.py` |
| `Common/Http/ContextHttpClientExtensions.cs` | `common/http/context_http_client.py` |
| Polly (pacote) | `common/http/resiliencia.py` |
| *(System.Text.Json camelCase)* | `common/modelo_api.py` |
| `IApoliceRepository.cs` | `apolice_repository.py` (classe `ApoliceRepository`, um `Protocol`) |
| `IApolicesApiClient.cs` | `apolices_api_client.py` (`ApolicesApiClient`, a porta) |
| `ApolicesApi/ApolicesApiClient.cs` | `apolices_api/apolices_api_http_client.py` (`ApolicesApiHttpClient`, o adaptador) |
| `Features/X/Endpoint.cs` + `Summary.cs` | `features/x/endpoint.py` (a documentação vai no decorator) |
| `Features/X/Handler.cs` | `features/x/handler.py` |
| `Features/RegistrarSinistro/Request.cs` + `Validator.cs` | `features/registrar_sinistro/request.py` |
| `Infrastructure/XModule.cs` (`AddXModule()`) | `infrastructure/x_module.py` (`adicionar_modulo_x(app)`) |
| *(o contêiner de DI resolve os tipos)* | `infrastructure/dependencias.py` (funções para o `Depends`) |
| `tests/Seguros.UnitTests` | `tests/unit` |
| `tests/Seguros.IntegrationTests` | `tests/integration` |
| `SegurosApiFactory` + `ScriptedHttpMessageHandler` + `ProblemaAssert` | `tests/integration/apoio.py` |

### 2.2 Conceitos da linguagem

| C# | Python | Onde ver no projeto |
|---|---|---|
| `namespace Seguros.Common;` | a pasta é o pacote; `__init__.py` marca a pasta como pacote | qualquer pasta em `src/seguros` |
| `using X;` | `from seguros.x import Y` | topo de todo arquivo |
| `PascalCase` para métodos e propriedades | `snake_case` para funções, métodos e atributos; `PascalCase` só para classes | todo lugar |
| `sealed record Segurado(string Nome, ...)` | `@dataclass(frozen=True, slots=True)` | `segurado.py` |
| `enum TipoCobertura` | `class TipoCobertura(StrEnum)` | `tipo_cobertura.py` |
| `interface IApoliceRepository` | `class ApoliceRepository(Protocol)` | `apolice_repository.py` |
| `Result<T>` | `class Result[T]` (genéricos do 3.12) | `result.py` |
| `public static Erro X(...)` | `@staticmethod` | `erros_de_apolice.py` |
| `public static readonly Erro X` | `X: ClassVar[Erro] = ...` | `erros_de_apolice.py` |
| `static Result<Apolice> Criar(...)` | `@classmethod def criar(cls, ...)` | `apolice.py` |
| `public Guid Id { get; }` | `@property def id(self)` | `apolice.py` |
| construtor privado | não existe; é convenção (`_atributo`, "crie pelo `criar()`") | `apolice.py` |
| `Guid` / `DateOnly` / `DateTime` / `decimal` | `UUID` / `date` / `datetime` / `Decimal` | domínio |
| `x is null` | `x is None` | handlers |
| `string.IsNullOrWhiteSpace(s)` | `not s or not s.strip()` | `apolice.py` |
| `$"Id '{id}'"` | `f"Id '{id}'"` (f-string) | catálogos de erro |
| LINQ `.Select(...).ToList()` | list comprehension `[f(x) for x in xs]` | `handler.py` |
| LINQ `.Any(c => ...)` | `any(... for c in xs)` | `apolice.py` |
| LINQ `.Where().OrderByDescending()` | `sorted((... if ...), key=..., reverse=True)` | `in_memory_sinistro_repository.py` |
| `yield return` | `yield` | `in_memory_apolice_repository.py` |
| `switch` com tipos / record patterns | `match` / `case Encontrada(apolice):` | `registrar_sinistro/handler.py` |
| `abstract record` com 3 subtipos | 3 dataclasses + `type X = A \| B \| C` | `apolice_consulta_resultado.py` |
| `async Task<T>` / `await` | `async def ... -> T` / `await` | todo lugar |
| `Task.Delay` / `TaskCompletionSource` | `asyncio.sleep` / `asyncio.Event` | `resiliencia.py`, testes |
| `try { } catch (X) { }` | `try: ... except X:` | `apolices_api_http_client.py` |
| `throw new ArgumentException(...)` | `raise ValueError(...)` | `periodo_vigencia.py` |
| `ILogger<T>` | `logger = logging.getLogger(__name__)` | handlers |
| `[Fact]` / `[Theory] [InlineData]` | `def test_...()` / `@pytest.mark.parametrize` | `tests/` |
| `Assert.Equal(a, b)` | `assert a == b` | `tests/` |
| `Assert.Throws<X>(...)` | `with pytest.raises(X):` | `test_periodo_vigencia.py` |

---

## 3. Passo a passo para refazer os arquivos

Cada fase termina com um **checkpoint**: um comando que mostra se o que você fez funciona. Só
siga para a próxima fase com o checkpoint passando.

Lembrete: **toda pasta dentro de `src/seguros` e de `tests` precisa de um `__init__.py`** (pode
ficar vazio). Ele diz ao Python que a pasta é um pacote importável. Crie-o sempre que criar uma
pasta nova.

### Fase 0: esqueleto do projeto

| # | Arquivo | O que aprender |
|---|---|---|
| 0.1 | `requirements.txt`, `requirements-dev.txt` | como listar dependências (o `<PackageReference>`) |
| 0.2 | `pyproject.toml` | configuração do projeto e do pytest (`pythonpath`, `asyncio_mode`) |
| 0.3 | `.gitignore` | ignorar `.venv/` e `__pycache__/` |
| 0.4 | `src/seguros/__init__.py` (vazio) | o que é um pacote |

**Checkpoint:** crie e ative o venv, instale os pacotes (seção 1) e rode `pip list`.

### Fase 1: base comum (`src/seguros/common`)

Nada de web ainda, só Python puro.

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 1.1 | `common/tipo_erro.py` | `TipoErro.cs` | `Enum`, `auto()` |
| 1.2 | `common/erro.py` | `Erro.cs` | `@dataclass(frozen=True)`, anotações de tipo, `X \| None`, valor padrão |
| 1.3 | `common/result.py` | `Result.cs` | genéricos `class Result[T]`, `@property`, `@classmethod` |

**Checkpoint:**
```powershell
python -c "import sys; sys.path.insert(0,'src'); from seguros.common.result import Result; print(Result.success(42).value)"
```
Deve imprimir `42`.

### Fase 2: domínio de Apólices (`domain/apolices/aggregates/apolices`)

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 2.1 | `tipo_cobertura.py` | `TipoCobertura.cs` | `StrEnum` (o membro é a própria string) |
| 2.2 | `segurado.py` | `Segurado.cs` | value object com dataclass |
| 2.3 | `cobertura.py` | `Cobertura.cs` | `Decimal` para dinheiro |
| 2.4 | `periodo_vigencia.py` | `PeriodoVigencia.cs` | `__post_init__` para validar, comparação encadeada `a <= x <= b` |
| 2.5 | `tests/unit/test_periodo_vigencia.py` | `PeriodoVigenciaTests.cs` | seu primeiro teste pytest, `parametrize`, `pytest.raises` |
| 2.6 | `erros_de_apolice.py` | `ErrosDeApolice.cs` | `@staticmethod`, `ClassVar`, f-strings |
| 2.7 | `apolice.py` | `Apolice.cs` | classe com `__init__`, `_privado`, `@property`, `@classmethod` como fábrica, `any(...)` |
| 2.8 | `tests/unit/test_apolice.py` | `ApoliceTests.cs` | funções auxiliares em teste |
| 2.9 | `apolice_repository.py` | `IApoliceRepository.cs` | `Protocol` (interface estrutural), `async def` |

**Checkpoint:** `python -m pytest tests/unit -v` (testes de PeriodoVigencia e Apolice passando).

### Fase 3: domínio de Sinistros (`domain/sinistros/aggregates/sinistros`)

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 3.1 | `tipo_cobertura.py` | `TipoCobertura.cs` | o mesmo enum **de novo, de propósito** (cada contexto com seu vocabulário); `@classmethod de_texto` e `Self` |
| 3.2 | `status_sinistro.py` | `StatusSinistro.cs` | — |
| 3.3 | `apolice_referenciada.py` | `ApoliceReferenciada.cs` | dataclass com métodos, `in` em tupla |
| 3.4 | `apolice_consulta_resultado.py` | `ApoliceConsultaResultado.cs` | união de tipos `type X = A \| B \| C` |
| 3.5 | `erros_de_sinistro.py` | `ErrosDeSinistro.cs` | formatação de data em f-string `{data:%Y-%m-%d}` |
| 3.6 | `sinistro.py` | `Sinistro.cs` | `uuid.uuid4()`, `datetime.now(UTC)` |
| 3.7 | `tests/unit/test_sinistro.py` | `SinistroTests.cs` | `*args` (o `params` do C#) |
| 3.8 | `sinistro_repository.py` | `ISinistroRepository.cs` | `Protocol` |
| 3.9 | `apolices_api_client.py` | `IApolicesApiClient.cs` | a **porta**: o domínio diz o que precisa, sem saber de HTTP |
| 3.10 | `tests/unit/test_fronteiras_de_contexto.py` | `FronteirasDeContextoTests.cs` | `ast` (ler o código-fonte), `pathlib`, `rglob` |

**Checkpoint:** `python -m pytest tests/unit -v` (todos os unitários passando, incluindo a fronteira).

### Fase 4: configuração e contratos JSON (`common`)

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 4.1 | `config/base.env`, `development.env`, `qas.env`, `production.env` | `appsettings*.json` | o `__` separa níveis (`HTTP_RESILIENCE__RETRY__MAX_RETRY_ATTEMPTS`) |
| 4.2 | `common/settings.py` | `ServicesSettings.cs`, `HttpResilienceSettings.cs`, `AddSettings` | `BaseModel`, `BaseSettings`, `Field(...)`, `@field_validator`, `default_factory`, `pathlib.Path` |
| 4.3 | `common/modelo_api.py` | (opção do System.Text.Json) | `model_config`, alias camelCase |

**Checkpoint:**
```powershell
python -c "import sys; sys.path.insert(0,'src'); from seguros.common.settings import carregar_settings; print(carregar_settings())"
```
Depois teste a validação, que deve dar erro de URL inválida:
```powershell
$env:SERVICES_SETTINGS__APOLICES_URI = "xpto"; python -c "import sys; sys.path.insert(0,'src'); from seguros.common.settings import carregar_settings; carregar_settings()"
Remove-Item Env:SERVICES_SETTINGS__APOLICES_URI
```

### Fase 5: erros HTTP no padrão RFC 9457 (`common/erros`)

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 5.1 | `common/erros/erro_para_http.py` | `ErroParaHttp.cs` | dicionário no lugar do `switch`, `JSONResponse`, parâmetros só-por-nome (`*`) |
| 5.2 | `common/erros/problem_details.py` | `GlobalExceptionHandler.cs` + `ProblemDetails*Extensions.cs` | `@app.exception_handler`, `@app.middleware`, funções dentro de funções |

*(o checkpoint desta fase é o da fase 6)*

### Fase 6: contexto de Apólices na web, primeira versão rodando

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 6.1 | `domain/apolices/contracts/apolice_response.py` | `ApoliceResponse.cs` | modelos Pydantic aninhados |
| 6.2 | `domain/apolices/infrastructure/in_memory_apolice_repository.py` | `InMemoryApoliceRepository.cs` | função geradora (`yield`), dict comprehension, `sorted(key=...)` |
| 6.3 | `domain/apolices/infrastructure/dependencias.py` | (contêiner de DI) | `request.app.state` como lugar dos singletons |
| 6.4 | `domain/apolices/features/consultar_apolice/handler.py` | `ConsultarApolice/Handler.cs` | list comprehension no `mapear` |
| 6.5 | `domain/apolices/features/consultar_apolice/endpoint.py` | `Endpoint.cs` + `Summary.cs` | `APIRouter`, decorators `@router.get`, `Depends`, `Annotated`, `Path` |
| 6.6 | `domain/apolices/features/listar_apolices/handler.py` e `endpoint.py` | `ListarApolices/*` | reaproveitar `mapear` |
| 6.7 | `domain/apolices/infrastructure/apolices_module.py` | `ApolicesModule.cs` | `include_router` |
| 6.8 | `main.py` (**versão inicial**) | `Program.cs` | `FastAPI(...)`, fábrica `criar_app`, `lifespan` |

Na versão inicial do `main.py`, deixe a linha `adicionar_modulo_sinistros(...)` de fora (ou
comentada), porque o contexto de Sinistros ainda não existe.

**Checkpoint:** suba a aplicação (`uvicorn seguros.main:criar_app --factory --app-dir src --port 5200 --reload`)
e abra:
* http://localhost:5200/swagger (o Swagger com a tag *Apolices*)
* http://localhost:5200/apolices (lista as 3 apólices)
* http://localhost:5200/apolices/99999999-9999-9999-9999-999999999999 (404 em `application/problem+json`)
* http://localhost:5200/rota-que-nao-existe (404 também em problem+json)

### Fase 7: comunicação HTTP com resiliência (`common/http`)

É a parte mais rica para aprender `async`.

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 7.1 | `common/http/resiliencia.py` | Polly + pipeline do `AddResilienceHandler` | exceções próprias, `asyncio.Semaphore`, `@asynccontextmanager`, `deque`, `asyncio.wait_for` (timeout), `while True` com retry, herdar de `httpx.AsyncBaseTransport` (o `DelegatingHandler`) |
| 7.2 | `common/http/context_http_client.py` | `ContextHttpClientExtensions.cs` | `httpx.AsyncClient(base_url=..., transport=...)` |

Leia com calma a ordem do pipeline: **limite de concorrência → retry → circuit breaker →
timeout → rede**. É a mesma do projeto C#.

### Fase 8: contexto de Sinistros na web

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 8.1 | `domain/sinistros/contracts/sinistro_response.py`, `apolice_do_sinistro_response.py` | `Contracts/*.cs` | — |
| 8.2 | `domain/sinistros/infrastructure/apolices_api/apolice_api_dto.py` | `ApoliceApiDto.cs` | cópia do contrato, **sem importar nada de Apólices** |
| 8.3 | `domain/sinistros/infrastructure/apolices_api/apolices_api_http_client.py` | `ApolicesApiClient.cs` | o **adaptador** (camada anticorrupção): `try/except` com várias exceções, `model_validate_json`, tradução DTO → domínio |
| 8.4 | `domain/sinistros/infrastructure/in_memory_sinistro_repository.py` | `InMemorySinistroRepository.cs` | generator expression + `sorted(reverse=True)` |
| 8.5 | `domain/sinistros/infrastructure/dependencias.py` | (DI) | — |
| 8.6 | `domain/sinistros/features/registrar_sinistro/request.py` | `Request.cs` + `Validator.cs` | `@field_validator`, `validate_default=True`, `raise ValueError` vira erro 400 |
| 8.7 | `domain/sinistros/features/registrar_sinistro/handler.py` | `Handler.cs` | **`match`/`case`** e `assert_never` |
| 8.8 | `domain/sinistros/features/registrar_sinistro/endpoint.py` | `Endpoint.cs` + `Summary.cs` | `status_code=201`, corpo JSON pelo tipo do parâmetro |
| 8.9 | `features/consultar_sinistro/handler.py` e `endpoint.py` | `ConsultarSinistro/*` | — |
| 8.10 | `features/listar_sinistros_por_apolice/handler.py` e `endpoint.py` | `ListarSinistrosPorApolice/*` | — |
| 8.11 | `features/consultar_apolice_do_sinistro/handler.py` e `endpoint.py` | `ConsultarApoliceDoSinistro/*` | — |
| 8.12 | `domain/sinistros/infrastructure/sinistros_module.py` | `SinistrosModule.cs` | montar o cliente HTTP do contexto |
| 8.13 | `main.py` (**versão final**) | `Program.cs` | acrescentar `adicionar_modulo_sinistros(...)` e o parâmetro `transporte_apolices` |

**Checkpoint:** com a aplicação no ar, execute as requisições de `http/seguros.http` (REST
Client) ou use o Swagger. No `POST /sinistros` o console mostra a chamada entre contextos:

```
INFO: httpx - HTTP Request: GET http://localhost:5200/apolices/11111111-1111-1111-1111-111111111111 "HTTP/1.1 200 OK"
```

Rode também `python -m pytest tests/unit` de novo: o teste de fronteira tem que continuar
passando.

### Fase 9: testes de integração (`tests/integration`)

| # | Arquivo | Origem C# | O que aprender |
|---|---|---|---|
| 9.1 | `tests/integration/apoio.py` | `SegurosApiFactory.cs`, `ScriptedHttpMessageHandler.cs`, `ProblemaAssert.cs` | `httpx.ASGITransport` (a aplicação em memória, sem porta), `httpx.MockTransport` (Apólices simulado), objeto chamável (`__call__`), `@asynccontextmanager` |
| 9.2 | `test_comunicacao_entre_contextos.py` | `ComunicacaoEntreContextosTests.cs` | Sinistros chamando o Apólices real em memória |
| 9.3 | `test_registrar_sinistro.py` | `RegistrarSinistroEndpointTests.cs` + `ApolicesUriTests.cs` | `nonlocal`, retry, circuito, timeout, montagem da URL |
| 9.4 | `test_protecao_contra_sobrecarga.py` | `ProtecaoContraSobrecargaTests.cs` | `asyncio.create_task`, `asyncio.Event`, concorrência de verdade |
| 9.5 | `test_problem_details.py` | `ProblemDetailsTests.cs` | trocar uma dependência no teste (`app.state`), `monkeypatch` |

**Checkpoint final:** `python -m pytest -v`, com **45 testes passando**.

### Fase 10: brincar com a resiliência

```powershell
$env:SERVICES_SETTINGS__APOLICES_URI = "http://localhost:5999"   # porta sem ninguém ouvindo
uvicorn seguros.main:criar_app --factory --app-dir src --port 5200
```

Envie o último `POST` do `http/seguros.http` três vezes seguidas. No console aparecem
`Retentativa 1/1`, depois `Circuito ABERTO por 15.0s`, e a terceira resposta volta `503` na hora,
sem nem tentar a rede. Para voltar ao normal: `Remove-Item Env:SERVICES_SETTINGS__APOLICES_URI`.

---

## 4. Estrutura final

```
DDDWithHttpV2Python/
  LEIA-ME.md                       este arquivo
  requirements.txt / requirements-dev.txt / pyproject.toml
  config/                          base.env + um .env por ambiente (o appsettings)
  http/seguros.http                requisições prontas (REST Client)
  src/seguros/
    main.py                        criar_app(): registra os módulos de cada contexto
    common/                        o que é transversal
      tipo_erro.py, erro.py, result.py, modelo_api.py, settings.py
      erros/                       RFC 9457: erro_para_http.py, problem_details.py
      http/                        resiliencia.py (o "Polly"), context_http_client.py
    domain/
      apolices/                    contexto de Apólices (não conhece nenhum outro)
        aggregates/apolices/       Apolice, Segurado, PeriodoVigencia, Cobertura, TipoCobertura,
                                   ErrosDeApolice, ApoliceRepository
        contracts/                 ApoliceResponse (contrato HTTP público)
        features/                  consultar_apolice/, listar_apolices/
        infrastructure/            apolices_module.py, dependencias.py, repositório em memória
      sinistros/                   contexto de Sinistros (conhece Apólices só por HTTP)
        aggregates/sinistros/      Sinistro, StatusSinistro, TipoCobertura (próprio),
                                   ApoliceReferenciada, ApoliceConsultaResultado,
                                   ErrosDeSinistro, SinistroRepository, ApolicesApiClient (porta)
        contracts/                 SinistroResponse, ApoliceDoSinistroResponse
        features/                  registrar_sinistro/, consultar_sinistro/,
                                   listar_sinistros_por_apolice/, consultar_apolice_do_sinistro/
        infrastructure/            sinistros_module.py, dependencias.py, repositório em memória,
                                   apolices_api/ (adaptador HTTP + DTO)
  tests/
    unit/                          domínio + fronteira entre contextos
    integration/                   a aplicação inteira em memória
```

## 5. Rotas, dados e erros

Iguais aos da versão C#:

| Método e rota | Contexto |
|---|---|
| `GET /apolices` | Apólices |
| `GET /apolices/{id}` | Apólices |
| `POST /sinistros` | Sinistros (chama `GET /apolices/{id}` por HTTP) |
| `GET /sinistros/{id}` | Sinistros |
| `GET /apolices/{apoliceId}/sinistros` | Sinistros |
| `GET /sinistros/{id}/apolice` | Sinistros (chama `GET /apolices/{id}` por HTTP) |

| Id | Número | Vigência | Coberturas |
|---|---|---|---|
| `11111111-1111-1111-1111-111111111111` | AP-0001 | 2026-01-01 a 2026-12-31 | Colisão, Roubo, Incêndio |
| `22222222-2222-2222-2222-222222222222` | AP-0002 | 2024 (**expirada**) | Colisão |
| `33333333-3333-3333-3333-333333333333` | AP-0003 | 2026-06-01 a 2027-05-31 | Incêndio, Danos a Terceiros |

Códigos de erro (`code` e final do `type`): `validacao` (400), `apolice-nao-encontrada` (404),
`sinistro-nao-encontrado` (404), `apolice-fora-de-vigencia` (422), `cobertura-nao-contratada`
(422), `apolices-api-indisponivel` (503), `erro-interno` (500).

## 6. Diferenças em relação à versão C#

* **Configuração**: arquivos `.env` em `config/` no lugar dos `appsettings.*.json`. O ambiente vem
  de `AMBIENTE` (`development`, `qas`, `production`) no lugar de `ASPNETCORE_ENVIRONMENT`.
  Variáveis de ambiente usam snake_case maiúsculo: `SERVICES_SETTINGS__APOLICES_URI`.
* **Tempos em segundos** (`timeout_segundos = 2`) no lugar de `TimeSpan` (`"00:00:02"`).
* **Resiliência escrita à mão**, sem Polly. O retry usa espera exponencial sem *jitter*.
* **Injeção de dependência**: os singletons ficam em `app.state` e cada endpoint monta o seu
  handler com `Depends(...)`. Não existe contêiner que resolva tipos sozinho.
* **Erro de validação** (400): os nomes dos campos em `errors` saem em camelCase (`apoliceId`).
  Erros de tipo (UUID ou data inválidos) têm mensagens próprias em português.
* **Rota inexistente**: o 404 usa `type: "about:blank"` (o valor padrão da RFC 9457).
* **`limiteIndenizacao`** sai como número no JSON (`50000.0`). O domínio continua usando `Decimal`.
* **Teste de fronteira** mais forte: olha todos os `import` do código-fonte, não só as assinaturas.
* **Uma cobertura desconhecida** vinda de Apólices é ignorada pela tradução. No C# o
  `Enum.Parse` lançaria exceção.
* **Sem lock nos repositórios em memória**: o `asyncio` roda num único thread, então um `dict`
  comum basta (no C# era `ConcurrentDictionary`).

## 7. Exercícios para continuar aprendendo

1. Adicione *jitter* (aleatoriedade) à espera do retry em `resiliencia.py` (dica: `random.uniform`).
2. Escreva testes unitários só para o `DisjuntorDeCircuito`, passando um `relogio` falso para não
   precisar esperar o tempo passar.
3. Crie um terceiro contexto, **Pagamentos**, que consulta Sinistros por HTTP, seguindo a receita
   do README C# ("Como adicionar uma nova chamada entre contextos"). Estenda o
   `test_fronteiras_de_contexto.py` para cobrir o novo contexto.
4. Troque o repositório em memória de Sinistros por SQLite (módulo `sqlite3`, que já vem no
   Python) sem mudar nenhum handler: só uma nova classe com os mesmos métodos do `Protocol`.
5. Instale o `mypy` (`pip install mypy`) e rode `mypy src` para ver o type checker conferindo
   as anotações (por exemplo, o `assert_never` dos handlers).
