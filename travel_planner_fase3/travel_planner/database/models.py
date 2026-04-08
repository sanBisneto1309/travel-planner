from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class TripStatus(str, enum.Enum):
    PLANEJANDO = "Planejando"
    CONFIRMADA = "Confirmada"
    EM_ANDAMENTO = "Em andamento"
    CONCLUIDA = "Concluída"
    CANCELADA = "Cancelada"


class Trip(Base):
    __tablename__ = "trips"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(120), nullable=False)
    destination = Column(String(120), nullable=False)
    country     = Column(String(80))
    trip_type   = Column(String(40), default="Outro")
    status      = Column(String(30), default=TripStatus.PLANEJANDO)
    start_date  = Column(Date, nullable=False)
    end_date    = Column(Date, nullable=False)
    budget      = Column(Float, default=0.0)
    currency    = Column(String(10), default="BRL")
    notes       = Column(Text, default="")
    cover_emoji = Column(String(10), default="✈️")
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    expenses    = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    itineraries = relationship("Itinerary", back_populates="trip", cascade="all, delete-orphan")

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @property
    def total_spent(self):
        return sum(e.amount for e in self.expenses)

    @property
    def budget_remaining(self):
        return self.budget - self.total_spent

    @property
    def budget_pct(self):
        if self.budget <= 0:
            return 0
        return min(round((self.total_spent / self.budget) * 100, 1), 100)


class Expense(Base):
    __tablename__ = "expenses"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    trip_id     = Column(Integer, ForeignKey("trips.id"), nullable=False)
    category    = Column(String(50), nullable=False)
    description = Column(String(200), nullable=False)
    amount      = Column(Float, nullable=False)
    currency    = Column(String(10), default="BRL")
    expense_date = Column(Date)
    created_at  = Column(DateTime, server_default=func.now())

    trip        = relationship("Trip", back_populates="expenses")


class Itinerary(Base):
    __tablename__ = "itineraries"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    trip_id     = Column(Integer, ForeignKey("trips.id"), nullable=False)
    day_number  = Column(Integer, nullable=False)
    date        = Column(Date)
    title       = Column(String(150))
    content     = Column(Text, default="")
    created_at  = Column(DateTime, server_default=func.now())

    trip        = relationship("Trip", back_populates="itineraries")
