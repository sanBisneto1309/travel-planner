"""
Serviço de busca de voos via Amadeus API.
Documentação: https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search
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
class FlightSegment:
    origin: str
    destination: str
    departure: str          # ISO datetime string
    arrival: str
    carrier_code: str
    flight_number: str
    aircraft: str
    duration: str
    cabin: str


@dataclass
class FlightOffer:
    offer_id: str
    price: float
    currency: str
    seats_available: int
    total_duration: str
    segments: list[FlightSegment] = field(default_factory=list)
    stops: int = 0
    validating_carrier: str = ""
    price_per_traveler: float = 0.0
    taxes: float = 0.0


def _get_client() -> "Client":
    if not AMADEUS_AVAILABLE:
        raise RuntimeError("Biblioteca 'amadeus' não instalada. Execute: pip install amadeus")
    key    = AMADEUS_API_KEY or os.getenv("AMADEUS_API_KEY", "")
    secret = AMADEUS_API_SECRET or os.getenv("AMADEUS_API_SECRET", "")
    if not key or not secret:
        raise ValueError("AMADEUS_API_KEY e AMADEUS_API_SECRET devem estar configurados no .env")
    return Client(client_id=key, client_secret=secret)


def search_flights(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: Optional[date] = None,
    adults: int = 1,
    travel_class: str = "ECONOMY",
    max_results: int = 10,
    currency_code: str = "BRL",
    non_stop: bool = False,
) -> list[FlightOffer]:
    """
    Busca ofertas de voos na Amadeus API.

    Args:
        origin:          Código IATA de origem (ex: "MCZ")
        destination:     Código IATA de destino (ex: "LIS")
        departure_date:  Data de ida
        return_date:     Data de volta (None = só ida)
        adults:          Nº de passageiros adultos
        travel_class:    ECONOMY | PREMIUM_ECONOMY | BUSINESS | FIRST
        max_results:     Máximo de ofertas retornadas (1-250)
        currency_code:   Moeda para exibição de preços
        non_stop:        Se True, retorna somente voos diretos

    Returns:
        Lista de FlightOffer ordenada por preço.
    """
    client = _get_client()

    params: dict = {
        "originLocationCode":      origin.upper(),
        "destinationLocationCode": destination.upper(),
        "departureDate":           departure_date.isoformat(),
        "adults":                  adults,
        "travelClass":             travel_class,
        "max":                     max_results,
        "currencyCode":            currency_code,
    }
    if return_date:
        params["returnDate"] = return_date.isoformat()
    if non_stop:
        params["nonStop"] = "true"

    try:
        response = client.shopping.flight_offers_search.get(**params)
    except ResponseError as e:
        raise RuntimeError(f"Erro na API Amadeus: {e.response.body}") from e

    offers: list[FlightOffer] = []
    for raw in response.data:
        price_info  = raw.get("price", {})
        total_price = float(price_info.get("grandTotal", price_info.get("total", 0)))
        taxes       = float(price_info.get("taxes", 0)) if price_info.get("taxes") else 0.0
        currency    = price_info.get("currency", currency_code)
        seats       = raw.get("numberOfBookableSeats", 0)
        val_carrier = (raw.get("validatingAirlineCodes") or [""])[0]

        itineraries = raw.get("itineraries", [])
        all_segs: list[FlightSegment] = []
        stops = 0
        total_dur = itineraries[0].get("duration", "") if itineraries else ""

        for itin in itineraries:
            segs = itin.get("segments", [])
            stops += max(0, len(segs) - 1)
            for s in segs:
                dep = s.get("departure", {})
                arr = s.get("arrival", {})
                cabin = ""
                # pegar cabin da primeira traveler pricing se disponível
                for tp in raw.get("travelerPricings", []):
                    for fd in tp.get("fareDetailsBySegment", []):
                        if fd.get("segmentId") == s.get("id"):
                            cabin = fd.get("cabin", "")
                all_segs.append(FlightSegment(
                    origin=dep.get("iataCode", ""),
                    destination=arr.get("iataCode", ""),
                    departure=dep.get("at", ""),
                    arrival=arr.get("at", ""),
                    carrier_code=s.get("carrierCode", ""),
                    flight_number=s.get("number", ""),
                    aircraft=s.get("aircraft", {}).get("code", ""),
                    duration=s.get("duration", ""),
                    cabin=cabin,
                ))

        per_traveler = total_price / adults if adults else total_price

        offers.append(FlightOffer(
            offer_id=raw.get("id", ""),
            price=total_price,
            currency=currency,
            seats_available=seats,
            total_duration=total_dur,
            segments=all_segs,
            stops=stops,
            validating_carrier=val_carrier,
            price_per_traveler=per_traveler,
            taxes=taxes,
        ))

    return sorted(offers, key=lambda o: o.price)


def get_airport_suggestions(keyword: str) -> list[dict]:
    """Busca aeroportos/cidades pelo nome ou código IATA."""
    client = _get_client()
    try:
        resp = client.reference_data.locations.get(
            keyword=keyword,
            subType="AIRPORT,CITY",
        )
        return [
            {
                "iata":    loc.get("iataCode", ""),
                "name":    loc.get("name", ""),
                "city":    loc.get("address", {}).get("cityName", ""),
                "country": loc.get("address", {}).get("countryName", ""),
                "label":   f"{loc.get('iataCode','')} – {loc.get('name','')} ({loc.get('address',{}).get('cityName','')})",
            }
            for loc in resp.data
        ]
    except ResponseError:
        return []


def format_duration(iso_duration: str) -> str:
    """Converte PT2H30M → 2h 30min."""
    if not iso_duration:
        return "-"
    iso_duration = iso_duration.replace("PT", "")
    result = ""
    if "H" in iso_duration:
        h, rest = iso_duration.split("H")
        result += f"{h}h "
        iso_duration = rest
    if "M" in iso_duration:
        m = iso_duration.replace("M", "")
        result += f"{m}min"
    return result.strip() or iso_duration
