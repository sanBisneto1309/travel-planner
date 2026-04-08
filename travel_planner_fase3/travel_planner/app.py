import streamlit as st
from database.db import init_db

st.set_page_config(
    page_title="Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 100%); }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #141824 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    div[data-testid="metric-container"] {
        background: rgba(79,142,247,0.08);
        border: 1px solid rgba(79,142,247,0.15);
        border-radius: 12px; padding: 16px;
    }
    .stButton > button {
        border-radius: 8px; font-weight: 600; transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(79,142,247,0.3);
    }
    hr { border-color: rgba(255,255,255,0.08) !important; }
    .stSelectbox > div, .stTextInput > div > div { border-radius: 8px !important; }
    div[data-testid="stExpander"] {
        border: 1px solid rgba(79,142,247,0.2) !important;
        border-radius: 12px !important;
        background: rgba(79,142,247,0.03) !important;
    }
    div[data-testid="stTabs"] button { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

init_db()

# Session state defaults
for key, val in [
    ("page", "home"),
    ("editing_trip_id", None),
    ("ai_generate", False),
    ("ai_result", None),
    ("ai_params", {}),
    ("flight_results", None),
    ("hotel_results", None),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px">
        <div style="font-size: 3rem">✈️</div>
        <div style="font-size: 1.4rem; font-weight: 700; color: #4F8EF7; letter-spacing: -0.5px">
            Travel Planner
        </div>
        <div style="font-size: 0.78rem; color: #888; margin-top: 4px">
            Organize suas aventuras
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    sections = [
        ("PLANEJAMENTO", "#4F8EF7", {
            "home":        ("🗺️", "Minhas Viagens"),
            "nova_viagem": ("➕", "Nova Viagem"),
            "orcamento":   ("💰", "Orçamento"),
        }),
        ("BUSCA", "#43C59E", {
            "busca_voos":   ("🔍", "Buscar Voos"),
            "busca_hoteis": ("🏨", "Buscar Hotéis"),
        }),
        ("INTELIGÊNCIA ARTIFICIAL", "#a78bfa", {
            "roteiro_ia": ("🤖", "Roteiro com IA"),
        }),
    ]

    for section_label, color, items in sections:
        st.markdown(
            f"<div style='color:{color}; font-size:0.72rem; font-weight:700; "
            f"padding:6px 0 4px; letter-spacing:1px'>{section_label}</div>",
            unsafe_allow_html=True,
        )
        for key, (icon, label) in items.items():
            active = st.session_state["page"] == key
            if st.button(f"{icon}  {label}", key=f"nav_{key}",
                         use_container_width=True,
                         type="primary" if active else "secondary"):
                if key != "nova_viagem":
                    st.session_state["editing_trip_id"] = None
                st.session_state["page"] = key
                st.rerun()
        st.divider()

    st.markdown("""
    <div style='color:#555; font-size:0.72rem; text-align:center; line-height:1.9'>
        ✅ Fase 1 — Base<br>
        ✅ Fase 2 — Busca<br>
        ✅ Fase 3 — IA
    </div>
    """, unsafe_allow_html=True)

# ── Roteamento ────────────────────────────────────────────────────────────────
page = st.session_state["page"]

if page == "home":
    from pages import home; home.render()
elif page == "nova_viagem":
    from pages import nova_viagem; nova_viagem.render()
elif page == "orcamento":
    from pages import orcamento; orcamento.render()
elif page == "busca_voos":
    from pages import busca_voos; busca_voos.render()
elif page == "busca_hoteis":
    from pages import busca_hoteis; busca_hoteis.render()
elif page == "roteiro_ia":
    from pages import roteiro_ia; roteiro_ia.render()
