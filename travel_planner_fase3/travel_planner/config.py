import os
from dotenv import load_dotenv

load_dotenv()

AMADEUS_API_KEY     = os.getenv("AMADEUS_API_KEY", "")
AMADEUS_API_SECRET  = os.getenv("AMADEUS_API_SECRET", "")
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
DATABASE_URL        = os.getenv("DATABASE_URL", "sqlite:///travel_planner.db")

CURRENCIES = ["BRL", "USD", "EUR", "GBP", "ARS", "CLP", "PEN", "COP"]
CATEGORIES = ["Passagem", "Hospedagem", "Alimentação", "Transporte", "Passeios", "Compras", "Outros"]

TRAVEL_ICONS = {
    "Praia":     "🏖️",
    "Montanha":  "⛰️",
    "Cidade":    "🏙️",
    "Campo":     "🌿",
    "Cultural":  "🏛️",
    "Aventura":  "🧗",
    "Cruzeiro":  "🚢",
    "Outro":     "✈️",
}
