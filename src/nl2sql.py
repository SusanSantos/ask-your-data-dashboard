"""Pergunta (PT-BR) -> SQL. LLM opcional (ANTHROPIC_API_KEY) com fallback determinístico por regras."""
from __future__ import annotations

import os
import re

SCHEMA = """tabela sales(order_date DATE, state VARCHAR, category VARCHAR, product VARCHAR,
quantity INT, unit_price DOUBLE, revenue DOUBLE)"""

_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"ticket m[ée]dio|valor m[ée]dio"), "select round(avg(revenue),2) as ticket_medio from sales"),
    (re.compile(r"receita.*(m[eê]s|mensal)"),
     "select strftime(order_date,'%Y-%m') as mes, round(sum(revenue),2) as receita from sales group by 1 order by 1"),
    (re.compile(r"receita.*(categoria)"),
     "select category, round(sum(revenue),2) as receita from sales group by 1 order by 2 desc"),
    (re.compile(r"receita.*(estado|uf)"),
     "select state, round(sum(revenue),2) as receita from sales group by 1 order by 2 desc"),
    (re.compile(r"(top|maiores|melhores).*produtos?"),
     "select product, round(sum(revenue),2) as receita from sales group by 1 order by 2 desc limit {n}"),
    (re.compile(r"quantidade.*(categoria)"),
     "select category, sum(quantity) as unidades from sales group by 1 order by 2 desc"),
    (re.compile(r"receita total|faturamento total|quanto vendemos"),
     "select round(sum(revenue),2) as receita_total from sales"),
]


def rule_based(question: str) -> str | None:
    q = question.lower()
    m = re.search(r"\b(\d{1,2})\b", q)
    n = int(m.group(1)) if m else 5
    for pat, sql in _RULES:
        if pat.search(q):
            return sql.format(n=n)
    return None


def llm_sql(question: str) -> str:  # pragma: no cover - requer chave e rede
    import anthropic

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.getenv("NL2SQL_MODEL", "claude-sonnet-5-5"),
        max_tokens=400,
        system=f"Converta a pergunta em UMA consulta DuckDB SELECT. Schema: {SCHEMA}. Responda só o SQL.",
        messages=[{"role": "user", "content": question}],
    )
    return re.sub(r"^```(?:sql)?|```$", "", msg.content[0].text.strip(), flags=re.MULTILINE).strip()


def question_to_sql(question: str) -> tuple[str, str]:
    """Retorna (sql, origem). Regras primeiro (barato, previsível); LLM se houver chave."""
    sql = rule_based(question)
    if sql:
        return sql, "regras"
    if os.getenv("ANTHROPIC_API_KEY"):
        return llm_sql(question), "llm"
    raise LookupError("Não entendi a pergunta (sem chave de LLM configurada para perguntas livres).")
