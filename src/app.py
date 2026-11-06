"""Dashboard Streamlit: KPIs + gráficos + pergunte aos dados em linguagem natural."""
import os

import plotly.express as px
import streamlit as st

from src.data import build_db
from src.guard import UnsafeSQL
from src.query import ask, run_sql

DB = os.getenv("SALES_DB", "sales.duckdb")
if not os.path.exists(DB):
    build_db(DB)

st.set_page_config(page_title="Ask Your Data", layout="wide")
st.title("Ask Your Data — vendas")

states = run_sql(DB, "select distinct state from sales order by 1")["state"].tolist()
sel = st.sidebar.multiselect("Estado", states, default=states)
where = "state in (" + ",".join(f"'{s}'" for s in sel) + ")" if sel else "1=0"

k = run_sql(DB, f"select sum(revenue) r, count(*) o, avg(revenue) t from sales where {where}").iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Receita", f"R$ {k.r:,.0f}".replace(",", "."))
c2.metric("Pedidos", f"{int(k.o):,}".replace(",", "."))
c3.metric("Ticket médio", f"R$ {k.t:,.2f}".replace(",", "."))

m = run_sql(DB, f"select strftime(order_date,'%Y-%m') mes, sum(revenue) receita from sales where {where} group by 1 order by 1")
cat = run_sql(DB, f"select category, sum(revenue) receita from sales where {where} group by 1 order by 2 desc")
a, b = st.columns(2)
a.plotly_chart(px.line(m, x="mes", y="receita", title="Receita mensal"), use_container_width=True)
b.plotly_chart(px.bar(cat, x="category", y="receita", title="Receita por categoria"), use_container_width=True)

st.subheader("Pergunte aos dados")
q = st.text_input("Ex.: receita por estado · top 5 produtos · ticket médio")
if q:
    try:
        df, sql, origin = ask(DB, q)
        st.caption(f"Origem do SQL: {origin}")
        st.code(sql, language="sql")
        st.dataframe(df, use_container_width=True)
    except (LookupError, UnsafeSQL) as e:
        st.warning(str(e))
