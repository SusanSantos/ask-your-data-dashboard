"""Guarda de segurança para SQL gerado por IA: somente SELECT, tabelas em allow-list, LIMIT forçado."""
from __future__ import annotations

import re

ALLOWED_TABLES = {"sales"}
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|copy|pragma|install|load|export|call|truncate|replace)\b",
    re.IGNORECASE,
)
MAX_ROWS = 1000


class UnsafeSQL(ValueError):
    pass


def validate(sql: str) -> str:
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        raise UnsafeSQL("Múltiplos comandos não são permitidos.")
    if not re.match(r"^(select|with)\b", s, re.IGNORECASE):
        raise UnsafeSQL("Apenas consultas SELECT são permitidas.")
    if FORBIDDEN.search(s):
        raise UnsafeSQL("Comando proibido detectado.")
    if re.search(r"--|/\*", s):
        raise UnsafeSQL("Comentários SQL não são permitidos.")
    if re.search(r"\b(read_csv|read_parquet|read_json|glob|httpfs)\w*\s*\(", s, re.IGNORECASE):
        raise UnsafeSQL("Leitura de arquivos externos não é permitida.")
    ctes = {m.lower() for m in re.findall(r"\b(\w+)\s+as\s*\(", s, re.IGNORECASE)}
    tables = {t.lower() for t in re.findall(r"\b(?:from|join)\s+([a-zA-Z_][\w.]*)", s, re.IGNORECASE)}
    bad = tables - ALLOWED_TABLES - ctes
    if bad:
        raise UnsafeSQL(f"Tabela(s) não permitida(s): {', '.join(sorted(bad))}")
    if not re.search(r"\blimit\s+\d+\s*$", s, re.IGNORECASE):
        s = f"select * from ({s}) as _q limit {MAX_ROWS}"
    return s
