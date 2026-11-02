# 🏅 OlympicScope

Pipeline de Engenharia de Dados sobre 120 anos de história olímpica (1896–2016): do arquivo de origem até os indicadores, em camadas **raw → refined → marts → dashboard Streamlit**, com Python, DuckDB, SQL e testes.

Projeto do desafio final da Trilha de Engenharia de Dados JR.

> **Período dos dados: Jogos de Verão de 1896 (Athina) a 2016 (Rio de Janeiro) e Jogos de Inverno de 1924 (Chamonix) a 2014 (Sochi).**
> Todos os números vêm só dos dois arquivos CSV do Kaggle, coletados em 2018. Edições posteriores a essas **não estão** no projeto, e nenhum dado foi buscado em outra fonte. Quando um indicador fala em "atual" ou "histórico", é sempre até 2016 (Verão) e 2014 (Inverno).

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
| **marts** | indicadores, cada um gerado por um arquivo em `sql/marts/` | feito: 15 marts (os 4 ★ e os 05 a 15), listados em "Indicadores" |
| **dashboard** | app Streamlit em `app/app.py`, lendo só do schema `marts` | feito: 4 páginas (Medalhas, Países, Atletas, Os Jogos) com os 15 marts; publicação na unidade 6.4 |

## Indicadores

Cada indicador é uma tabela no schema `marts`, gerada por **um** arquivo SQL. O comentário no topo de cada arquivo diz a pergunta que ele responde, o grão, as regras de contagem e as exclusões.

**Regras que valem para todos os marts:**
- **Medalhas conquistadas:** uma por combinação distinta de edição + prova + NOC + medalha. Um time de basquete campeão conta **1** ouro.
- **Registros de medalhistas:** linhas com medalha. O mesmo time de 12 jogadores conta **12**.
- **País = NOC**, com a região ao lado. NOCs históricos (URS, GDR, FRG...) ficam separados.
- **Exclusões:** `Art Competitions` e os Jogos de 1906 ficam fora dos marts (continuam na refined).

| Mart | Pergunta | Grão | SQL | Linhas |
|---|---|---|---|---|
| ★ `marts.medalhas_por_pais_edicao` | Quantas medalhas cada país conquistou em cada edição, e em que posição ficou? | NOC × edição (todos os NOCs participantes, inclusive sem medalha) | [`sql/marts/01_medalhas_por_pais_edicao.sql`](sql/marts/01_medalhas_por_pais_edicao.sql) | 3.803 |
| ★ `marts.quadro_historico` | Qual é o quadro de medalhas de todos os tempos de cada país, no Verão e no Inverno? | NOC × temporada (inclusive quem nunca ganhou medalha) | [`sql/marts/02_quadro_historico.sql`](sql/marts/02_quadro_historico.sql) | 347 |
| ★ `marts.evolucao_olimpica` | Como os Jogos cresceram: quantos atletas, países, modalidades e provas em cada edição? | edição | [`sql/marts/03_evolucao_olimpica.sql`](sql/marts/03_evolucao_olimpica.sql) | 50 |
| ★ `marts.participacao_genero` | Como mudou a participação de homens e mulheres ao longo das edições? | edição × sexo (toda edição com F e M) | [`sql/marts/04_participacao_genero.sql`](sql/marts/04_participacao_genero.sql) | 100 |
| `marts.desempenho_esportivo` | Qual o tamanho de cada modalidade: participações, atletas, provas e medalhas? | modalidade × temporada | [`sql/marts/05_desempenho_esportivo.sql`](sql/marts/05_desempenho_esportivo.sql) | 68 |
| `marts.perfil_atletas` | Qual a idade, altura e peso médios dos atletas de cada modalidade, por sexo? | modalidade × sexo × temporada | [`sql/marts/06_perfil_atletas.sql`](sql/marts/06_perfil_atletas.sql) | 118 |
| `marts.perfil_atletas_pais` | Qual a idade, altura e peso médios dos atletas de cada país, por sexo? | NOC × sexo × temporada | [`sql/marts/07_perfil_atletas_pais.sql`](sql/marts/07_perfil_atletas_pais.sql) | 654 |

| `marts.ranking_atletas` | Quem são os maiores medalhistas individuais? | atleta (só medalhistas) | [`sql/marts/08_ranking_atletas.sql`](sql/marts/08_ranking_atletas.sql) | 27.821 |
| `marts.estreias_paises` | Quando cada país estreou, e quando ganhou a primeira medalha e o primeiro ouro? | NOC × temporada | [`sql/marts/09_estreias_paises.sql`](sql/marts/09_estreias_paises.sql) | 347 |
| `marts.eficiencia_paises` | Quantas medalhas cada país conquistou para cada 100 atletas enviados? | NOC × edição | [`sql/marts/10_eficiencia_paises.sql`](sql/marts/10_eficiencia_paises.sql) | 3.803 |
| `marts.dominio_modalidade` | Quais países mais ganharam em cada modalidade, e com que fatia das medalhas? | modalidade × temporada × NOC (só quem ganhou) | [`sql/marts/11_dominio_modalidade.sql`](sql/marts/11_dominio_modalidade.sql) | 1.433 |
| `marts.genero_por_pais` | Qual a participação de mulheres na delegação de cada país, por edição? | NOC × edição | [`sql/marts/12_genero_por_pais.sql`](sql/marts/12_genero_por_pais.sql) | 3.803 |
| `marts.longevidade_atletas` | Quais atletas disputaram mais edições, e por quanto tempo? | atleta (2 edições ou mais) | [`sql/marts/13_longevidade_atletas.sql`](sql/marts/13_longevidade_atletas.sql) | 36.770 |
| `marts.medalhistas_extremos` | Quem foram os medalhistas mais jovens e mais velhos de cada modalidade? | modalidade × temporada × extremo × atleta (empatados ficam) | [`sql/marts/14_medalhistas_extremos.sql`](sql/marts/14_medalhistas_extremos.sql) | 190 |
| `marts.programa_olimpico` | Quando cada modalidade entrou e saiu dos Jogos, e quantas vezes ficou de fora? | modalidade × temporada | [`sql/marts/15_programa_olimpico.sql`](sql/marts/15_programa_olimpico.sql) | 68 |

As médias de idade, altura e peso vêm com `n_idade`, `n_altura` e `n_peso`: quantos atletas × edição entraram em cada média. Altura em centímetros e peso em quilogramas no banco; o dashboard mostra no padrão brasileiro (ex.: 1,75 m e 63,50 kg).

## Como rodar do zero

Pré-requisito: [uv](https://docs.astral.sh/uv/) instalado.

```bash
git clone https://github.com/Surmani/OlympicScope.git
cd OlympicScope
uv sync
uv run python -m pipeline.ingestao   # raw/ → schema raw do DuckDB
uv run python -m pipeline.refined    # schema raw → schema refined (SQL em sql/refined/)
uv run python -m pipeline.marts      # schema refined → schema marts (SQL em sql/marts/)
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

Os marts executam, em ordem, os arquivos de `sql/marts/` (um arquivo por indicador) e imprimem a contagem de cada tabela criada. Se a pasta não tiver nenhum SQL, o script avisa e termina com erro, em vez de "dar certo" sem gerar nada.

```
marts.medalhas_por_pais_edicao: 3.803 linhas
marts.quadro_historico: 347 linhas
marts.evolucao_olimpica: 50 linhas
marts.participacao_genero: 100 linhas
marts.desempenho_esportivo: 68 linhas
marts.perfil_atletas: 118 linhas
marts.perfil_atletas_pais: 654 linhas
marts.ranking_atletas: 27.821 linhas
marts.estreias_paises: 347 linhas
marts.eficiencia_paises: 3.803 linhas
marts.dominio_modalidade: 1.433 linhas
marts.genero_por_pais: 3.803 linhas
marts.longevidade_atletas: 36.770 linhas
marts.medalhistas_extremos: 190 linhas
marts.programa_olimpico: 68 linhas
```

_Os comandos das próximas camadas serão adicionados a cada etapa._

## Dashboard

```bash
uv run streamlit run app/app.py
```

Abre em http://localhost:8501. O dashboard só **consulta**: lê o schema `marts` em modo leitura, só com `SELECT ... WHERE` (as consultas estão em [`app/consultas.py`](app/consultas.py), testadas), e mostra os números no padrão brasileiro (altura em metros, peso em kg, vírgula decimal). O período dos dados fica no topo de todas as páginas.

- **Temporada** (Verão ou Inverno) no menu lateral, valendo para todas as páginas.
- **Medalhas:** quadro por edição e de um país ao longo do tempo, quadro histórico, ranking de atletas e domínio por modalidade.
- **Países:** estreias, medalhas por 100 atletas, mulheres na delegação e perfil médio dos atletas.
- **Atletas:** perfil médio por modalidade, longevidade (mais edições disputadas) e medalhistas mais jovens e mais velhos.
- **Os Jogos:** evolução (atletas, países, modalidades e provas), participação de mulheres e homens, tamanho das modalidades e programa olímpico.
- Os eixos dos gráficos saem no formato americano (limitação dos gráficos nativos do Streamlit); tabelas e textos, no brasileiro.
- O banco só fica aberto durante cada consulta, então dá para rodar o pipeline com o dashboard aberto. Os resultados ficam em cache por 1 hora; para ver números novos antes disso, use "Clear cache" no menu do Streamlit.

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
| Estrutura | Execução de pastas de SQL num módulo único, `pipeline/executor_sql.py`, usado pela refined e pelos marts | As duas camadas fazem exatamente o mesmo (ordem pelo prefixo, nome da tabela conferido, contagem do banco); com duas cópias, uma correção seria esquecida na outra. A refined continuou com as mesmas contagens e 12 de 12 verificações depois da mudança | — |
| Marts | `Art Competitions` e Jogos de 1906 fora de todos os marts | H6 e H7 confirmaram que existem: competição artística não é esportiva, e 1906 não é reconhecido pelo COI. Ficam na refined; cada mart escreve a regra no comentário do SQL | base dos marts: 269.731 → 265.735 linhas (50 edições) |
| Mart 01 | Todos os NOCs participantes de cada edição, com zero quando não ganharam medalha; `ranking_edicao` NULL para quem não tem medalha | O dashboard pode mostrar quem participou sem medalha e filtrar só medalhistas com `WHERE`; quem não tem medalha não aparece no quadro | 3.803 pares NOC × edição, 1.631 com medalha |
| Mart 01 | Ranking pelo critério do COI (ouro, prata, bronze) com `RANK()`: empatados dividem a posição e a próxima pula (1, 2, 2, 4) | É como os quadros oficiais mostram empates | 174 empates nos dados, envolvendo 536 NOCs |
| Mart 01 | Regra da spec para medalhas conquistadas mantida, com limitação registrada | Em 19 casos a mesma edição + prova + NOC + medalha aparece com mais de um `Team`: às vezes são duas medalhas de verdade (KOR, 2 bronzes no tênis de mesa em duplas de 1992), às vezes uma só com o nome do cavalo em `Team` (hipismo por equipes de 2008). `Team` não separa os dois casos com segurança | no máximo 22 medalhas contadas a menos, de 18.534 |
| Mart 02 | `quadro_historico` lê do mart 01 (soma por NOC × temporada) em vez de repetir as regras sobre a refined | Regras de contagem e exclusões escritas num lugar só; os totais dos dois marts batem por construção (toda medalha pertence a uma única edição). Ranking pelo critério do COI dentro de cada temporada, com `RANK()` e NULL para quem nunca ganhou medalha | 347 pares NOC × temporada (192 com medalha); 18.534 medalhas e 39.158 registros, iguais ao mart 01 |
| Mart 03 | `city` de 1956 Summer exibida como `Melbourne \| Stockholm` (cidades juntas em ordem alfabética) | Consequência da H2: mantém uma linha por edição sem esconder a segunda cidade e sem inventar regra de "cidade principal" | 1 edição; as outras 49 têm uma cidade só |
| Mart 03 | Art Competitions fora de atletas, países, modalidades e provas | Mesma exclusão padrão de todos os marts. Muda bastante 7 edições (1912 a 1948): em 1932 Summer, 1.922 atletas com Art e 1.335 sem | 7 edições com contagem menor; nenhuma edição some |
| Mart 04 | Toda edição tem as linhas F e M, mesmo com zero atletas de um sexo | Em 1896 não houve mulheres: com a linha F = 0, o gráfico mostra 0% em vez de um buraco, e o dashboard não precisa completar linhas (ele só faz `SELECT ... WHERE`). O zero é o resultado da contagem, não dado inventado | 1 linha com zero (1896 Summer, F); 100 linhas no total |
| Mart 04 | `percentual_atletas` de 0 a 100 com 2 casas (`DECIMAL(5,2)`) | Mesmo padrão do peso; na tela vira `45,03%`. O arredondamento poderia fazer F + M somar 99,99 ou 100,01 | nos dados reais, F + M soma exatamente 100,00 nas 50 edições |
| Marts 06 e 07 | Nas médias de idade, altura e peso, cada atleta entra **uma vez por edição** (por modalidade no 06, por NOC no 07), não uma vez por prova | A média responde "qual a altura média dos atletas"; por linha, quem disputou 15 provas na mesma edição pesaria 15 vezes. Nenhum atleta tem valores diferentes entre provas da mesma edição, então juntar não perde nada | 265.735 participações → 184.569 atletas × edição (0 com valores diferentes). No 06, 599 atletas × edição contam em duas modalidades |
| Marts 06 e 07 | Médias com 2 casas, sem imputação, com `n_idade`, `n_altura` e `n_peso`; grupos com poucos dados ficam no mart | Mostra sobre quantos dados cada média foi calculada; quem exibe decide filtrar | 06: 11 grupos sem nenhuma altura; 07: 14 |
| Mart 08 | Ranking só com medalhistas; cada linha com medalha é uma medalha do atleta | Um ranking com mais de 100 mil atletas zerados não acrescenta nada; no nível individual, cada jogador de um time campeão ganhou um ouro (regra da spec) | 27.821 medalhistas de 133.179 atletas; 39.158 medalhas individuais, igual aos registros do mart 01 |
| Mart 08 | `noc` com todos os países que o atleta defendeu, juntos em ordem alfabética (ex.: `GDR \| GER`) | Mostrar só um esconderia parte da carreira | 767 medalhistas com mais de um NOC (319 ganharam medalha por mais de um) |
| Mart 09 | Lê do mart 01; inclui primeiro ouro além da primeira medalha | Regras e exclusões num lugar só; "quando veio o primeiro ouro" é tão útil quanto a primeira medalha | 347 NOC × temporada: 155 nunca ganharam medalha, 202 nunca ganharam ouro |
| Mart 10 | Taxa em medalhas por 100 atletas, com 2 casas, e todos os participantes | Por atleta os números ficam pequenos demais para ler. Delegações pequenas distorcem a taxa (1896 AUS: 1 atleta, 3 medalhas = 300); a coluna `atletas` fica para o dashboard filtrar | 3.803 NOC × edição; delegações somam 184.569, igual ao mart 03 |
| Mart 11 | Só NOCs com medalha na modalidade; prova em grupo conta 1 medalha para o país; `percentual_medalhas` = fatia das medalhas da modalidade | Ranking de domínio não precisa de quem nunca ganhou; proporção compara modalidades de tamanhos diferentes. O arredondamento faz a soma de uma modalidade variar | 1.433 de 3.963 pares modalidade × NOC; 18.534 medalhas, igual ao mart 05; soma dos percentuais de 99,95 a 100,08 |
| Mart 12 | Todas as delegações, inclusive as sem mulheres (0%) ou sem homens (100%) | É o que o mart quer mostrar | 3.803 delegações: 1.018 sem mulheres, 31 sem homens |
| Mart 13 | Só atletas com 2 edições ou mais; Verão e Inverno somados; ranking por edições e, no empate, anos de carreira | Quem esteve numa edição só não tem longevidade para mostrar; a carreira olímpica é uma só | 36.770 de 133.179 atletas; máximo de 10 edições (Ian Millar, 1972–2012) |
| Mart 14 | Todos os empatados ficam; uma linha por atleta em cada extremo, com quantas medalhas ganhou naquela idade e as provas juntas; medalhas sem idade ficam de fora | Escolher um entre atletas da mesma idade seria arbitrário. Toda modalidade tem medalhista com idade | 190 linhas (97 mais jovens, 93 mais velhos); 573 medalhas sem idade fora do mart |
| Mart 15 | "Programa atual" = última edição do dataset (2016 no Verão, 2014 no Inverno); `ausencias` = edições da temporada, entre a primeira e a última, sem a modalidade | O dataset termina nessas edições; ausências mostram modalidades que saíram e voltaram | 68 modalidades: 49 no programa de 2016/2014, 19 com ausências |
| Dashboard | Consultas do app separadas da tela (`app/consultas.py`), cada uma com texto SQL fixo e filtros como parâmetro; um teste confere que nenhuma tem `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`, `GROUP BY`, `JOIN` ou janela, nem lê `refined`/`raw` | Garante a regra "só `SELECT ... WHERE` nos marts" com teste, não só com revisão | 19 consultas |
| Dashboard | Cortes mínimos ajustáveis (padrão 10): delegação mínima na eficiência e mínimo de atletas na média do perfil por país | Amostras pequenas distorcem taxa e média; o corte é um `WHERE`, então a regra do dashboard continua valendo | — |
| Dashboard | Exibir as 10 primeiras linhas nos gráficos de barras (as tabelas mostram todas) | Gráfico com centenas de barras fica ilegível; as linhas já vêm ordenadas do SQL. Em "Tamanho das modalidades", o gráfico reordena as linhas pelo indicador escolhido antes de pegar as 10 primeiras (só muda a ordem, não calcula nada) | — |
| Estrutura | Configuração mínima do Ruff (`known-first-party`) no `pyproject.toml` | Os módulos do `app/` são importados sem prefixo (o `streamlit run` coloca `app/` no caminho), e o Ruff os misturava com as bibliotecas externas | — |
| Mart de sede | Não feito (vantagem do país-sede) | Os CSVs só têm a cidade-sede; nenhuma coluna liga cidade a país e nenhuma nota de `noc_regions` cita as 42 cidades. Fazer exigiria dado de fora dos CSVs | — |
| Origem | Nomes sem letras acentuadas (ex.: `Mnica`, `Rukajrvi`) mantidos como vieram | O `athlete_events.csv` original tem 0 bytes fora do ASCII: os acentos já foram removidos na origem do Kaggle, não na nossa leitura. Não há como recuperar sem inventar dado | nenhuma (nada alterado) |
| Projeto | Dashboard Streamlit obrigatório (no desafio é opcional) | Decisão do autor: o projeto só está completo com o dashboard lendo os marts | — |

## Documentação

- [`docs/SPEC.md`](docs/SPEC.md): especificação completa do projeto (arquitetura, modelo de dados, regras de contagem e fluxo de desenvolvimento).

## Onde a IA errou (e como descobri)

_Preenchido ao longo do projeto, no momento em que acontece._

| Etapa | O que a IA fez ou assumiu | Como descobri |
|---|---|---|
| 1.1 — `pipeline/db.py` | Leu a contagem de `gravar` com `fetchone()`, que no DuckDB 2.x deixa o resultado aberto e trava o próximo uso da mesma conexão | O teste "gravar duas vezes substitui sem duplicar" falhou com `ResourceInUseException`; corrigido para `fetchall()` |
| 2.4 — `ui.py` | Na verificação manual, o script da IA encerrou só o processo do `uv` e deixou o `python ui.py` filho rodando, segurando o banco | A ingestão rodada logo depois falhou com erro de lock; a IA conferiu que o processo era o `ui.py` e o encerrou. O código entregue não tinha o problema |
| 3.1 — hipóteses | Duas consultas de `hipoteses.sql` usaram recursos que o DuckDB não suporta (alias junto com subconsulta; `QUALIFY` com `GROUP BY ALL`) | Falharam na primeira execução; corrigidas antes de qualquer número ir para o README |
| 3.2c — `events` | No teste da saída do `refined.py`, a IA esperava 4 provas nos dados inventados, mas eram 3 (`Swimming 100m` se repetia) | Recontando os dados inventados antes de rodar o teste |
| Mart 02 | No teste que confere se os marts 01 e 02 batem, o valor esperado foi escrito errado (9 medalhas em vez de 10) | O teste falhou; o SQL estava certo e os dois lados da comparação já eram iguais |
| Mart 02 → 03 | Ao dizer quantas unidades faltavam, a IA contou uma a mais desde a 4.1 (disse 7 quando eram 6) | Recontando a lista de unidades uma a uma, ao responder "faltam quantos?" |
| Mart 08 | Na proposta e no primeiro comentário do SQL, a IA disse que 319 medalhistas tinham mais de um NOC; o mart mostrou 767. Os 319 eram só os que ganharam medalha por mais de um país; o mart junta os NOCs de todas as participações | Conferindo a contagem do mart nos dados reais, depois de rodar; comentário do SQL e README corrigidos |
| Rodadas 2 e 4 (consultas de investigação) | Usou `at` como apelido de tabela em consultas avulsas de conferência, e `at` é palavra reservada no DuckDB | As consultas falharam com erro de sintaxe; o apelido foi trocado. Nenhuma delas faz parte do projeto |
| 5.1 — dashboard | No teste das consultas, criou o banco temporário com o nome `marts.duckdb`; o DuckDB passou a ter um catálogo `marts` que conflita com o schema `marts` | Os testes falharam com "Ambiguous reference to catalog or schema"; o arquivo foi renomeado |
