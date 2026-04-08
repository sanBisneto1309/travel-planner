from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Cria todas as tabelas se não existirem."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Retorna uma sessão do banco de dados."""
    return SessionLocal()
