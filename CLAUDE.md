# Instruções para a IA — OlympicScope

Responda sempre em português.

## Fonte da verdade

- A especificação do projeto está em `docs/SPEC.md`. Leia antes de qualquer trabalho.
- A spec é a fonte da verdade e o código é consequência dela. Não acrescente requisito que não esteja escrito lá.
- Se algo estiver ambíguo ou não definido, pergunte antes de escrever código, apresentando as opções.
- Não invente características dos dados. Toda afirmação sobre o dado real precisa vir de uma consulta executada.

## Estado atual

Concluídas e commitadas: unidades 0.1 (estrutura uv e .gitignore), 0.2 (arquivos originais em raw/), 0.3 (README e docs/SPEC.md), 1.1 (`pipeline/db.py` com testes), 2.1 (validação dos arquivos de origem em `pipeline/ingestao.py`), 2.2 (leitura dos CSVs como texto e criação das tabelas raw), 2.3 (conferência das contagens e registro no README), 2.4 (`ui.py`, explorador somente leitura), 3.1 (hipóteses H1–H8 em `sql/investigacao/hipoteses.sql` e no README), 3.2a (`pipeline/refined.py` e `refined.noc_regions`), 3.2b (`refined.games` e `refined.games_cities`), 3.2c (`refined.events`), 3.2d (`refined.athletes`), 3.3 (fato `refined.athlete_results`), 3.4 (12 verificações em `sql/verificacoes/refined.sql`), 4.1 (`pipeline/marts.py` e `pipeline/executor_sql.py`), 4.2 (mart ★ 01_medalhas_por_pais_edicao), mart ★ 02_quadro_historico, mart ★ 03_evolucao_olimpica, mart ★ 04_participacao_genero e rodada 1 da 4.3 (marts 05, 06 e 07). Etapas 2 e 3 fechadas; os 4 marts ★ prontos.

O Streamlit é obrigatório neste projeto (decisão do usuário, já na spec).

A 3.2 foi dividida em quatro unidades: 3.2a `noc_regions`, 3.2b `games`, 3.2c `events`, 3.2d `athletes`.

Próxima: **unidade 4.3, rodada 2 — marts 08, 09 e 10**. Depois: rodadas 11–13, 14–15; Streamlit; 6.1 a 6.4 (6.4 = publicação).

Marts 05–15 são feitos em rodadas de até três (pedido do usuário), cada mart com seu commit. Numeração: 06 `perfil_atletas`, 07 `perfil_atletas_pais`, 08 `ranking_atletas`. Mart de vantagem da sede descartado (os CSVs não têm o país da sede).

Atualize esta seção ao final de cada unidade, depois que o usuário confirmar o commit.

## Fluxo de cada unidade

1. Diga o objetivo da unidade e quais arquivos serão criados ou alterados.
2. Implemente somente o escopo da unidade. Não antecipe etapas futuras.
3. Escreva a spec da etapa como docstring no topo de cada arquivo, dizendo por que cada regra existe, com critérios de aceite.
4. Rode as verificações: `uv run pytest` e `uv run ruff check .`. Quando a unidade mexer em dados, rode o pipeline e mostre as contagens de linhas antes e depois.
5. Feche a unidade com este bloco:

   **Unidade X.Y pronta para commit.**
   - **Arquivos:** lista dos arquivos criados ou alterados
   - **Testes:** comandos rodados e resultado
   - **Assumi sem você confirmar:** lista, ou "nada"
   - **Para o README "Onde a IA errou":** se algo que você fez precisou ser corrigido nesta unidade, descreva aqui
   - **Comandos prontos para copiar:**
     ```
     git add <arquivos da unidade>
     git commit -m "<mensagem Conventional Commits específica>"
     git push
     ```

6. Termine sempre com a pergunta exata: **Deseja seguir?**
7. Só comece a próxima unidade depois que o usuário responder que sim.

## Proibido

- Executar `git add`, `git commit`, `git push`, merge ou qualquer comando que altere o histórico do git. O usuário faz todos os commits manualmente.
- Presumir que o commit foi feito.
- Mensagem de commit genérica: ela deve descrever exatamente as alterações da unidade.
- Alterar os arquivos em `raw/`.
- Abrir o banco do projeto (`data/olympics.duckdb`) ou ler `raw/` dentro dos testes. Testes usam dados inventados e DuckDB em memória ou `tmp_path`.

## Ambiente

- Windows, PowerShell.
- Comandos Python sempre com `uv run`.
- Antes de rodar o pipeline, confirme que o `ui.py` não está aberto (lock do DuckDB).
