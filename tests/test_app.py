from pathlib import Path

import duckdb
import pytest

from src.data import build_db
from src.guard import UnsafeSQL, validate
from src.nl2sql import rule_based
from src.query import ask, run_sql


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    return build_db(str(tmp_path_factory.mktemp("d") / "s.duckdb"), n=500)


@pytest.mark.parametrize("bad", [
    "drop table sales",
    "select * from sales; drop table sales",
    "select * from users",
    "delete from sales",
    "select * from read_csv('/etc/passwd')",
    "select 1 -- x",
    "copy sales to 'x.csv'",
    "attach 'other.db'",
])
def test_guard_blocks_unsafe(bad):
    with pytest.raises(UnsafeSQL):
        validate(bad)


def test_guard_adds_limit_and_allows_cte():
    assert "limit 1000" in validate("select * from sales")
    assert validate("with a as (select * from sales) select * from a").lower().startswith("select * from (with")


def test_rules_cover_questions():
    assert rule_based("Qual a receita por estado?")
    assert "limit 3" in rule_based("top 3 produtos")
    assert rule_based("qual a cor do céu") is None


def test_ask_end_to_end(db):
    df, _sql, origin = ask(db, "receita por categoria")
    assert origin == "regras" and len(df) == 5
    assert df["receita"].is_monotonic_decreasing


def test_db_is_read_only(db):
    run_sql(db, "select 1")  # consulta válida funciona
    with pytest.raises(duckdb.Error):
        duckdb.connect(db, read_only=True).execute("delete from sales")


def test_unknown_question_without_llm(db, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LookupError):
        ask(db, "qual a cor do céu")


def test_streamlit_app_smoke(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("SALES_DB", str(tmp_path / "s.duckdb"))
    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "src" / "app.py"), default_timeout=60).run()
    assert not at.exception
    assert len(at.metric) == 3
