"""
Serviço de busca de hotéis via Amadeus API.
Documentação: https://developers.amadeus.com/self-service/category/hotels
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import os

try:
    from amadeus import Client, ResponseError
    AMADEUS_AVAILABLE = True
except ImportError:
    AMADEUS_AVAILABLE = False

from config import AMADEUS_API_KEY, AMADEUS_API_SECRET


@dataclass
class HotelOffer:
    hotel_id: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    stars: int
    rating: Optional[float]
    price_per_night: float
    total_price: float
    currency: str
    room_type: str
    room_description: str
    board_type: str          # RO, BB, HB, FB, AI
    cancellation_policy: str
    check_in: str
    check_out: str
    available: bool = True
    amenities: list[str] = field(default_factory=list)


def _get_client() -> "Client":
    if not AMADEUS_AVAILABLE:
        raise RuntimeError("Biblioteca 'amadeus' não instalada.")
    key    = AMADEUS_API_KEY or os.getenv("AMADEUS_API_KEY", "")
    secret = AMADEUS_API_SECRET or os.getenv("AMADEUS_API_SECRET", "")
    if not key or not secret:
        raise ValueError("AMADEUS_API_KEY e AMADEUS_API_SECRET devem estar configurados no .env")
    return Client(client_id=key, client_secret=secret)


def _board_label(code: str) -> str:
    return {
        "ROOM_ONLY": "Sem café",
        "BREAKFAST": "Café incluído",
        "HALF_BOARD": "Meia pensão",
        "FULL_BOARD": "Pensão completa",
        "ALL_INCLUSIVE": "All inclusive",
    }.get(code, code or "-")


def search_hotels(
    city_code: str,
    check_in: date,
    check_out: date,
    adults: int = 1,
    rooms: int = 1,
    currency: str = "BRL",
    radius: int = 5,
    ratings: Optional[list[int]] = None,
    max_results: int = 20,
) -> list[HotelOffer]:
    """
    Busca ofertas de hotéis para uma cidade.

    Args:
        city_code:   Código IATA da cidade (ex: "LIS", "GRU", "MCZ")
        check_in:    Data de check-in
        check_out:   Data de check-out
        adults:      Nº de adultos por quarto
        rooms:       Nº de quartos
        currency:    Moeda para exibição
        radius:      Raio de busca em km do centro
        ratings:     Filtro de estrelas (ex: [3, 4, 5])
        max_results: Máximo de hotéis retornados

    Returns:
        Lista de HotelOffer ordenada por preço por noite.
    """
    client = _get_client()
    nights = (check_out - check_in).days or 1

    # 1. Buscar lista de hotéis na cidade
    hotel_params: dict = {
        "cityCode": city_code.upper(),
        "radius":   radius,
        "radiusUnit": "KM",
        "hotelSource": "ALL",
    }
    if ratings:
        hotel_params["ratings"] = ",".join(str(r) for r in ratings)

    try:
        hotels_resp = client.reference_data.locations.hotels.by_city.get(**hotel_params)
    except ResponseError as e:
        raise RuntimeError(f"Erro ao buscar hotéis: {e.response.body}") from e

    hotel_ids = [h.get("hotelId") for h in hotels_resp.data[:50] if h.get("hotelId")]
    if not hotel_ids:
        return []

    # 2. Buscar disponibilidade e preços
    try:
        offers_resp = client.shopping.hotel_offers_search.get(
            hotelIds=",".join(hotel_ids[:20]),   # API limita ~20 por chamada
            checkInDate=check_in.isoformat(),
            checkOutDate=check_out.isoformat(),
            adults=adults,
            roomQuantity=rooms,
            currency=currency,
            bestRateOnly="true",
        )
    except ResponseError as e:
        raise RuntimeError(f"Erro ao buscar disponibilidade: {e.response.body}") from e

    results: list[HotelOffer] = []
    for item in offers_resp.data[:max_results]:
        hotel = item.get("hotel", {})
        offers = item.get("offers", [])
        if not offers:
            continue

        offer = offers[0]
        price_info  = offer.get("price", {})
        total       = float(price_info.get("total", price_info.get("base", 0)))
        per_night   = round(total / nights, 2)
        cur         = price_info.get("currency", currency)

        room         = offer.get("room", {})
        room_type    = room.get("typeEstimated", {}).get("category", "")
        room_desc    = room.get("description", {}).get("text", "")[:120]
        board_raw    = offer.get("boardType", "")
        board        = _board_label(board_raw)

        policies     = offer.get("policies", {})
        cancel_raw   = policies.get("cancellations", [{}])
        cancel_desc  = cancel_raw[0].get("description", {}).get("text", "Consulte o hotel") if cancel_raw else "Consulte o hotel"

        geo = hotel.get("location", {})
        results.append(HotelOffer(
            hotel_id=hotel.get("hotelId", ""),
            name=hotel.get("name", "Hotel"),
            city=hotel.get("cityCode", city_code),
            country=hotel.get("countryCode", ""),
            latitude=float(geo.get("latitude", 0)),
            longitude=float(geo.get("longitude", 0)),
            stars=int(hotel.get("rating", 0) or 0),
            rating=None,
            price_per_night=per_night,
            total_price=total,
            currency=cur,
            room_type=room_type,
            room_description=room_desc,
            board_type=board,
            cancellation_policy=cancel_desc[:100],
            check_in=check_in.isoformat(),
            check_out=check_out.isoformat(),
            amenities=hotel.get("amenities", [])[:8],
        ))

    return sorted(results, key=lambda h: h.price_per_night)
