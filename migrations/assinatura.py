"""Cria a estrutura de assinaturas demonstrativas sem cobranças reais."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import engine
from models import AssinaturaDB


if __name__ == "__main__":
    AssinaturaDB.__table__.create(engine, checkfirst=True)
    print("Estrutura de assinaturas demonstrativas preparada.")
