# 🏅 OlympicScope

Pipeline de Engenharia de Dados sobre 120 anos de história olímpica (1896–2016): do arquivo de origem até os indicadores, em camadas **raw → refined → marts → dashboard Streamlit**, com Python, DuckDB, SQL e testes.

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
| **refined** | dados tipados, limpos e modelados (dimensões e fato) | feito, com 12 verificações a cada execução: `refined.noc_regions` (231 linhas), `refined.games` (51), `refined.games_cities` (52), `refined.events` (765), `refined.athletes` (135.571), fato `refined.athlete_results` (269.731) |
| **marts** | indicadores, cada um gerado por um arquivo em `sql/marts/` | a fazer |
| **dashboard** | app Streamlit em `app/app.py`, lendo só do schema `marts` | a fazer |

## Indicadores

_Serão listados aqui, cada um com o caminho do `.sql` de onde saiu._

## Como rodar do zero

Pré-requisito: [uv](https://docs.astral.sh/uv/) instalado.

```bash
git clone https://github.com/Surmani/OlympicScope.git
cd OlympicScope
uv sync
uv run python -m pipeline.ingestao   # raw/ → schema raw do DuckDB
uv run python -m pipeline.refined    # schema raw → schema refined (SQL em sql/refined/)
uv run pytest
```

A ingestão cria o banco em `data/olympics.duckdb` e imprime a contagem de cada tabela lida do banco. Pode ser rodada quantas vezes quiser: a saída é sempre a mesma.

```
raw.athlete_events: 271.116 linhas
raw.noc_regions: 230 linhas
Total: 271.346 linhas
```

A refined executa, em ordem, os arquivos de `sql/refined/`, imprime a contagem de cada tabela criada e, no fim, roda as 12 verificações de [`sql/verificacoes/refined.sql`](sql/verificacoes/refined.sql) sobre os dados reais: chaves únicas e não nulas em cada dimensão, nenhuma chave da fato sem dimensão, nenhuma linha idêntica na fato e medalhas só com valores válidos. Se alguma falhar, a execução lista qual foi e termina com erro (código 1), em vez de seguir com dado inconsistente.

```
refined.noc_regions: 231 linhas
refined.games: 51 linhas
refined.games_cities: 52 linhas
refined.events: 765 linhas
refined.athletes: 135.571 linhas
refined.athlete_results: 269.731 linhas
verificações: 12 de 12 ok
```

_Os comandos das próximas camadas serão adicionados a cada etapa._

## Explorar o banco no navegador

```bash
uv run python ui.py
```

Abre o banco em http://localhost:4213 com a [DuckDB UI](https://duckdb.org/docs/stable/core_extensions/ui), **somente para leitura**: dá para consultar as tabelas, mas não alterar o banco. Na primeira vez, a extensão é baixada da internet. `Ctrl+C` encerra.

- Se o banco ainda não existir, o script avisa e sai: rode a ingestão antes.
- **Feche o `ui.py` (Ctrl+C) antes de rodar a ingestão.** Enquanto ele está aberto, o DuckDB não deixa outro processo gravar no arquivo, e a ingestão falha com `IO Error: Cannot open file ... já está sendo usado por outro processo`.

## Conferência da camada raw

As contagens do banco foram comparadas com uma leitura independente dos arquivos, feita com o módulo `csv` da biblioteca padrão do Python (não com o pandas usado na ingestão). O `csv` respeita campos entre aspas, então conta registros, não linhas de texto.

| Arquivo | Linhas físicas (com cabeçalho) | Registros no CSV | Linhas no banco | Colunas (CSV = banco) | Bateu? |
|---|---|---|---|---|---|
| `athlete_events.csv` | 271.117 | 271.116 | 271.116 | 15 = 15, mesmos nomes e ordem | sim |
| `noc_regions.csv` | 231 | 230 | 230 | 3 = 3, mesmos nomes e ordem | sim |

Todos os registros têm o mesmo número de campos do cabeçalho (15 e 3). No banco, todas as colunas da raw são VARCHAR, e o texto `NA` foi preservado como texto: em `Medal`, por exemplo, são 231.333 linhas com `'NA'` e nenhuma nula.

## Hipóteses H1–H8 (investigação antes da refined)

Antes de transformar qualquer coisa, cada hipótese da [spec](docs/SPEC.md) foi verificada com uma consulta sobre o schema `raw`. Todas as consultas estão em [`sql/investigacao/hipoteses.sql`](sql/investigacao/hipoteses.sql), uma por bloco, e podem ser rodadas de novo no `ui.py`. Nada foi alterado nesta etapa: as decisões são tomadas nas unidades da refined, citando estes números.

| # | Hipótese | Resultado | O que o dado mostrou |
|---|---|---|---|
| H1 | Existem linhas duplicadas idênticas em `athlete_events` | **Confirmada** | 612 grupos de linhas idênticas nas 15 colunas, somando 1.997 linhas; **1.385 linhas em excesso** (conferido por outro caminho: 271.116 linhas − 269.731 distintas = 1.385). Das 1.385, **1.315 são de `Art Competitions`**; o resto é Sailing (37), Cycling (32) e Equestrianism (1). |
| H2 | Uma edição pode ter mais de uma cidade | **Confirmada** | Só uma edição: **1956 Summer**, com `Melbourne` e `Stockholm`. |
| H3 | Um mesmo `ID` aparece com nomes ou sexo diferentes | **Não confirmada** | Dos 135.571 `ID`s distintos, 0 têm mais de um nome e 0 têm mais de um sexo. |
| H4 | Existem NOCs em `athlete_events` que não estão em `noc_regions` | **Confirmada** | Só um: **`SGP`**, com 349 linhas (Team `Singapore` e nomes de barcos/duplas, de 1948 a 2016). No sentido inverso, `SIN` (região `Singapore`) está em `noc_regions` e nunca aparece em `athlete_events`. |
| H5 | Vários NOCs apontam para a mesma região | **Confirmada** | 15 regiões com mais de um NOC, por exemplo: Germany (FRG, GDR, GER, SAA), Russia (EUN, RUS, URS), Czech Republic (BOH, CZE, TCH), Serbia (SCG, SRB, YUG). Uma das "regiões" agrupadas é o texto `NA` (ROT, TUV, UNK, cujas notas são Refugee Olympic Team, Tuvalu e Unknown): é ausência, não uma região. |
| H6 | `Art Competitions` aparece como modalidade | **Confirmada** | 3.578 linhas, 7 edições (de 1912 a 1948), 29 provas e 1.814 atletas. |
| H7 | Os Jogos de 1906 estão no dataset | **Confirmada** | `1906 Summer`, em Athina: 1.733 linhas e 841 atletas. |
| H8 | `Height` e `Weight` têm valores decimais | **Confirmada só em `Weight`** | `Height`: 210.945 valores preenchidos, nenhum com ponto decimal. `Weight`: 208.241 preenchidos, **1.058 fracionários** (os mais comuns: 63.5, 69.5, 67.5). Nenhum valor preenchido deixa de converter para número nas duas colunas. |

### Perfil de ausências

Quantos valores de cada coluna são o texto `NA` ou texto vazio `''`. As colunas que não aparecem na tabela têm zero nos dois.

| Tabela | Coluna | Texto `NA` | Texto vazio |
|---|---|---|---|
| `athlete_events` | `Age` | 9.474 | 0 |
| `athlete_events` | `Height` | 60.171 | 0 |
| `athlete_events` | `Weight` | 62.875 | 0 |
| `athlete_events` | `Medal` | 231.333 | 0 |
| `noc_regions` | `region` | 3 | 0 |
| `noc_regions` | `notes` | 0 | 209 |

Em `athlete_events`, a ausência aparece só como `NA`, e só nas quatro colunas que a spec já citava. Em `noc_regions`, `notes` vazio aparece como `''` (209 de 230 linhas), e `region` tem 3 `NA`.

### Pontos que ficam para as próximas unidades

- **H1 (duplicatas):** decidir na tabela fato (3.3) se as 1.385 linhas em excesso saem, sabendo que quase todas são de `Art Competitions`, que os marts já excluem.
- **H2 (1956 com duas cidades):** pela spec, essa dúvida é apresentada antes de criar `refined.games` (3.2), com duas opções: uma tabela de cidades separada ou a cidade fora da dimensão.
- **H4 (`SGP` × `SIN`):** decidir na `refined.noc_regions` (3.2) como ligar as 349 linhas de `SGP`, porque hoje elas ficariam sem região.
- **H5 (`region = 'NA'`):** na refined, esses 3 viram nulo e deixam de parecer uma região chamada "NA".
- **H8:** `Weight` precisa de um tipo com decimais; `Height` cabe em inteiro. O tipo é definido na fato (3.3).
- **`notes` vazio:** decidir na `refined.noc_regions` se `''` vira nulo, como o `NA`.

_H4, H5 e `notes` vazio já foram resolvidos em `refined.noc_regions`, H2 em `refined.games` / `refined.games_cities`, e H1 e H8 em `refined.athlete_results` (ver "Decisões sobre o dado")._

## Decisões sobre o dado

| Etapa | Decisão | Motivo | Linhas afetadas |
|---|---|---|---|
| Estrutura | Arquivos originais versionados em `raw/` | Licença CC0 permite; quem clona chega aos mesmos números sem depender do Kaggle | — |
| Estrutura | Banco DuckDB fora do git | É gerado do zero pelo pipeline; versionar criaria um arquivo binário que muda a cada execução | — |
| Raw | Todas as colunas lidas como texto (VARCHAR) | Conversão de tipo é decisão; fica registrada na refined | nenhuma (nada alterado) |
| Raw | Texto `NA` mantido como texto, não convertido em nulo | No dataset a ausência vem escrita como `NA`; converter na leitura seria uma limpeza escondida na raw | nenhuma (nada alterado) |
| Raw | Faltando um arquivo de origem, nada é ingerido | Ingerir uma tabela de duas em silêncio gera indicadores errados que parecem certos | — |
| Estrutura | Pasta `sql/investigacao/` (não prevista na estrutura inicial da spec) com as consultas das hipóteses | Cada número citado no README precisa ter a consulta de onde saiu, e qualquer pessoa pode rodá-la de novo | — |
| Refined — `noc_regions` | `TRIM` em todos os textos | Regra geral da refined: espaço sobrando faz o mesmo valor parecer dois | 0 (nenhum valor tinha espaço sobrando) |
| Refined — `noc_regions` | Texto `NA` em `region` vira NULL | Regra geral da refined; sem isso, ROT, TUV e UNK pareciam uma região chamada "NA" (H5) | 3 (ROT, TUV, UNK) |
| Refined — `noc_regions` | Texto vazio `''` em `notes` vira NULL | Na refined toda ausência é NULL, para consultar só com `IS NULL` | 209 |
| Refined — `noc_regions` | Linha `SGP → Singapore` acrescentada a partir da linha `SIN`, que é mantida | Os atletas de Singapura usam `SGP`, que não existia em `noc_regions` (H4); sem a linha, ficariam sem região e a fato teria chave sem dimensão. Nenhum registro da origem é apagado ou alterado | +1 linha na dimensão (230 → 231); 349 linhas de atletas passam a ter região |
| Refined — `games` | Uma linha por edição (`games_id` = texto de `Games`), com `year` convertido para INTEGER | Nos dados, `Games` é sempre `Year + ' ' + Season` e cada edição tem um único ano e temporada; Verão e Inverno do mesmo ano são edições distintas | 271.116 linhas da raw → 51 edições (29 de Verão, 22 de Inverno); 0 falhas na conversão de `year` |
| Refined — `games` | Cidade fora de `refined.games`, numa tabela própria `refined.games_cities` (edição × cidade) | H2: 1956 Summer teve Melbourne (4.829 linhas) e Stockholm (298, todas de Equestrianism). Com a cidade na dimensão, essa edição viraria duas linhas; tirando a cidade da refined, o mart 03 dependeria da raw | 52 pares edição × cidade (51 edições + a segunda cidade de 1956) |
| Refined — `events` | Uma linha por par `sport + event`, com `event_id` gerado por `ROW_NUMBER()` ordenado por `sport` e `event` | A spec define a prova pelo par; nos dados, nenhuma prova aparece em duas modalidades. A ordenação torna o id determinístico (estável enquanto o conjunto de provas não mudar; o dataset é fixo) | 271.116 linhas da raw → 765 provas de 66 modalidades (29 delas de Art Competitions, mantidas; a exclusão é nos marts) |
| Refined — `athletes` | Uma linha por atleta (`athlete_id` INTEGER, `name`, `sex`); idade, altura e peso ficam na fato | Esses três mudam a cada participação. H3 não se confirmou (nenhum ID com dois nomes ou dois sexos), então cada ID vira exatamente uma linha. Homônimos (713 nomes com mais de um ID) continuam separados, porque a chave é o ID | 271.116 linhas da raw → 135.571 atletas (33.981 F, 101.590 M); 0 falhas na conversão do ID |
| Refined — `athletes` | Espaços excedentes em `name`: `TRIM` nas pontas e qualquer sequência de 2+ espaços no meio vira **um** espaço | A spec manda remover espaços excedentes; `name` é a única coluna do dataset com esse problema. Conferido nos dados: em todos os nomes alterados, as letras e o número de palavras continuam iguais (nada fica grudado, ex.: `João   Pedro` → `João Pedro`) | 157 atletas (35 com espaço nas pontas, 128 com espaço duplo no meio) |
| Refined — `athlete_results` | Linhas idênticas nas 15 colunas saem, ficando uma (H1) | Uma cópia idêntica não acrescenta informação e infla contagens de linhas. Linhas que diferem em qualquer coluna ficam: medalhas em provas diferentes (ex.: 100 m e 200 m) nunca são duplicata, e as 89 repetições na mesma prova com medalha ou time diferente (regatas de 1900, obras de arte) são mantidas | −1.385 linhas (271.116 → 269.731), 1.315 delas de Art Competitions. Registros com medalha: 39.783 → 39.772 (−11 cópias: 3 de ouro, 8 de prata). Medalhas conquistadas: 18.905 → 18.905 (nenhuma perdida). Atletas com medalha em mais de uma prova na mesma edição: 3.414 → 3.414 |
| Refined — `athlete_results` | `athlete_id`, `age` e `height` INTEGER; `weight` DECIMAL(5,2) | H8: altura não tem decimais; peso tem. Duas casas por decisão do autor | 0 falhas de conversão (todo NULL vem de `NA`). 6 pesos com 13 casas arredondados: `74.6666666666667` → 74.67 e `77.3333333333333` → 77.33 (3 linhas cada) |
| Refined — `athlete_results` | Unidades mantidas como na origem: altura em centímetros, peso em quilogramas | Já é o sistema métrico usado no Brasil (medianas: 175 cm e 70 kg); converter na refined só trocaria a escala sem ganho | nenhuma |
| Refined — `athlete_results` | Idade, altura e peso ausentes continuam NULL (sem imputação) | Regra da spec: preencher seria inventar dado | NULL: `age` 9.315, `height` 58.814, `weight` 61.527 |
| Refined — `athlete_results` | Toda chave da fato existe na dimensão | Regra da spec; conferido com LEFT JOIN em cada dimensão | 0 órfãos em `athlete_id`, `games_id`, `event_id` e `noc` |
| Refined | Verificações de integridade rodam a cada execução, sobre os dados reais, e falham a execução se acharem problema | A spec manda garantir que toda chave da fato exista na dimensão; os testes provam isso só com dados inventados. Assim, uma mudança na raw ou num SQL da refined é percebida antes de chegar aos marts | 12 verificações, 0 problemas nos dados reais |
| Origem | Nomes sem letras acentuadas (ex.: `Mnica`, `Rukajrvi`) mantidos como vieram | O `athlete_events.csv` original tem 0 bytes fora do ASCII: os acentos já foram removidos na origem do Kaggle, não na nossa leitura. Não há como recuperar sem inventar dado | nenhuma (nada alterado) |
| Projeto | Dashboard Streamlit obrigatório (no desafio é opcional) | Decisão do autor: o projeto só está completo com o dashboard lendo os marts | — |

## Documentação

- [`docs/SPEC.md`](docs/SPEC.md): especificação completa do projeto (arquitetura, modelo de dados, regras de contagem e fluxo de desenvolvimento).

## Onde a IA errou (e como descobri)

_Preenchido ao longo do projeto, no momento em que acontece._

| Etapa | O que a IA fez ou assumiu | Como descobri |
|---|---|---|
| 1.1 — `pipeline/db.py` | Leu a contagem de `gravar` com `fetchone()`, que no DuckDB 2.x deixa o resultado aberto e trava o próximo uso da mesma conexão | O teste "gravar duas vezes substitui sem duplicar" falhou com `ResourceInUseException`; corrigido para `fetchall()` |
