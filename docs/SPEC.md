# OlympicScope — Especificação do Projeto

## 1. Objetivo

Desenvolver um projeto de Engenharia de Dados com o dataset **120 Years of Olympic History – Athletes and Results**, do Kaggle.

O projeto constrói um pipeline completo — ingestão, transformação, modelagem analítica, indicadores em SQL e visualização — seguindo a arquitetura em camadas:

`RAW → REFINED → MARTS → STREAMLIT`

O desenvolvimento é incremental, orientado por especificação e dividido em unidades pequenas, cada uma com seu próprio commit.

Este projeto é o desafio final da Trilha de Engenharia de Dados JR. Critério principal:

- cada indicador tem um arquivo `.sql` de onde saiu;
- cada decisão sobre o dado tem um motivo escrito;
- o histórico do git conta a ordem em que as coisas aconteceram.

## 2. Fonte de dados

- **Dataset:** 120 Years of Olympic History – Athletes and Results
- **URL:** https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results
- **Autora:** Randi H. Griffin; dados coletados do Sports Reference em 2018
- **Licença informada pelo Kaggle:** CC0 – Public Domain

### Arquivos

**athlete_events.csv** — aproximadamente 271.116 linhas e 15 colunas (confirmar na ingestão).

| Coluna | Descrição |
|---|---|
| ID | Identificador do atleta |
| Name | Nome do atleta |
| Sex | Sexo (M/F) |
| Age | Idade na participação |
| Height | Altura em centímetros |
| Weight | Peso em quilogramas |
| Team | Nome da equipe |
| NOC | Código do Comitê Olímpico Nacional |
| Games | Identificação da edição (ex.: `1992 Summer`) |
| Year | Ano |
| Season | Temporada (Summer/Winter) |
| City | Cidade-sede |
| Sport | Modalidade |
| Event | Prova (o texto já inclui o nome da modalidade) |
| Medal | Gold, Silver, Bronze ou o texto `NA` |

**noc_regions.csv** — aproximadamente 230 linhas e 3 colunas (confirmar na ingestão).

| Coluna | Descrição |
|---|---|
| NOC | Código do Comitê Olímpico Nacional |
| region | Nome da região/país |
| notes | Observações |

### O que é uma linha de cada arquivo

- `athlete_events.csv`: um atleta em uma prova em uma edição dos Jogos.
- `noc_regions.csv`: um código NOC e a região a que ele pertence.

### Observações conhecidas sobre os dados

- Cobre Jogos de Verão e de Inverno, de Atenas 1896 a Rio 2016.
- Ausências são marcadas com o **texto `NA`** (em `Age`, `Height`, `Weight`, `Medal` e possivelmente outras colunas) — não com célula vazia.
- Um mesmo atleta aparece várias vezes na mesma edição (uma linha por prova).
- Idade, altura e peso podem variar entre participações ou estar ausentes.
- **Esportes coletivos:** cada jogador do time tem sua própria linha com medalha. Contar linhas com medalha NÃO é contar medalhas conquistadas.

### Hipóteses a verificar com contagens (não assumir antes de conferir)

| # | Hipótese | Onde verificar |
|---|---|---|
| H1 | Existem linhas duplicadas idênticas em `athlete_events` | Etapa 3 |
| H2 | Uma edição (`Games`) pode ter mais de uma cidade (ex.: 1956 Summer) | Etapa 3, antes de criar `refined.games` |
| H3 | Um mesmo `ID` pode aparecer com nomes ou sexo diferentes | Etapa 3, antes de criar `refined.athletes` |
| H4 | Existem NOCs em `athlete_events` que não estão em `noc_regions` | Etapa 3, teste de integridade |
| H5 | Vários NOCs apontam para a mesma região (ex.: URS e RUS) | Etapa 3 |
| H6 | `Art Competitions` aparece como modalidade | Etapa 3 |
| H7 | Os Jogos de 1906 (não reconhecidos pelo COI) estão no dataset | Etapa 3 |
| H8 | `Height` e `Weight` têm valores decimais | Etapa 3, antes de definir os tipos |

O resultado de cada hipótese (confirmada ou não, com a contagem) deve ir para a seção de decisões do README.

## 3. Stack tecnológica

- Python 3.11 ou superior
- DuckDB como banco analítico
- Pandas para leitura dos CSVs
- SQL para transformação e marts
- Streamlit para visualização (obrigatório neste projeto, embora opcional no desafio)
- Pytest para testes
- Ruff para lint e formatação
- uv para dependências e ambiente virtual
- Git e GitHub para versionamento

Não adicionar bibliotecas sem justificativa.

## 4. Arquitetura

### RAW

Duas partes:

1. **Arquivos de origem** em `raw/`, exatamente como baixados do Kaggle.
2. **Schema `raw` no DuckDB**, com uma tabela por arquivo:
   - `raw.athlete_events`
   - `raw.noc_regions`

Regras:

- Não modificar nem descompactar/recompactar os arquivos originais.
- Nenhuma limpeza nesta camada: nenhuma conversão de tipo, nenhuma linha descartada ou deduplicada, nenhum nome de coluna alterado, nenhum valor corrigido, preenchido ou normalizado.
  Motivo: a fronteira entre "o dado que chegou" e "o dado que eu decidi" precisa existir em algum lugar, e esse lugar é a passagem de raw para refined.
- Todas as colunas das tabelas raw são **VARCHAR** (`dtype=str`, inferência desligada).
  Motivo: a conversão de tipo é uma decisão, e decisões são registradas na refined.
- **Decisão sobre ausências (opção A):** o texto `NA` continua sendo o texto `NA` na raw (`keep_default_na=False` no pandas). A conversão de `NA` em NULL acontece na refined.
  Motivo: no Olist a ausência é célula vazia, que já chega nula. Neste dataset a ausência vem escrita como o texto `NA`; transformá-la em nulo na leitura seria uma normalização escondida dentro da raw.
- Encoding declarado como `utf-8`, nunca adivinhado.
- Nomes de colunas mantidos como na origem.
- Antes de abrir o banco, verificar se todos os arquivos existem. Faltando algum: listar os que faltam, dizer em que pasta procurou e encerrar com `sys.exit(1)`, sem ingerir parcialmente.
  Motivo: ingerir uma tabela de duas em silêncio produz indicadores errados que parecem certos.
- Ingestão idempotente: `CREATE OR REPLACE TABLE`.
- Ao final, imprimir uma linha por tabela com a contagem lida **do banco** (não do DataFrame), milhar separado por ponto, e uma linha com o total.
  Motivo: a contagem na tela tem que ser a do que foi gravado, não a do que estava na memória.
- A pasta `raw/` **é versionada no Git** (a licença CC0 permite redistribuição), para que quem clonar o repositório rode o projeto sem precisar de conta no Kaggle. O README informa que os arquivos foram baixados do Kaggle, com link e licença.

### Módulo de conexão — `pipeline/db.py`

Primeiro código do projeto; todas as etapas o importam. Expõe exatamente:

| Nome | O que faz |
|---|---|
| `PASTA_RAW` | `Path` da pasta `raw/` |
| `CAMINHO_BANCO` | `Path` de `data/olympics.duckdb` |
| `conectar()` | abre o banco, criando a pasta `data/` e o arquivo se faltarem |
| `criar_schema(con, nome)` | `CREATE SCHEMA IF NOT EXISTS` |
| `gravar(con, df, schema, tabela)` | `CREATE OR REPLACE TABLE` com as colunas e tipos do DataFrame, sem alterar nada; devolve a contagem lida do banco |

Regras:

- **Caminhos resolvidos a partir do próprio `db.py`**, nunca do diretório corrente.
  Motivo: rodar o script de outra pasta não pode criar um banco vazio no lugar errado, que parece ingestão quebrada.
- **Só isso, nada mais:** `db.py` não lê CSV, não conhece nome de tabela, não imprime nada e não converte tipo.
  Motivo: todas as etapas importam este arquivo; regra de negócio escondida aqui valeria para todas sem aparecer em nenhuma spec.
- `gravar` não deixa view ou tabela temporária para trás.
- `conectar()` devolve a conexão aberta; quem chama é quem fecha. Nenhuma conexão global.

### Saída no terminal

Todo script executável reconfigura o stdout para UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`).
Motivo: o projeto é desenvolvido no Windows, onde acentos saem embaralhados no terminal por padrão.

### Explorador do banco — `ui.py`

Script na raiz que abre o banco no navegador com a extensão `ui` do DuckDB (`INSTALL ui; LOAD ui; CALL start_ui()`, em http://localhost:4213).

- Fica de pé até Ctrl+C; no Ctrl+C fecha a conexão e sai sem traceback.
  Motivo: o arquivo `.duckdb` aceita um único processo escrevendo; com o `ui.py` de pé, o pipeline falha com erro de lock.
- **Não cria banco:** se `data/olympics.duckdb` não existir, avisa que é preciso rodar a ingestão e sai com `sys.exit(1)`. Por isso não usa `conectar()`.
  Motivo: um banco vazio aberto no navegador parece ingestão quebrada.
- `ui.py` e o pipeline não se importam.

### REFINED

Tipagem, padronização, validação e modelagem relacional. Transformações escritas em SQL, executadas por `pipeline/refined.py`.

Princípio: a refined **não descarta registros válidos**. Linhas que não devem entrar em certos indicadores (ex.: Art Competitions, Jogos de 1906) ficam na refined e são filtradas nos marts, com a regra escrita no SQL do mart.

Modelo lógico inicial (ajustar após verificar as hipóteses H1–H8):

**refined.athletes** — uma linha por atleta.

| Coluna | Tipo |
|---|---|
| athlete_id | INTEGER |
| name | VARCHAR |
| sex | VARCHAR |

Idade, altura e peso não ficam aqui: são da participação. Antes de criar, verificar H3.

**refined.games** — uma linha por edição.

| Coluna | Tipo |
|---|---|
| games_id | VARCHAR (ex.: `1992 Summer`) |
| year | INTEGER |
| season | VARCHAR |

Verão e Inverno do mesmo ano são edições distintas.

**refined.games_cities** — uma linha por par edição × cidade-sede.

| Coluna | Tipo |
|---|---|
| games_id | VARCHAR |
| city | VARCHAR |

Decisão H2 (unidade 3.2b): 1956 Summer teve duas cidades (Melbourne e, só para o hipismo, Stockholm). A cidade saiu de `refined.games` para esta tabela, para que `games_id` continue único sem perder nenhuma cidade.

**refined.noc_regions** — uma linha por NOC.

| Coluna | Tipo |
|---|---|
| noc | VARCHAR |
| region | VARCHAR |
| notes | VARCHAR |

**refined.events** — uma linha por prova.

| Coluna | Tipo |
|---|---|
| event_id | INTEGER |
| sport | VARCHAR |
| event | VARCHAR |

A combinação `sport + event` identifica uma prova. `event_id` é gerado de forma determinística (mesma entrada → mesmo id em toda execução, ex.: `ROW_NUMBER()` ordenado por sport, event).

**refined.athlete_results** — tabela fato.

| Coluna | Tipo |
|---|---|
| athlete_id | INTEGER |
| games_id | VARCHAR |
| event_id | INTEGER |
| noc | VARCHAR |
| team | VARCHAR |
| age | INTEGER |
| height | definir após H8 |
| weight | definir após H8 |
| medal | VARCHAR (Gold/Silver/Bronze ou NULL) |

Grão: uma participação de um atleta em uma prova de uma edição.

Regras de transformação:

- Converter tipos explicitamente (`CAST`/`TRY_CAST`), contando quantos valores viraram NULL por falha de conversão.
- Remover espaços excedentes dos textos.
- Converter o texto `NA` em NULL.
- Não imputar idade, altura nem peso.
- Investigar duplicatas (H1) antes de remover; registrar quantas linhas saíram e por quê.
- Garantir que toda chave da fato exista na dimensão correspondente.
- **Contar linhas antes e depois de cada etapa e de cada JOIN.** Diferença sem explicação é erro.

Toda decisão vai para a seção de decisões do README, no formato: decisão, motivo, linhas afetadas.

### MARTS

Tabelas analíticas no schema `marts`, cada uma gerada por **um arquivo SQL** em `sql/marts/`, executado por `pipeline/marts.py`.

#### Regras de contagem (valem para todos os marts)

- **Medalhas conquistadas:** uma por combinação distinta de `games_id + event_id + noc + medal`. Um time de basquete campeão conta 1 ouro.
- **Registros de medalhistas:** contagem de linhas com medalha. Um time de 12 jogadores conta 12.
- Quando os dois números aparecem, os nomes das colunas deixam claro qual é qual (`medalhas_conquistadas` e `registros_medalhistas`).
- **País = NOC**, com a coluna `region` ao lado para consulta. NOCs históricos (URS, GDR, FRG etc.) ficam separados.
- **Atletas** são contados com `COUNT(DISTINCT athlete_id)`.
- **Ranking de medalhas:** ouro, depois prata, depois bronze (critério do COI).
- **Exclusões padrão** (confirmar após H6 e H7): `Art Competitions` e Jogos de 1906 ficam fora dos marts. A regra fica escrita em comentário no SQL de cada mart.

#### Regra do dashboard aplicada aos marts

O Streamlit só faz `SELECT ... WHERE` nas colunas de filtro. Nada de `SUM`, `AVG`, `COUNT` nem `GROUP BY` no app. Por isso, **cada mart já vem no grão exato em que será exibido**, com as colunas de filtro presentes.

#### Marts previstos

Prioridade: os marcados com ★ são o núcleo do projeto; os demais são feitos se houver tempo.

**★ 01_medalhas_por_pais_edicao.sql** → `marts.medalhas_por_pais_edicao`
- Grão: NOC × edição.
- Colunas: noc, region, games_id, year, season, ouro, prata, bronze, medalhas_conquistadas, registros_medalhistas, ranking_edicao.

**★ 02_quadro_historico.sql** → `marts.quadro_historico`
- Grão: NOC × temporada.
- Colunas: noc, region, season, ouro, prata, bronze, medalhas_conquistadas, registros_medalhistas, edicoes_disputadas, ranking_historico.

**★ 03_evolucao_olimpica.sql** → `marts.evolucao_olimpica`
- Grão: edição.
- Colunas: games_id, year, season, city, atletas, paises (NOCs distintos), modalidades, provas.

**★ 04_participacao_genero.sql** → `marts.participacao_genero`
- Grão: edição × sexo.
- Colunas: games_id, year, season, sex, atletas, percentual_atletas.

**05_desempenho_esportivo.sql** → `marts.desempenho_esportivo`
- Grão: modalidade × temporada.
- Colunas: sport, season, participacoes, atletas, provas, medalhas_conquistadas, registros_medalhistas.

**06_perfil_atletas.sql** → `marts.perfil_atletas`
- Grão: modalidade × sexo × temporada.
- Colunas: sport, sex, season, idade_media, altura_media, peso_media, e a quantidade de registros com valor preenchido para cada média (`n_idade`, `n_altura`, `n_peso`), para deixar claro sobre quantos dados a média foi calculada.

**07_ranking_atletas.sql** → `marts.ranking_atletas`
- Grão: atleta.
- Colunas: athlete_id, name, sex, noc, ouro, prata, bronze, total_medalhas, edicoes, ranking.
- Aqui cada linha com medalha é uma medalha do atleta (correto no nível individual).

Cada mart tem no topo um comentário com: pergunta que responde, grão, regras de contagem e exclusões aplicadas.

### STREAMLIT (obrigatório)

O desafio trata o dashboard como opcional; neste projeto ele é **obrigatório** (decisão do autor), e o projeto só está completo com ele.

- Lê **exclusivamente** do schema `marts`.
- Só `SELECT ... WHERE`; nenhuma regra de negócio, transformação ou agregação.
- Filtros possíveis: temporada, edição, país (NOC), modalidade, sexo — cada gráfico usa apenas os filtros cujas colunas existem no mart que ele lê.
- Títulos, unidades, legendas e uma frase explicando cada indicador, incluindo a diferença entre medalhas conquistadas e registros de medalhistas.

## 5. Estrutura de diretórios

```text
olympicscope/
├── raw/                          # versionado (CC0)
│   ├── athlete_events.csv
│   └── noc_regions.csv
├── data/                         # não versionado
│   └── olympics.duckdb
├── pipeline/
│   ├── __init__.py
│   ├── db.py                     # conexão e criação dos schemas
│   ├── ingestao.py               # raw/ → schema raw
│   ├── refined.py                # raw → refined
│   └── marts.py                  # executa sql/marts/*.sql em ordem
├── sql/
│   ├── investigacao/             # consultas das hipóteses H1–H8 (só leitura)
│   │   └── hipoteses.sql
│   ├── refined/                  # SQL das transformações (NN_<tabela>.sql, em ordem)
│   └── marts/
│       ├── 01_medalhas_por_pais_edicao.sql
│       ├── 02_quadro_historico.sql
│       ├── 03_evolucao_olimpica.sql
│       ├── 04_participacao_genero.sql
│       ├── 05_desempenho_esportivo.sql
│       ├── 06_perfil_atletas.sql
│       └── 07_ranking_atletas.sql
├── tests/
├── app/
│   └── app.py                    # Streamlit (obrigatório)
├── docs/
│   └── SPEC.md                   # este arquivo
├── executar.py                   # reconstrói tudo do zero: ingestão → refined → marts
├── ui.py                         # abre o banco no navegador (DuckDB UI)
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

A estrutura pode ser ajustada, desde que as responsabilidades continuem separadas e documentadas.

## 6. Qualidade e testes

**Regra obrigatória:** nenhum teste abre `data/olympics.duckdb` nem lê os arquivos de `raw/`. Testes usam:

- dados inventados, pequenos e controlados;
- DuckDB em memória (`duckdb.connect()`) ou arquivos temporários (`tmp_path` do pytest).

Testes previstos:

- **Ingestão:** `NA` continua texto; todas as colunas viram texto; arquivo ausente é detectado.
- **Tipagem e transformação:** `NA` vira NULL; tipos convertidos; espaços removidos.
- **Duplicidade:** linhas duplicadas inventadas são tratadas conforme a regra decidida.
- **Integridade referencial:** toda chave da fato existe na dimensão.
- **Indicadores:** um time inventado de 3 jogadores com ouro gera `medalhas_conquistadas = 1` e `registros_medalhistas = 3`.
- **Execução dos marts:** cada SQL de mart roda sobre um schema refined inventado em memória.
- **Funções auxiliares.**

Rodar `uv run pytest` e `uv run ruff check .` ao fim de cada unidade.

## 7. Git e fluxo de desenvolvimento

Padrão Conventional Commits: `tipo(escopo): descrição curta`

Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.

Exemplos:

- `chore(project): initialize project structure`
- `feat(database): implement DuckDB connection`
- `feat(ingestion): load raw CSV files into DuckDB`
- `feat(refined): create athletes dimension`
- `feat(marts): add medals by country per edition`
- `test(refined): add referential integrity tests`
- `docs(readme): document duplicate removal decision`

### REGRA OBRIGATÓRIA: COMMIT MANUAL PELO USUÁRIO

O usuário é o único que executa commits.

Para cada unidade de trabalho, a IA deve:

1. Informar o objetivo da unidade.
2. Informar quais arquivos serão criados ou alterados.
3. Implementar somente esse escopo.
4. Executar os testes e verificações pertinentes.
5. Apresentar o resumo dos arquivos alterados.
6. Informar os testes executados e os resultados.
7. Informar as contagens de linhas antes/depois, quando a unidade mexer em dados.
8. Informar o que assumiu sem que o usuário tenha pedido (para o usuário conferir e registrar na seção "Onde a IA errou" se for o caso).
9. Gerar uma mensagem de commit específica para as alterações.
10. Exibir a mensagem pronta para copiar.
11. Aguardar o usuário executar o commit e confirmar.

A IA NÃO PODE:

- Executar `git commit`, `git push` ou merge.
- Avançar para a próxima unidade sem confirmação.
- Presumir que o commit foi feito.
- Sugerir mensagem de commit genérica.

Modelo de encerramento de unidade:

> **Unidade concluída!**
>
> Arquivos alterados:
> - `pipeline/db.py`
> - `tests/test_db.py`
>
> Testes:
> - `pytest`: 3 aprovados
> - `ruff check`: aprovado
>
> Assumi sem confirmação: _(listar ou "nada")_
>
> Mensagem de commit:
> `feat(database): implement DuckDB connection`
>
> Faça o commit e me confirme para seguirmos.

## 8. Versionamento dos dados

Os arquivos originais de `raw/` são versionados, sem alteração, em um commit próprio. O banco gerado não é versionado: ele é recriado do zero com `executar.py`.

`.gitignore`:

```gitignore
# Banco de dados gerado
data/
*.duckdb
*.duckdb.wal

# Ambiente Python
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/

# Streamlit
.streamlit/secrets.toml
```

## 9. README (exigências do desafio)

O README é a primeira coisa que a correção abre. Ele precisa ter:

1. **Fonte:** link do Kaggle e licença CC0.
2. **O que é uma linha de cada tabela** (raw, refined e marts).
3. **As três camadas** e os indicadores que saem delas, com o caminho do `.sql` de cada um.
4. **Como rodar do zero**, em comandos: `git clone`, `uv sync`, `uv run python executar.py`, `uv run pytest` e `uv run streamlit run app/app.py`.
5. **Decisões sobre o dado:** tabela com decisão, motivo e linhas afetadas, incluindo o resultado das hipóteses H1–H8.
6. **Onde a IA errou:** seção curta, no final, com a etapa em que a IA errou ou assumiu algo não pedido e como foi descoberto (quase sempre contando linhas antes e depois). Preenchida durante o projeto, não no fim.

Quem clona o repositório tem que chegar aos indicadores só lendo o README.

## 10. Etapas de desenvolvimento

**Etapa 0 — Estrutura**
- 0.1 Criar o projeto com uv, dependências e `.gitignore`.
- 0.2 Versionar os arquivos originais em `raw/`, sem alteração.
- 0.3 Adicionar esta spec em `docs/SPEC.md` e o README inicial (fonte, link do Kaggle, licença, origem dos arquivos de `raw/`).

**Etapa 1 — Banco**
- 1.1 `pipeline/db.py`: `PASTA_RAW`, `CAMINHO_BANCO`, `conectar`, `criar_schema`, `gravar`, com testes em banco temporário.

**Etapa 2 — Ingestão RAW**
- 2.1 Validação dos arquivos de origem.
- 2.2 Leitura dos CSVs como texto e criação das tabelas raw (idempotente).
- 2.3 Conferência das contagens com os dados reais e registro no README.
- 2.4 `ui.py` para explorar o banco no navegador.

**Etapa 3 — REFINED**
- 3.1 Investigar H1–H8 e registrar os resultados no README (sem transformar nada ainda).
- 3.2 Dimensões: `noc_regions`, `games`, `events`, `athletes` (uma unidade por dimensão, se necessário).
- 3.3 Tabela fato `athlete_results`.
- 3.4 Testes de tipagem, duplicidade e integridade referencial.

**Etapa 4 — MARTS**
- 4.1 `pipeline/marts.py`.
- 4.2 Um mart por unidade, começando pelos ★, cada um com seu teste.

**Etapa 5 — Dashboard (obrigatório)**
- Streamlit lendo apenas os marts.

**Etapa 6 — Finalização**
- 6.1 `executar.py` rodando tudo do zero.
- 6.2 Revisão de testes e Ruff.
- 6.3 README final, conferido seguindo-o do zero em uma pasta nova.

## 11. Diretrizes para a IA

Trabalhe como engenheiro de dados sênior, priorizando:

- simplicidade e clareza;
- código modular;
- SQL legível e comentado;
- reprodutibilidade e idempotência;
- rastreabilidade (contagens antes e depois);
- testes automatizados;
- documentação das decisões.

Não antecipe etapas. Não implemente funcionalidades de etapas futuras.

### Como cada arquivo é entregue (padrão do curso)

Esta SPEC.md é o mapa do projeto. O detalhe de cada etapa é escrito quando a etapa começa, no topo do próprio arquivo:

1. **A spec como docstring no topo do arquivo**, dizendo por que cada regra existe — não só o que ela manda fazer.
2. **Critérios de aceite** testáveis (ex.: "rodar duas vezes imprime exatamente a mesma coisa").
3. O código, com comentários apenas onde a decisão não é óbvia.
4. **Uma lista final do que a IA assumiu e que não estava na spec.** Se a lista não estiver vazia, é a spec que precisa melhorar — e o item pode ir para a seção "Onde a IA errou" do README.

Quando uma etapa mudar alguma decisão desta SPEC.md, ela é atualizada num commit `docs(spec): ...`.

**Não invente resultados nem características dos dados.** Toda afirmação sobre o dado real precisa vir de uma consulta executada. Se não for possível executar, diga isso e peça ao usuário para rodar a consulta e informar o resultado.

Quando uma decisão importante não estiver definida nesta spec, apresente a dúvida com as opções antes de implementar.

Comece exclusivamente pela Etapa 0, unidade 0.1. Ao terminar cada unidade, apresente a mensagem de commit e aguarde a confirmação do usuário.

**Objetivo final:** um projeto de portfólio de Engenharia de Dados com decisões justificadas e histórico de desenvolvimento organizado.
