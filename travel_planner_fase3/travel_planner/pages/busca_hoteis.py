import streamlit as st
from datetime import date, timedelta
from services.hotel_service import search_hotels, HotelOffer

BOARD_EMOJI = {
    "Sem café": "🛏️",
    "Café incluído": "☕",
    "Meia pensão": "🍽️",
    "Pensão completa": "🍴",
    "All inclusive": "🎉",
}

AMENITY_ICONS = {
    "SWIMMING_POOL": "🏊 Piscina",
    "SPA": "💆 Spa",
    "FITNESS_CENTER": "🏋️ Academia",
    "AIR_CONDITIONING": "❄️ Ar-cond.",
    "RESTAURANT": "🍽️ Restaurante",
    "PARKING": "🅿️ Estacionamento",
    "WIFI": "📶 Wi-Fi",
    "PETS_ALLOWED": "🐾 Aceita pets",
    "ROOM_SERVICE": "🛎️ Room service",
    "BAR": "🍸 Bar",
    "BUSINESS_CENTER": "💼 Centro negócios",
    "AIRPORT_SHUTTLE": "🚌 Transfer aeroporto",
}


def render():
    st.markdown("## 🏨 Buscar Hotéis")
    _render_search_form()

    if "hotel_results" in st.session_state and st.session_state["hotel_results"]:
        _render_results(st.session_state["hotel_results"])
    elif "hotel_error" in st.session_state and st.session_state["hotel_error"]:
        st.error(st.session_state["hotel_error"])
        _show_setup_help()


def _render_search_form():
    with st.form("hotel_search_form"):
        st.markdown("### Parâmetros de Busca")

        col1, col2 = st.columns(2)
        city_code = col1.text_input(
            "Cidade (código IATA) *",
            value=st.session_state.get("ht_city", "LIS"),
            placeholder="Ex: LIS, GRU, MCZ, SSA",
            help="Código IATA da cidade de destino",
        ).upper().strip()

        col3, col4 = st.columns(2)
        check_in = col3.date_input(
            "Check-in *",
            value=st.session_state.get("ht_cin", date.today() + timedelta(days=30)),
            min_value=date.today(),
        )
        check_out = col4.date_input(
            "Check-out *",
            value=st.session_state.get("ht_cout", date.today() + timedelta(days=37)),
            min_value=date.today() + timedelta(days=1),
        )

        col5, col6, col7 = st.columns(3)
        adults = col5.number_input("Adultos/quarto", min_value=1, max_value=4,
                                   value=st.session_state.get("ht_adults", 1))
        rooms = col6.number_input("Quartos", min_value=1, max_value=9,
                                  value=st.session_state.get("ht_rooms", 1))
        radius = col7.number_input("Raio (km)", min_value=1, max_value=50,
                                   value=st.session_state.get("ht_radius", 5))

        stars = st.multiselect(
            "Filtrar por estrelas",
            [1, 2, 3, 4, 5],
            default=st.session_state.get("ht_stars", [3, 4, 5]),
            format_func=lambda x: "⭐" * x,
        )

        submitted = st.form_submit_button("🔎 Buscar Hotéis", type="primary", use_container_width=True)

    if submitted:
        if not city_code:
            st.error("Informe o código da cidade!")
            return
        if check_out <= check_in:
            st.error("Check-out deve ser após o check-in!")
            return

        st.session_state.update({
            "ht_city": city_code, "ht_cin": check_in, "ht_cout": check_out,
            "ht_adults": adults, "ht_rooms": rooms, "ht_radius": radius,
            "ht_stars": stars, "hotel_results": None, "hotel_error": None,
        })

        nights = (check_out - check_in).days
        with st.spinner(f"Buscando hotéis em {city_code} para {nights} noite(s)... 🏨"):
            try:
                results = search_hotels(
                    city_code=city_code,
                    check_in=check_in,
                    check_out=check_out,
                    adults=adults,
                    rooms=rooms,
                    radius=radius,
                    ratings=stars if stars else None,
                )
                st.session_state["hotel_results"] = results
                if not results:
                    st.warning("Nenhum hotel disponível para os critérios informados.")
            except (ValueError, RuntimeError) as e:
                st.session_state["hotel_error"] = str(e)
        st.rerun()


def _render_results(hotels: list[HotelOffer]):
    st.divider()

    check_in  = st.session_state.get("ht_cin")
    check_out = st.session_state.get("ht_cout")
    nights = (check_out - check_in).days if check_in and check_out else 1

    st.markdown(f"### 🏨 {len(hotels)} hotel(is) disponível(is)  ·  {nights} noite(s)")

    # Filtros rápidos
    col1, col2, col3 = st.columns(3)
    max_price = col1.number_input(
        "Preço máx./noite (R$)", min_value=0.0,
        value=float(max(h.price_per_night for h in hotels)) if hotels else 9999.0,
        step=50.0,
    )
    board_options = ["Todos"] + list({h.board_type for h in hotels})
    board_filter = col2.selectbox("Regime alimentar", board_options)
    sort_by = col3.selectbox("Ordenar por", ["Menor preço/noite", "Mais estrelas", "Nome"])

    # Aplicar filtros
    filtered = [h for h in hotels if h.price_per_night <= max_price]
    if board_filter != "Todos":
        filtered = [h for h in filtered if h.board_type == board_filter]

    if sort_by == "Mais estrelas":
        filtered = sorted(filtered, key=lambda h: h.stars, reverse=True)
    elif sort_by == "Nome":
        filtered = sorted(filtered, key=lambda h: h.name)

    st.markdown(f"**{len(filtered)} resultado(s) após filtros**")
    st.divider()

    if not filtered:
        st.info("Nenhum hotel corresponde aos filtros aplicados.")
        return

    for hotel in filtered:
        _render_hotel_card(hotel, nights)


def _render_hotel_card(hotel: HotelOffer, nights: int):
    stars_str = "⭐" * hotel.stars if hotel.stars else ""
    board_icon = BOARD_EMOJI.get(hotel.board_type, "🏨")
    amenities_str = "  ".join(
        AMENITY_ICONS.get(a, "") for a in hotel.amenities if AMENITY_ICONS.get(a)
    )

    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid rgba(67,197,158,0.25);
            border-radius: 12px;
            padding: 18px 22px;
            margin-bottom: 14px;
            background: rgba(67,197,158,0.04);
        ">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px">
                <div>
                    <span style="font-size:1.1rem; font-weight:700; color:#43C59E">{hotel.name}</span>
                    <span style="margin-left:8px; font-size:0.9rem">{stars_str}</span>
                    <div style="color:#888; font-size:0.82rem; margin-top:3px">
                        📍 {hotel.city}, {hotel.country}
                    </div>
                </div>
                <div style="text-align:right">
                    <div style="font-size:1.4rem; font-weight:700; color:#4F8EF7">
                        {hotel.currency} {hotel.price_per_night:,.2f}<span style="font-size:0.75rem; color:#888">/noite</span>
                    </div>
                    <div style="color:#888; font-size:0.8rem">Total {nights} noite(s): {hotel.currency} {hotel.total_price:,.2f}</div>
                </div>
            </div>
            <div style="margin-top:10px; font-size:0.85rem; color:#aaa; display:flex; flex-wrap:wrap; gap:14px">
                <span>{board_icon} {hotel.board_type}</span>
                <span>📅 {hotel.check_in} → {hotel.check_out}</span>
                <span>🔖 {hotel.room_type or "Quarto padrão"}</span>
            </div>
            {f'<div style="margin-top:8px; font-size:0.82rem; color:#888">{amenities_str}</div>' if amenities_str else ""}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Ver detalhes"):
            col1, col2 = st.columns(2)
            col1.markdown(f"**Quarto:** {hotel.room_type or 'Padrão'}")
            col1.markdown(f"**Descrição:** {hotel.room_description or '-'}")
            col1.markdown(f"**Regime:** {hotel.board_type}")
            col2.markdown(f"**Cancelamento:** {hotel.cancellation_policy}")
            if hotel.latitude and hotel.longitude:
                col2.markdown(f"**Localização:** [{hotel.latitude:.4f}, {hotel.longitude:.4f}]")


def _show_setup_help():
    with st.expander("ℹ️ Como configurar a API Amadeus", expanded=True):
        st.markdown("""
        **Passo a passo:**
        1. Acesse [developers.amadeus.com](https://developers.amadeus.com)
        2. Crie uma conta gratuita e uma aplicação
        3. Copie **API Key** e **API Secret**
        4. No arquivo `.env`:
        ```
        AMADEUS_API_KEY=sua_chave_aqui
        AMADEUS_API_SECRET=seu_secret_aqui
        ```
        5. Reinicie o Streamlit

        > **Códigos IATA de cidades brasileiras:**
        > MCZ (Maceió), GRU (São Paulo/Guarulhos), GIG (Rio de Janeiro), SSA (Salvador),
        > REC (Recife), FOR (Fortaleza), BSB (Brasília), CWB (Curitiba), POA (Porto Alegre)
        """)
