import streamlit as st
from datetime import date, timedelta
from services.flight_service import search_flights, format_duration, FlightOffer

CABINS = ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]
CABIN_LABELS = {
    "ECONOMY": "Econômica",
    "PREMIUM_ECONOMY": "Econômica Premium",
    "BUSINESS": "Executiva",
    "FIRST": "Primeira Classe",
}
AIRLINE_NAMES = {
    "LA": "LATAM", "G3": "Gol", "AD": "Azul", "TP": "TAP",
    "AA": "American", "UA": "United", "DL": "Delta", "IB": "Iberia",
    "BA": "British Airways", "AF": "Air France", "KL": "KLM",
    "LH": "Lufthansa", "EK": "Emirates", "QR": "Qatar Airways",
}

def render():
    st.markdown("## 🔍 Buscar Voos")

    _render_search_form()

    if "flight_results" in st.session_state and st.session_state["flight_results"]:
        _render_results(st.session_state["flight_results"])
    elif "flight_error" in st.session_state and st.session_state["flight_error"]:
        st.error(st.session_state["flight_error"])
        _show_setup_help()


def _render_search_form():
    with st.form("flight_search_form"):
        st.markdown("### Parâmetros de Busca")

        col1, col2 = st.columns(2)
        origin = col1.text_input(
            "Origem (código IATA) *",
            value=st.session_state.get("fl_origin", "MCZ"),
            placeholder="Ex: GRU, MCZ, SSA",
            help="Código IATA do aeroporto de origem",
        ).upper().strip()
        destination = col2.text_input(
            "Destino (código IATA) *",
            value=st.session_state.get("fl_dest", "LIS"),
            placeholder="Ex: LIS, GRU, CDG",
            help="Código IATA do aeroporto de destino",
        ).upper().strip()

        col3, col4 = st.columns(2)
        dep_date = col3.date_input(
            "Data de ida *",
            value=st.session_state.get("fl_dep", date.today() + timedelta(days=30)),
            min_value=date.today(),
        )
        ret_date = col4.date_input(
            "Data de volta (opcional)",
            value=st.session_state.get("fl_ret", None),
            min_value=date.today(),
        )

        col5, col6, col7, col8 = st.columns(4)
        adults = col5.number_input("Adultos", min_value=1, max_value=9,
                                   value=st.session_state.get("fl_adults", 1))
        cabin_idx = CABINS.index(st.session_state.get("fl_cabin", "ECONOMY"))
        cabin = col6.selectbox("Classe", [CABIN_LABELS[c] for c in CABINS], index=cabin_idx)
        cabin_code = CABINS[[CABIN_LABELS[c] for c in CABINS].index(cabin)]

        non_stop = col7.checkbox("Somente diretos", value=st.session_state.get("fl_nonstop", False))
        max_res  = col8.number_input("Máx. resultados", min_value=5, max_value=50,
                                     value=st.session_state.get("fl_max", 15))

        submitted = st.form_submit_button("🔎 Buscar Voos", type="primary", use_container_width=True)

    if submitted:
        if not origin or not destination:
            st.error("Informe origem e destino!")
            return

        # Guardar parâmetros
        st.session_state.update({
            "fl_origin": origin, "fl_dest": destination,
            "fl_dep": dep_date, "fl_ret": ret_date,
            "fl_adults": adults, "fl_cabin": cabin_code,
            "fl_nonstop": non_stop, "fl_max": max_res,
            "flight_results": None, "flight_error": None,
        })

        with st.spinner("Buscando voos... ✈️"):
            try:
                results = search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=dep_date,
                    return_date=ret_date if ret_date and ret_date > dep_date else None,
                    adults=adults,
                    travel_class=cabin_code,
                    max_results=int(max_res),
                    non_stop=non_stop,
                )
                st.session_state["flight_results"] = results
                if not results:
                    st.warning("Nenhum voo encontrado para os critérios informados.")
            except (ValueError, RuntimeError) as e:
                st.session_state["flight_error"] = str(e)
        st.rerun()


def _render_results(offers: list[FlightOffer]):
    st.divider()
    st.markdown(f"### ✈️ {len(offers)} voo(s) encontrado(s)")

    # Filtros laterais inline
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    max_price = col_filter1.number_input(
        "Preço máximo (R$)", min_value=0.0,
        value=float(max(o.price for o in offers)) if offers else 9999.0,
        step=100.0,
    )
    stop_options = ["Todos", "Direto", "1 parada", "2+ paradas"]
    stop_filter = col_filter2.selectbox("Paradas", stop_options)
    sort_by = col_filter3.selectbox("Ordenar", ["Menor preço", "Menor duração", "Menos paradas"])

    # Aplicar filtros
    filtered = [o for o in offers if o.price <= max_price]
    if stop_filter == "Direto":
        filtered = [o for o in filtered if o.stops == 0]
    elif stop_filter == "1 parada":
        filtered = [o for o in filtered if o.stops == 1]
    elif stop_filter == "2+ paradas":
        filtered = [o for o in filtered if o.stops >= 2]

    if sort_by == "Menor duração":
        filtered = sorted(filtered, key=lambda o: o.total_duration)
    elif sort_by == "Menos paradas":
        filtered = sorted(filtered, key=lambda o: o.stops)

    st.markdown(f"**{len(filtered)} resultado(s) após filtros**")
    st.divider()

    if not filtered:
        st.info("Nenhum voo corresponde aos filtros aplicados.")
        return

    for offer in filtered:
        _render_flight_card(offer)


def _render_flight_card(offer: FlightOffer):
    stops_label = "✅ Direto" if offer.stops == 0 else f"🔄 {offer.stops} parada(s)"
    carrier = AIRLINE_NAMES.get(offer.validating_carrier, offer.validating_carrier)
    dur = format_duration(offer.total_duration)

    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid rgba(79,142,247,0.25);
            border-radius: 12px;
            padding: 18px 22px;
            margin-bottom: 14px;
            background: rgba(79,142,247,0.04);
        ">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px">
                <div>
                    <span style="font-size:1.1rem; font-weight:700; color:#4F8EF7">{carrier or "Cia Aérea"}</span>
                    <span style="color:#888; font-size:0.85rem; margin-left:10px">{" · ".join(s.carrier_code+s.flight_number for s in offer.segments)}</span>
                </div>
                <div style="text-align:right">
                    <div style="font-size:1.5rem; font-weight:700; color:#43C59E">{offer.currency} {offer.price:,.2f}</div>
                    <div style="color:#888; font-size:0.78rem">{offer.price_per_traveler:,.2f} por passageiro</div>
                </div>
            </div>
            <div style="margin-top:10px; display:flex; gap:20px; flex-wrap:wrap; font-size:0.88rem; color:#aaa">
                <span>⏱ {dur}</span>
                <span>{stops_label}</span>
                <span>💺 {offer.seats_available} assento(s)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Ver detalhes dos segmentos"):
            for i, seg in enumerate(offer.segments, 1):
                dep_time = seg.departure[11:16] if len(seg.departure) >= 16 else seg.departure
                arr_time = seg.arrival[11:16] if len(seg.arrival) >= 16 else seg.arrival
                dep_date = seg.departure[:10] if seg.departure else ""
                col1, col2, col3, col4 = st.columns([2, 1, 2, 2])
                col1.markdown(f"**{seg.origin}** `{dep_time}`\n\n{dep_date}")
                col2.markdown(f"→\n\n{format_duration(seg.duration)}")
                col3.markdown(f"**{seg.destination}** `{arr_time}`")
                col4.markdown(f"✈ `{seg.carrier_code}{seg.flight_number}` · {seg.cabin or 'ECO'} · ✈ {seg.aircraft}")
                if i < len(offer.segments):
                    st.divider()


def _show_setup_help():
    with st.expander("ℹ️ Como configurar a API Amadeus", expanded=True):
        st.markdown("""
        **Passo a passo:**
        1. Acesse [developers.amadeus.com](https://developers.amadeus.com) e crie uma conta gratuita
        2. Crie uma aplicação → copie **API Key** e **API Secret**
        3. No arquivo `.env` do projeto, preencha:
        ```
        AMADEUS_API_KEY=sua_chave_aqui
        AMADEUS_API_SECRET=seu_secret_aqui
        ```
        4. Reinicie o Streamlit

        > O plano gratuito (test) possui todas as funcionalidades e dados reais de voos.
        """)
