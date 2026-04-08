"""
Serviço de geração de roteiros de viagem usando a API da Anthropic (Claude).
Suporta streaming para exibição em tempo real no Streamlit.
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Generator, Optional
import os

import anthropic

from config import ANTHROPIC_API_KEY


def _get_client() -> anthropic.Anthropic:
    key = ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY não configurado no arquivo .env")
    return anthropic.Anthropic(api_key=key)


# ── Prompt principal ──────────────────────────────────────────────────────────

def _build_prompt(
    destination: str,
    country: str,
    trip_type: str,
    start_date: date,
    end_date: date,
    budget: float,
    currency: str,
    adults: int,
    interests: list[str],
    dietary: str,
    mobility: str,
    extra_notes: str,
) -> str:
    duration = (end_date - start_date).days + 1
    interests_str = ", ".join(interests) if interests else "geral"
    date_list = [
        (start_date + timedelta(days=i)).strftime("%d/%m/%Y (%A)")
        for i in range(duration)
    ]

    return f"""Você é um especialista em planejamento de viagens com profundo conhecimento de {destination}, {country}.

Crie um roteiro de viagem COMPLETO, DETALHADO e PRÁTICO para:

**DESTINO:** {destination}, {country}
**TIPO DE VIAGEM:** {trip_type}
**PERÍODO:** {start_date.strftime("%d/%m/%Y")} até {end_date.strftime("%d/%m/%Y")} ({duration} dias)
**ORÇAMENTO TOTAL:** {currency} {budget:,.2f} para {adults} pessoa(s)
**ORÇAMENTO/PESSOA/DIA:** {currency} {budget / adults / duration:,.2f}
**INTERESSES:** {interests_str}
**RESTRIÇÃO ALIMENTAR:** {dietary or "Nenhuma"}
**MOBILIDADE:** {mobility or "Sem restrições"}
**OBSERVAÇÕES:** {extra_notes or "Nenhuma"}

**DATAS DO ROTEIRO:**
{chr(10).join(f"- Dia {i+1}: {d}" for i, d in enumerate(date_list))}

---

## ESTRUTURA OBRIGATÓRIA DO ROTEIRO

Para cada dia, siga EXATAMENTE este formato:

### 🗓️ Dia [N] — [Data] — [Título do Dia]

**🌅 Manhã**
- [Atividade detalhada com horário sugerido, endereço/bairro e dica prática]
- [Segunda atividade se houver]

**☀️ Tarde**
- [Atividade detalhada]

**🌙 Noite**
- [Atividade/Jantar com sugestão de restaurante local e faixa de preço]

**💡 Dicas do Dia**
- [Dica de transporte local, ingressos antecipados, reservas necessárias, etc.]

**💰 Estimativa de Gastos do Dia**
- Alimentação: {currency} [valor estimado]
- Transporte: {currency} [valor estimado]
- Atrações: {currency} [valor estimado]
- **Total do Dia: {currency} [soma]**

---

Após todos os dias, inclua:

## 📋 Resumo Financeiro da Viagem
- Custo estimado total por pessoa
- Custo estimado total da viagem
- Dicas para economizar

## 🎒 O Que Levar
- Lista prática de itens essenciais para este destino e época

## 🚨 Informações Importantes
- Documentos necessários
- Vacinas recomendadas (se aplicável)
- Segurança e dicas locais
- Melhor época para visitar

## 📱 Apps e Recursos Úteis
- Apps de transporte, tradução, mapas específicos para o destino

Seja ESPECÍFICO: use nomes reais de restaurantes, museus, praias, bairros. Evite sugestões genéricas.
Adapte o ritmo do roteiro ao tipo de viagem: {trip_type}.
Priorize experiências autênticas e locais dentro do orçamento informado.
"""


# ── Geração com streaming ─────────────────────────────────────────────────────

def generate_itinerary_stream(
    destination: str,
    country: str,
    trip_type: str,
    start_date: date,
    end_date: date,
    budget: float,
    currency: str,
    adults: int = 1,
    interests: Optional[list[str]] = None,
    dietary: str = "",
    mobility: str = "",
    extra_notes: str = "",
) -> Generator[str, None, None]:
    """
    Gera roteiro de viagem via streaming.
    Yields chunks de texto conforme a IA responde.
    """
    client = _get_client()
    prompt = _build_prompt(
        destination=destination,
        country=country,
        trip_type=trip_type,
        start_date=start_date,
        end_date=end_date,
        budget=budget,
        currency=currency,
        adults=adults,
        interests=interests or [],
        dietary=dietary,
        mobility=mobility,
        extra_notes=extra_notes,
    )

    with client.messages.stream(
        model="claude-opus-4-5",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
        system=(
            "Você é um guia de viagens experiente e apaixonado. "
            "Sempre responde em português brasileiro com formatação Markdown clara. "
            "Suas sugestões são práticas, específicas e consideram o orçamento do viajante."
        ),
    ) as stream:
        for text in stream.text_stream:
            yield text


def generate_itinerary(
    destination: str,
    country: str,
    trip_type: str,
    start_date: date,
    end_date: date,
    budget: float,
    currency: str,
    adults: int = 1,
    interests: Optional[list[str]] = None,
    dietary: str = "",
    mobility: str = "",
    extra_notes: str = "",
) -> str:
    """Versão sem streaming — retorna o roteiro completo como string."""
    return "".join(generate_itinerary_stream(
        destination=destination, country=country, trip_type=trip_type,
        start_date=start_date, end_date=end_date, budget=budget,
        currency=currency, adults=adults, interests=interests,
        dietary=dietary, mobility=mobility, extra_notes=extra_notes,
    ))


# ── Sugestão rápida de destino ────────────────────────────────────────────────

def suggest_destinations(
    preferences: str,
    budget: float,
    currency: str,
    duration_days: int,
) -> str:
    """Sugere destinos baseado em preferências, orçamento e duração."""
    client = _get_client()
    prompt = (
        f"Sugira 5 destinos de viagem ideais considerando:\n"
        f"- Preferências: {preferences}\n"
        f"- Orçamento: {currency} {budget:,.2f} total\n"
        f"- Duração: {duration_days} dias\n\n"
        "Para cada destino, forneça:\n"
        "1. Nome do destino e país\n"
        "2. Por que é ideal para este perfil\n"
        "3. Estimativa de custo total\n"
        "4. Melhor época para visitar\n"
        "5. Uma dica exclusiva\n\n"
        "Responda em português brasileiro com formatação Markdown."
    )
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
