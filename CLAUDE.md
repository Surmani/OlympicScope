# Instruções para a IA — OlympicScope

Responda sempre em português.

## Fonte da verdade

- A especificação do projeto está em `docs/SPEC.md`. Leia antes de qualquer trabalho.
- A spec é a fonte da verdade e o código é consequência dela. Não acrescente requisito que não esteja escrito lá.
- Se algo estiver ambíguo ou não definido, pergunte antes de escrever código, apresentando as opções.
- Não invente características dos dados. Toda afirmação sobre o dado real precisa vir de uma consulta executada.

## Estado atual

Concluídas e commitadas: unidades 0.1 (estrutura uv e .gitignore), 0.2 (arquivos originais em raw/), 0.3 (README e docs/SPEC.md) e 1.1 (`pipeline/db.py` com testes).

Próxima: **unidade 2.1 — validação dos arquivos de origem**.

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
