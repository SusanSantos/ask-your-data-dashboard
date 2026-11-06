from __future__ import annotations

import duckdb
import pandas as pd

from src.guard import validate
from src.nl2sql import question_to_sql


def run_sql(db: str, sql: str) -> pd.DataFrame:
    safe = validate(sql)  # TODA consulta passa pela guarda, venha de regra, LLM ou usuário
    con = duckdb.connect(db, read_only=True)
    try:
        return con.execute(safe).df()
    finally:
        con.close()


def ask(db: str, question: str) -> tuple[pd.DataFrame, str, str]:
    sql, origin = question_to_sql(question)
    return run_sql(db, sql), sql, origin
