from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

STATES = ["SC", "PR", "CE", "SP", "PE"]
CATS = ["eletronicos", "moda", "casa", "livros", "esportes"]


def build_db(path: str = "sales.duckdb", n: int = 6000, seed: int = 3) -> str:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(
        {
            "order_date": pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 540, n), unit="D"),
            "state": rng.choice(STATES, n, p=[0.25, 0.25, 0.2, 0.2, 0.1]),
            "category": rng.choice(CATS, n),
            "product": [f"Produto {i}" for i in rng.integers(1, 41, n)],
            "quantity": rng.integers(1, 5, n),
            "unit_price": rng.uniform(20, 900, n).round(2),
        }
    )
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    con = duckdb.connect(path)
    con.execute("create or replace table sales as select * from df")
    con.close()
    return path
