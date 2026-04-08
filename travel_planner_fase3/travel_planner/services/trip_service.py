from datetime import date
from sqlalchemy.orm import Session, joinedload
from database.models import Trip, Expense, Itinerary
from database.db import get_session


# ─── Viagens ────────────────────────────────────────────────────────────────

def create_trip(name: str, destination: str, start_date: date, end_date: date,
                budget: float, currency: str, country: str = "",
                trip_type: str = "Outro", notes: str = "", cover_emoji: str = "✈️") -> Trip:
    db: Session = get_session()
    try:
        trip = Trip(
            name=name, destination=destination, start_date=start_date,
            end_date=end_date, budget=budget, currency=currency,
            country=country, trip_type=trip_type, notes=notes,
            cover_emoji=cover_emoji,
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        return trip
    finally:
        db.close()


def get_all_trips() -> list[Trip]:
    db: Session = get_session()
    try:
        trips = db.query(Trip).options(
            joinedload(Trip.expenses),
            joinedload(Trip.itineraries),
        ).order_by(Trip.start_date.desc()).all()
        db.expunge_all()
        return trips
    finally:
        db.close()


def get_trip(trip_id: int) -> Trip | None:
    db: Session = get_session()
    try:
        trip = db.query(Trip).options(
            joinedload(Trip.expenses),
            joinedload(Trip.itineraries),
        ).filter(Trip.id == trip_id).first()
        if trip:
            db.expunge_all()
        return trip
    finally:
        db.close()


def update_trip(trip_id: int, **kwargs) -> Trip | None:
    db: Session = get_session()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if trip:
            for key, value in kwargs.items():
                if hasattr(trip, key):
                    setattr(trip, key, value)
            db.commit()
        return trip
    finally:
        db.close()


def delete_trip(trip_id: int) -> bool:
    db: Session = get_session()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if trip:
            db.delete(trip)
            db.commit()
            return True
        return False
    finally:
        db.close()


# ─── Despesas ────────────────────────────────────────────────────────────────

def add_expense(trip_id: int, category: str, description: str,
                amount: float, currency: str, expense_date: date | None = None) -> Expense:
    db: Session = get_session()
    try:
        expense = Expense(
            trip_id=trip_id, category=category, description=description,
            amount=amount, currency=currency, expense_date=expense_date or date.today(),
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense
    finally:
        db.close()


def get_expenses(trip_id: int) -> list[Expense]:
    db: Session = get_session()
    try:
        expenses = db.query(Expense).filter(
            Expense.trip_id == trip_id
        ).order_by(Expense.expense_date.desc()).all()
        db.expunge_all()
        return expenses
    finally:
        db.close()


def delete_expense(expense_id: int) -> bool:
    db: Session = get_session()
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            db.delete(expense)
            db.commit()
            return True
        return False
    finally:
        db.close()


# ─── Itinerários ─────────────────────────────────────────────────────────────

def save_itinerary_day(trip_id: int, day_number: int, title: str,
                       content: str, date_: date | None = None) -> Itinerary:
    db: Session = get_session()
    try:
        existing = db.query(Itinerary).filter(
            Itinerary.trip_id == trip_id,
            Itinerary.day_number == day_number,
        ).first()
        if existing:
            existing.title = title
            existing.content = content
            existing.date = date_
            db.commit()
            db.refresh(existing)
            return existing
        item = Itinerary(trip_id=trip_id, day_number=day_number,
                         title=title, content=content, date=date_)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    finally:
        db.close()


def get_itinerary(trip_id: int) -> list[Itinerary]:
    db: Session = get_session()
    try:
        items = db.query(Itinerary).filter(
            Itinerary.trip_id == trip_id
        ).order_by(Itinerary.day_number).all()
        db.expunge_all()
        return items
    finally:
        db.close()
