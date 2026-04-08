import streamlit as st
from datetime import date, timedelta
from services.trip_service import create_trip, get_trip, update_trip
from config import TRAVEL_ICONS, CURRENCIES


def render():
    editing_id = st.session_state.get("editing_trip_id")
    trip = get_trip(editing_id) if editing_id else None

    st.markdown("## ✈️ " + ("Editar Viagem" if trip else "Nova Viagem"))

    if trip:
        st.info(f"Editando: **{trip.name}**")

    with st.form("trip_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        name = col1.text_input(
            "Nome da viagem *",
            value=trip.name if trip else "",
            placeholder="Ex: Férias em Lisboa",
        )
        destination = col2.text_input(
            "Destino principal *",
            value=trip.destination if trip else "",
            placeholder="Ex: Lisboa",
        )

        col3, col4 = st.columns(2)
        country = col3.text_input(
            "País",
            value=trip.country if trip else "",
            placeholder="Ex: Portugal",
        )

        trip_type_options = list(TRAVEL_ICONS.keys())
        current_type = trip.trip_type if trip else "Outro"
        idx = trip_type_options.index(current_type) if current_type in trip_type_options else 0
        trip_type = col4.selectbox("Tipo de viagem", trip_type_options, index=idx)

        col5, col6 = st.columns(2)
        start_date = col5.date_input(
            "Data de ida *",
            value=trip.start_date if trip else date.today() + timedelta(days=30),
            min_value=date(2000, 1, 1),
        )
        end_date = col6.date_input(
            "Data de volta *",
            value=trip.end_date if trip else date.today() + timedelta(days=37),
            min_value=date(2000, 1, 1),
        )

        col7, col8, col9 = st.columns([2, 1, 2])
        budget = col7.number_input(
            "Orçamento total",
            min_value=0.0,
            value=float(trip.budget) if trip else 0.0,
            step=100.0,
            format="%.2f",
        )
        currency = col8.selectbox(
            "Moeda",
            CURRENCIES,
            index=CURRENCIES.index(trip.currency) if trip else 0,
        )

        status_options = ["Planejando", "Confirmada", "Em andamento", "Concluída", "Cancelada"]
        current_status = trip.status if trip else "Planejando"
        status = col9.selectbox(
            "Status",
            status_options,
            index=status_options.index(current_status),
        )

        notes = st.text_area(
            "Notas / Observações",
            value=trip.notes if trip else "",
            placeholder="Documentos necessários, dicas, lembretes...",
            height=120,
        )

        col_submit, col_cancel = st.columns([1, 5])
        submitted = col_submit.form_submit_button("💾 Salvar", use_container_width=True, type="primary")

        if submitted:
            if not name or not destination:
                st.error("Nome e destino são obrigatórios!")
            elif end_date < start_date:
                st.error("A data de volta não pode ser anterior à data de ida!")
            else:
                emoji = TRAVEL_ICONS.get(trip_type, "✈️")

                if trip:
                    update_trip(
                        trip.id,
                        name=name, destination=destination, country=country,
                        trip_type=trip_type, start_date=start_date, end_date=end_date,
                        budget=budget, currency=currency, status=status,
                        notes=notes, cover_emoji=emoji,
                    )
                    st.success("✅ Viagem atualizada com sucesso!")
                else:
                    create_trip(
                        name=name, destination=destination, start_date=start_date,
                        end_date=end_date, budget=budget, currency=currency,
                        country=country, trip_type=trip_type, notes=notes,
                        cover_emoji=emoji,
                    )
                    st.success("✅ Viagem criada com sucesso!")

                st.session_state["editing_trip_id"] = None
                st.session_state["page"] = "home"
                st.rerun()

    if trip:
        if st.button("← Cancelar edição"):
            st.session_state["editing_trip_id"] = None
            st.session_state["page"] = "home"
            st.rerun()
