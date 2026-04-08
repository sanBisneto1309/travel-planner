import streamlit as st
from datetime import date
import plotly.express as px
import pandas as pd
from services.trip_service import get_all_trips, delete_trip
from config import TRAVEL_ICONS


def render():
    st.markdown("## 🗺️ Minhas Viagens")

    trips = get_all_trips()

    # ─── Métricas rápidas ────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    total = len(trips)
    planejando = sum(1 for t in trips if t.status == "Planejando")
    concluidas = sum(1 for t in trips if t.status == "Concluída")
    total_gasto = sum(t.total_spent for t in trips)

    col1.metric("Total de Viagens", total)
    col2.metric("Planejando", planejando)
    col3.metric("Concluídas", concluidas)
    col4.metric("Total Gasto", f"R$ {total_gasto:,.2f}")

    st.divider()

    # ─── Filtros ─────────────────────────────────────────────────────
    col_search, col_status, col_sort = st.columns([3, 2, 2])
    search = col_search.text_input("🔍 Buscar viagem", placeholder="Destino ou nome...")
    status_filter = col_status.selectbox("Status", ["Todos", "Planejando", "Confirmada", "Em andamento", "Concluída", "Cancelada"])
    sort_by = col_sort.selectbox("Ordenar por", ["Data (mais recente)", "Data (mais antiga)", "Nome", "Orçamento"])

    # Aplicar filtros
    filtered = trips
    if search:
        filtered = [t for t in filtered if search.lower() in t.name.lower() or search.lower() in t.destination.lower()]
    if status_filter != "Todos":
        filtered = [t for t in filtered if t.status == status_filter]

    if sort_by == "Nome":
        filtered = sorted(filtered, key=lambda t: t.name)
    elif sort_by == "Orçamento":
        filtered = sorted(filtered, key=lambda t: t.budget, reverse=True)
    elif sort_by == "Data (mais antiga)":
        filtered = sorted(filtered, key=lambda t: t.start_date)

    st.markdown(f"**{len(filtered)} viagem(ns) encontrada(s)**")
    st.divider()

    # ─── Cards de viagens ────────────────────────────────────────────
    if not filtered:
        st.info("Nenhuma viagem encontrada. Crie sua primeira viagem no menu lateral! ✈️")
        return

    for trip in filtered:
        _render_trip_card(trip)

    # ─── Gráfico de gastos ───────────────────────────────────────────
    if trips:
        st.divider()
        st.markdown("### 📊 Visão Geral de Orçamentos")
        df = pd.DataFrame([{
            "Viagem": t.name,
            "Orçamento": t.budget,
            "Gasto": t.total_spent,
        } for t in trips if t.budget > 0])

        if not df.empty:
            fig = px.bar(
                df.melt(id_vars="Viagem", var_name="Tipo", value_name="Valor"),
                x="Viagem", y="Valor", color="Tipo", barmode="group",
                color_discrete_map={"Orçamento": "#4F8EF7", "Gasto": "#F76F6F"},
                labels={"Valor": "Valor (R$)"},
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend_title_text="",
            )
            st.plotly_chart(fig, use_container_width=True)


def _render_trip_card(trip):
    status_colors = {
        "Planejando":    "#4F8EF7",
        "Confirmada":    "#43C59E",
        "Em andamento":  "#F7A84F",
        "Concluída":     "#9B9B9B",
        "Cancelada":     "#F76F6F",
    }
    color = status_colors.get(trip.status, "#ccc")
    today = date.today()
    days_to_go = (trip.start_date - today).days

    with st.container():
        st.markdown(f"""
        <div style="
            border-left: 4px solid {color};
            background: rgba(79,142,247,0.05);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:1.6rem">{trip.cover_emoji}</span>
                    <strong style="font-size:1.15rem; margin-left:8px">{trip.name}</strong>
                    <span style="
                        background:{color}22; color:{color};
                        border-radius:20px; padding:2px 10px;
                        font-size:0.78rem; margin-left:10px;
                        font-weight:600;
                    ">{trip.status}</span>
                </div>
            </div>
            <div style="margin-top:8px; color:#888; font-size:0.9rem">
                📍 {trip.destination}{f", {trip.country}" if trip.country else ""}
                &nbsp;•&nbsp; 📅 {trip.start_date.strftime("%d/%m/%Y")} → {trip.end_date.strftime("%d/%m/%Y")}
                &nbsp;•&nbsp; 🕓 {trip.duration_days} dia(s)
                {f"&nbsp;•&nbsp; ⏳ Em {days_to_go} dias" if days_to_go > 0 else ""}
            </div>
            <div style="margin-top:6px; font-size:0.88rem">
                💰 Orçamento: <strong>{trip.currency} {trip.budget:,.2f}</strong>
                &nbsp;|&nbsp; Gasto: <strong style="color:{color}">{trip.currency} {trip.total_spent:,.2f}</strong>
                &nbsp;|&nbsp; Restante: <strong>{trip.currency} {trip.budget_remaining:,.2f}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns([1, 1, 6])
        if col_a.button("✏️ Editar", key=f"edit_{trip.id}"):
            st.session_state["editing_trip_id"] = trip.id
            st.session_state["page"] = "nova_viagem"
            st.rerun()
        if col_b.button("🗑️ Excluir", key=f"del_{trip.id}"):
            delete_trip(trip.id)
            st.success(f'Viagem "{trip.name}" excluída.')
            st.rerun()
