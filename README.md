# Ask Your Data — Dashboard com IA (NL → SQL seguro)

Dashboard Streamlit com KPIs e gráficos, mais uma caixa **"Pergunte aos dados"**: o usuário escreve em português, o sistema gera SQL, **valida** e executa em DuckDB (somente leitura).

> **EN summary:** Streamlit dashboard over DuckDB with a natural-language-to-SQL box. Questions are translated by deterministic rules first (cheap, predictable) and by an LLM (Claude, optional via `ANTHROPIC_API_KEY`) as fallback. Every query — regardless of origin — passes a SQL guard (SELECT-only, table allow-list, no comments/multi-statements/file readers, forced LIMIT) and runs on a read-only connection.

## Por que a guarda importa
SQL gerado por LLM é entrada não confiável. Aqui a segurança não depende do modelo "se comportar":
1. **Guarda sintática** (`src/guard.py`): só `SELECT`/`WITH`; bloqueia DDL/DML, `;`, comentários, `read_csv`/`attach`/`copy`, tabelas fora da allow-list; força `LIMIT 1000`.
2. **Conexão read-only** no DuckDB — segunda barreira independente.
3. **Regras antes do LLM**: perguntas comuns não gastam token nem variam de resposta.

## Como rodar
```bash
make install
make run                     # abre o dashboard
export ANTHROPIC_API_KEY=... # opcional: habilita perguntas livres
make test && make lint
```
Perguntas que funcionam sem chave: *receita por estado*, *receita por mês*, *top 5 produtos*, *ticket médio*, *quantidade por categoria*.

## Testes (14)
8 SQLs maliciosos bloqueados · LIMIT/CTE · regras · fim-a-fim · banco somente leitura · pergunta desconhecida sem chave · smoke test do app Streamlit (3 KPIs renderizam).

## Limitações
- O caminho com LLM (`llm_sql`) **não é coberto por testes automatizados** (exige chave e rede); a guarda o protege, mas a qualidade do SQL gerado não foi medida.
- Guarda baseada em regex: suficiente para este escopo; para produção, usar parser SQL (ex.: `sqlglot`) e permissões de banco por usuário.
- Dados sintéticos de uma única tabela.

## Bullets para currículo
- Construí dashboard analítico com interface de linguagem natural para SQL (LLM + regras), com camada de segurança contra SQL injection/exfiltração (guarda sintática + conexão read-only) validada por testes adversariais.
