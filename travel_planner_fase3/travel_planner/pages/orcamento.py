import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date
from services.trip_service import get_all_trips, get_expenses, add_expense, delete_expense
from config import CATEGORIES


def render():
    st.markdown("## 💰 Controle de Orçamento")

    trips = get_all_trips()
    if not trips:
        st.info("Crie uma viagem primeiro para registrar despesas.")
        return

    trip_options = {f"{t.cover_emoji} {t.name} ({t.destination})": t.id for t in trips}
    selected_label = st.selectbox("Selecione a viagem", list(trip_options.keys()))
    trip_id = trip_options[selected_label]
    trip = next(t for t in trips if t.id == trip_id)

    # ─── Métricas ────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Orçamento Total", f"{trip.currency} {trip.budget:,.2f}")
    col2.metric("Total Gasto", f"{trip.currency} {trip.total_spent:,.2f}")
    remaining = trip.budget_remaining
    col3.metric("Saldo Restante", f"{trip.currency} {remaining:,.2f}",
                delta=f"{remaining:+.2f}", delta_color="normal" if remaining >= 0 else "inverse")
    col4.metric("% Utilizado", f"{trip.budget_pct}%")

    # Barra de progresso
    pct = trip.budget_pct / 100
    color = "normal" if pct < 0.8 else ("warning" if pct < 1.0 else "error")
    st.progress(min(pct, 1.0), text=f"Orçamento utilizado: {trip.budget_pct}%")

    st.divider()

    # ─── Adicionar despesa ───────────────────────────────────────────
    with st.expander("➕ Adicionar Nova Despesa", expanded=False):
        with st.form("expense_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            category = col_a.selectbox("Categoria", CATEGORIES)
            exp_date = col_b.date_input("Data", value=date.today())

            description = st.text_input("Descrição *", placeholder="Ex: Jantar no restaurante XYZ")

            col_c, col_d = st.columns(2)
            amount = col_c.number_input("Valor *", min_value=0.01, step=10.0, format="%.2f")
            currency = col_d.text_input("Moeda", value=trip.currency)

            if st.form_submit_button("💾 Registrar Despesa", type="primary"):
                if not description:
                    st.error("Descrição é obrigatória!")
                else:
                    add_expense(trip_id, category, description, amount, currency, exp_date)
                    st.success("Despesa registrada! ✅")
                    st.rerun()

    st.divider()

    # ─── Gráficos ────────────────────────────────────────────────────
    expenses = get_expenses(trip_id)

    if expenses:
        col_pie, col_line = st.columns(2)

        # Gráfico de pizza por categoria
        df = pd.DataFrame([{
            "Categoria": e.category,
            "Valor": e.amount,
        } for e in expenses])

        cat_df = df.groupby("Categoria")["Valor"].sum().reset_index()
        fig_pie = px.pie(cat_df, values="Valor", names="Categoria",
                         title="Gastos por Categoria",
                         color_discrete_sequence=px.colors.qualitative.Set3)
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        col_pie.plotly_chart(fig_pie, use_container_width=True)

        # Gauge de orçamento
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=trip.total_spent,
            title={"text": f"Gasto vs Orçamento ({trip.currency})"},
            delta={"reference": trip.budget},
            gauge={
                "axis": {"range": [0, trip.budget * 1.2] if trip.budget > 0 else [0, 100]},
                "bar": {"color": "#4F8EF7"},
                "steps": [
                    {"range": [0, trip.budget * 0.7], "color": "#e8f4e8"},
                    {"range": [trip.budget * 0.7, trip.budget], "color": "#fff3e0"},
                ],
                "threshold": {
                    "line": {"color": "#F76F6F", "width": 3},
                    "thickness": 0.75,
                    "value": trip.budget,
                },
            },
        ))
        fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280)
        col_line.plotly_chart(fig_gauge, use_container_width=True)

        # ─── Tabela de despesas ──────────────────────────────────────
        st.markdown("### 📋 Histórico de Despesas")

        for exp in expenses:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 3, 1.5, 1, 0.8])
                col1.markdown(f"**{exp.category}**")
                col2.write(exp.description)
                col3.write(f"{exp.currency} {exp.amount:,.2f}")
                col4.write(exp.expense_date.strftime("%d/%m/%Y") if exp.expense_date else "-")
                if col5.button("🗑️", key=f"del_exp_{exp.id}"):
                    delete_expense(exp.id)
                    st.rerun()
    else:
        st.info("Nenhuma despesa registrada ainda. Adicione sua primeira despesa acima!")
