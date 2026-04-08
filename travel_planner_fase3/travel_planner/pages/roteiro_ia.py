"""
P¡gina de geraÃ§Ã£o de roteiros com IA (Claude).
"""
import streamlit as st
from datetime import date, timedelta

from services.ai_service import generate_itinerary_stream, suggest_destinations
from services.trip_service import (
    get_all_trips, get_itinerary, save_itinerary_day, get_trip,
)
from config import TRAVEL_ICONS, CURRENCIES

INTERESTS = [
    "Gastronomia", "HistÃ³ria & Cultura", "Praias", "Natureza & Trilhas",
    "Arte & Museus", "Vida Noturna", "Compras", "Fotografia",
    "Esportes de Aventura", "FamÃ­lia & CrianÃ§as", "Arquitetura",
    "Turismo Religioso", "Ecoturismo", "Vinhos & Cerveja Artesanal",
]

DIETARY = ["Nenhuma", "Vegetariano", "Vegano", "Sem glÃºten", "Sem lactose", "Halal", "Kosher"]
MOBILITY = ["Sem restriÃ§Ãµes", "Dificuldade de locomoÃ§Ã£o", "Cadeira de rodas", "Evita longas caminhadas"]


def render():
    st.markdown("## ð¤ Roteiro com IA")

    tab_gerar, tab_salvo, tab_sugerir = st.tabs([
        "â¨ Gerar Roteiro", "ð Roteiro Salvo", "ð Sugerir Destino"
    ])

    with tab_gerar:
        _tab_gerar()
    with tab_salvo:
        _tab_salvo()
    with tab_sugerir:
        _tab_sugerir()


# ââ Aba: Gerar Roteiro ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def _tab_gerar():
    st.markdown("### Configure sua viagem e deixe a IA montar seu roteiro")

    trips = get_all_trips()
    use_trip = st.toggle("Usar dados de uma viagem existente", value=bool(trips))

    trip_ref = None
    if use_trip and trips:
        trip_options = {f"{t.cover_emoji} {t.name} â {t.destination}": t.id for t in trips}
        selected = st.selectbox("Selecione a viagem", list(trip_options.keys()))
        trip_ref = get_trip(trip_options[selected])

    st.divider()

    # ââ FormulÃ¡rio ââââââââââââââââââââââââââââââââââââââââââââââââââââ
    with st.form("itinerary_form"):
        col1, col2 = st.columns(2)

        destination = col1.text_input(
            "Destino *",
            value=trip_ref.destination if trip_ref else "",
            placeholder="Ex: Lisboa, Chapada Diamantina, TÃ³quio",
        )
        country = col2.text_input(
            "PaÃ­s *",
            value=trip_ref.country if trip_ref else "",
            placeholder="Ex: Portugal, Brasil, JapÃ£o",
        )

        col3, col4 = st.columns(2)
        start_date = col3.date_input(
            "Data de inÃ­cio *",
            value=trip_ref.start_date if trip_ref else date.today() + timedelta(days=30),
            min_value=date(2000, 1, 1),
        )
        end_date = col4.date_input(
            "Data de fim *",
            value=trip_ref.end_date if trip_ref else date.today() + timedelta(days=37),
            min_value=date(2000, 1, 1),
        )

        col5, col6, col7, col8 = st.columns(4)
        budget = col5.number_input(
            "OrÃ§amento total",
            min_value=0.0,
            value=float(trip_ref.budget) if trip_ref else 5000.0,
            step=500.0, format="%.2f",
        )
        currency = col6.selectbox(
            "Moeda",
            CURRENCIES,
            index=CURRENCIES.index(trip_ref.currency) if trip_ref else 0,
        )
        adults = col7.number_input("Adultos", min_value=1, max_value=20,
                                   value=1)

        trip_type_opts = list(TRAVEL_ICONS.keys())
        curr_type = trip_ref.trip_type if trip_ref else "Cultural"
        trip_type = col8.selectbox(
            "Tipo",
            trip_type_opts,
            index=trip_type_opts.index(curr_type) if curr_type in trip_type_opts else 0,
        )

        interests = st.multiselect(
            "Interesses (selecione atÃ© 5)",
            INTERESTS,
            default=st.session_state.get("ai_interests", []),
            max_selections=5,
        )

        col9, col10 = st.columns(2)
        dietary  = col9.selectbox("RestriÃ§Ã£o alimentar", DIETARY)
        mobility = col10.selectbox("Mobilidade", MOBILITY)

        extra_notes = st.text_area(
            "ObservaÃ§Ãµes extras (opcional)",
            placeholder="Ex: com bebÃª de 1 ano, comemorando aniversÃ¡rio, preferimos hotÃ©is boutique...",
            height=80,
        )

        save_to_trip = None
        if trips:
            save_options = {"NÃ£o salvar": None}
            save_options.update({f"{t.cover_emoji} {t.name}": t.id for t in trips})
            save_label = st.selectbox(
                "Salvar roteiro na viagem:",
                list(save_options.keys()),
                index=1 if trip_ref else 0,
            )
            save_to_trip = save_options[save_label]

        submitted = st.form_submit_button(
            "â¨ Gerar Roteiro com IA", type="primary", use_container_width=True
        )

    if submitted:
        if not destination or not country:
            st.error("Destino e paÃ­s sÃ£o obrigatÃ³rios!")
            return
        if end_date < start_date:
            st.error("Data de fim deve ser apÃ³s a data de inÃ­cio!")
            return

        duration = (end_date - start_date).days + 1
        if duration > 30:
            st.warning("Para viagens longas (>30 dias), a geraÃ§Ã£o pode demorar mais.")

        st.session_state["ai_interests"] = interests
        st.session_state["ai_save_trip"] = save_to_trip
        st.session_state["ai_params"] = {
            "destination": destination, "country": country,
            "trip_type": trip_type, "start_date": start_date,
            "end_date": end_date, "budget": budget, "currency": currency,
            "adults": adults, "interests": interests,
            "dietary": dietary if dietary != "Nenhuma" else "",
            "mobility": mobility if mobility != "Sem restriÃ§Ãµes" else "",
            "extra_notes": extra_notes,
        }
        st.session_state["ai_generate"] = True
        st.rerun()

    # ââ GeraÃ§Ã£o por streaming âââââââââââââââââââââââââââââââââââââââââ
    if st.session_state.get("ai_generate"):
        params = st.session_state.get("ai_params", {})
        save_to_trip = st.session_state.get("ai_save_trip")

        st.divider()
        duration = (params["end_date"] - params["start_date"]).days + 1
        st.markdown(f"### ð Roteiro: {params['destination']}, {params['country']} Â· {duration} dias")

        info_cols = st.columns(4)
        info_cols[0].metric("DuraÃ§Ã£o", f"{duration} dias")
        info_cols[1].metric("OrÃ§amento", f"{params['currency']} {params['budget']:,.0f}")
        info_cols[2].metric("Viajantes", params['adults'])
        info_cols[3].metric("Tipo", params['trip_type'])

        st.divider()

        output_placeholder = st.empty()
        status_placeholder = st.empty()

        full_text = ""
        try:
            status_placeholder.info("ð¤ Gerando seu roteiro personalizado... Isso pode levar alguns segundos.")
            for chunk in generate_itinerary_stream(**params):
                full_text += chunk
                output_placeholder.markdown(full_text + "â")

            output_placeholder.markdown(full_text)
            status_placeholder.success("â Roteiro gerado com sucesso!")

            st.session_state["ai_result"] = full_text
            st.session_state["ai_generate"] = False

            # Salvar no banco se solicitado
            if save_to_trip:
                _save_itinerary_to_db(full_text, save_to_trip, params["start_date"])
                st.success(f"ð¾ Roteiro salvo na viagem!")

            # BotÃ£o de download
            st.download_button(
                "ð¥ Baixar roteiro (.md)",
                data=full_text,
                file_name=f"roteiro_{params['destination'].lower().replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        except ValueError as e:
            status_placeholder.error(str(e))
            _show_api_help()
        except Exception as e:
            status_placeholder.error(f"Erro ao gerar roteiro: {e}")

    elif "ai_result" in st.session_state and st.session_state["ai_result"]:
        params = st.session_state.get("ai_params", {})
        st.divider()
        st.markdown(st.session_state["ai_result"])
        st.download_button(
            "ð¥ Baixar roteiro (.md)",
            data=st.session_state["ai_result"],
            file_name=f"roteiro_{params.get('destination','viagem').lower().replace(' ','_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )


def _save_itinerary_to_db(full_text: str, trip_id: int, start_date: date):
    """Divide o roteiro em dias e salva cada um no banco."""
    lines = full_text.split("\n")
    current_day = None
    current_title = ""
    current_lines: list[str] = []

    def flush():
        if current_day is not None:
            day_date = start_date + timedelta(days=current_day - 1)
            save_itinerary_day(
                trip_id=trip_id,
                day_number=current_day,
                title=current_title,
                content="\n".join(current_lines).strip(),
                date_=day_date,
            )

    for line in lines:
        if line.startswith("### ðï¸ Dia ") or line.startswith("### Dia "):
            flush()
            current_lines = []
            parts = line.replace("### ðï¸ ", "").replace("### ", "").split("â")
            try:
                current_day = int(parts[0].replace("Dia", "").strip())
                current_title = parts[-1].strip() if len(parts) > 1 else f"Dia {current_day}"
            except (ValueError, IndexError):
                current_day = (current_day or 0) + 1
                current_title = line.strip()
        elif current_day is not None:
            current_lines.append(line)

    flush()  # salvar Ãºltimo dia


# ââ Aba: Roteiro Salvo ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def _tab_salvo():
    st.markdown("### Roteiros salvos nas suas viagens")

    trips = get_all_trips()
    if not trips:
        st.info("Nenhuma viagem encontrada. Crie uma viagem primeiro.")
        return

    trip_options = {f"{t.cover_emoji} {t.name} â {t.destination}": t.id for t in trips}
    selected = st.selectbox("Selecione a viagem", list(trip_options.keys()), key="saved_trip_sel")
    trip_id = trip_options[selected]
    trip = next(t for t in trips if t.id == trip_id)

    itinerary = get_itinerary(trip_id)

    if not itinerary:
        st.info("Nenhum roteiro salvo para esta viagem. Gere um na aba **â¨ Gerar Roteiro**.")
        return

    st.markdown(f"**{len(itinerary)} dia(s) no roteiro de {trip.destination}**")
    st.divider()

    for day in itinerary:
        date_str = day.date.strftime("%d/%m/%Y") if day.date else ""
        with st.expander(f"ðï¸ Dia {day.day_number} â {date_str} â {day.title or ''}"):
            st.markdown(day.content)

    # Download do roteiro salvo
    full = "\n\n".join(
        f"### Dia {d.day_number} â {d.date.strftime('%d/%m/%Y') if d.date else ''} â {d.title}\n\n{d.content}"
        for d in itinerary
    )
    st.download_button(
        "ð¥ Baixar roteiro completo (.md)",
        data=full,
        file_name=f"roteiro_{trip.destination.lower().replace(' ', '_')}.md",
        mime="text/markdown",
        use_container_width=True,
    )


# ââ Aba: Sugerir Destino ââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def _tab_sugerir():
    st.markdown("### NÃ£o sabe para onde ir? A IA sugere destinos para vocÃª!")

    with st.form("suggest_form"):
        preferences = st.text_area(
            "Descreva o que vocÃª procura *",
            placeholder="Ex: Quero praias tranquilas com boa gastronomia, cultura local e natureza. Prefiro destinos menos turÃ­sticos...",
            height=100,
        )
        col1, col2, col3 = st.columns(3)
        budget = col1.number_input("OrÃ§amento total (R$)", min_value=500.0,
                                   value=5000.0, step=500.0)
        currency = col2.selectbox("Moeda", CURRENCIES)
        duration = col3.number_input("DuraÃ§Ã£o (dias)", min_value=1, max_value=90,
                                     value=7)

        submitted = st.form_submit_button("ð Sugerir Destinos", type="primary",
                                          use_container_width=True)

    if submitted:
        if not preferences:
            st.error("Descreva suas preferÃªncias!")
            return

        with st.spinner("ð¤ Analisando suas preferÃªncias..."):
            try:
                result = suggest_destinations(
                    preferences=preferences,
                    budget=budget,
                    currency=currency,
                    duration_days=int(duration),
                )
                st.divider()
                st.markdown(result)
            except ValueError as e:
                st.error(str(e))
                _show_api_help()
            except Exception as e:
                st.error(f"Erro: {e}")


# ââ Helper ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def _show_api_help():
    with st.expander("â¹ï¸ Como configurar a API da Anthropic", expanded=True):
        st.markdown("""
        **Passo a passo:**
        1. Acesse [console.anthropic.com](https://console.anthropic.com) e crie uma conta
        2. VÃ¡ em **API Keys** â crie uma nova chave
        3. No arquivo `.env` do projeto:
        ```
        ANTHROPIC_API_KEY=sk-ant-...
        ```
        4. Reinicie o Streamlit

        > Novos usuÃ¡rios recebem crÃ©ditos gratuitos para testes.
        """)
