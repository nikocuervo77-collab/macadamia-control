import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Si existe DATABASE_URL en .env usar esa (Postgres), si no, usar SQLite local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./macadamia.db")

# Ajuste para Render/Supabase que a veces usan 'postgres://' en vez de 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
