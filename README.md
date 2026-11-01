# 🏅 OlympicScope

Pipeline de Engenharia de Dados sobre 120 anos de história olímpica (1896–2016): do arquivo de origem até os indicadores, em camadas **raw → refined → marts**, com Python, DuckDB, SQL e testes.

Projeto do desafio final da Trilha de Engenharia de Dados JR.

## Fonte dos dados

| | |
|---|---|
| **Dataset** | [120 years of Olympic history: athletes and results](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results) |
| **Autora** | Randi H. Griffin, com dados coletados do Sports Reference em 2018 |
| **Cobertura** | Jogos de Verão e de Inverno, de Atenas 1896 a Rio 2016 |
| **Licença** | CC0 1.0 — domínio público |

Os arquivos da pasta `raw/` foram baixados do Kaggle pelo link acima e estão versionados neste repositório **sem nenhuma alteração**. A licença CC0 permite a redistribuição, e assim o projeto roda sem precisar de conta no Kaggle.

### O que é uma linha de cada arquivo

| Arquivo | Uma linha é... |
|---|---|
| `raw/athlete_events.csv` | um atleta em uma prova em uma edição dos Jogos |
| `raw/noc_regions.csv` | um código de Comitê Olímpico Nacional (NOC) e a região/país dele |

Os dois arquivos se ligam pela coluna `NOC`.

## Camadas

| Camada | O que tem | Status |
|---|---|---|
| **raw** | cópia fiel dos arquivos de origem, tudo como texto (`raw.athlete_events`: 271.116 linhas; `raw.noc_regions`: 230 linhas) | feito |
| **refined** | dados tipados, limpos e modelados (dimensões e fato) | a fazer |
| **marts** | indicadores, cada um gerado por um arquivo em `sql/marts/` | a fazer |

## Indicadores

_Serão listados aqui, cada um com o caminho do `.sql` de onde saiu._

## Como rodar do zero

Pré-requisito: [uv](https://docs.astral.sh/uv/) instalado.

```bash
git clone https://github.com/Surmani/OlympicScope.git
cd OlympicScope
uv sync
uv run python -m pipeline.ingestao   # raw/ → schema raw do DuckDB
uv run pytest
```

A ingestão cria o banco em `data/olympics.duckdb` e imprime a contagem de cada tabela lida do banco. Pode ser rodada quantas vezes quiser: a saída é sempre a mesma.

```
raw.athlete_events: 271.116 linhas
raw.noc_regions: 230 linhas
Total: 271.346 linhas
```

_Os comandos das próximas camadas serão adicionados a cada etapa._

## Conferência da camada raw

As contagens do banco foram comparadas com uma leitura independente dos arquivos, feita com o módulo `csv` da biblioteca padrão do Python (não com o pandas usado na ingestão). O `csv` respeita campos entre aspas, então conta registros, não linhas de texto.

| Arquivo | Linhas físicas (com cabeçalho) | Registros no CSV | Linhas no banco | Colunas (CSV = banco) | Bateu? |
|---|---|---|---|---|---|
| `athlete_events.csv` | 271.117 | 271.116 | 271.116 | 15 = 15, mesmos nomes e ordem | sim |
| `noc_regions.csv` | 231 | 230 | 230 | 3 = 3, mesmos nomes e ordem | sim |

Todos os registros têm o mesmo número de campos do cabeçalho (15 e 3). No banco, todas as colunas da raw são VARCHAR, e o texto `NA` foi preservado como texto: em `Medal`, por exemplo, são 231.333 linhas com `'NA'` e nenhuma nula.

## Decisões sobre o dado

| Etapa | Decisão | Motivo |
|---|---|---|
| Estrutura | Arquivos originais versionados em `raw/` | Licença CC0 permite; quem clona chega aos mesmos números sem depender do Kaggle |
| Estrutura | Banco DuckDB fora do git | É gerado do zero pelo pipeline; versionar criaria um arquivo binário que muda a cada execução |
| Raw | Todas as colunas lidas como texto (VARCHAR) | Conversão de tipo é decisão; fica registrada na refined |
| Raw | Texto `NA` mantido como texto, não convertido em nulo | No dataset a ausência vem escrita como `NA`; converter na leitura seria uma limpeza escondida na raw |
| Raw | Faltando um arquivo de origem, nada é ingerido | Ingerir uma tabela de duas em silêncio gera indicadores errados que parecem certos |

## Documentação

- [`docs/SPEC.md`](docs/SPEC.md): especificação completa do projeto (arquitetura, modelo de dados, regras de contagem e fluxo de desenvolvimento).

## Onde a IA errou (e como descobri)

_Preenchido ao longo do projeto, no momento em que acontece._

| Etapa | O que a IA fez ou assumiu | Como descobri |
|---|---|---|
| 1.1 — `pipeline/db.py` | Leu a contagem de `gravar` com `fetchone()`, que no DuckDB 2.x deixa o resultado aberto e trava o próximo uso da mesma conexão | O teste "gravar duas vezes substitui sem duplicar" falhou com `ResourceInUseException`; corrigido para `fetchall()` |
