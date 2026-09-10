"""Cria feedback com as mesmas restrições dos modelos da API."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import engine
from models import FeedbackDB


def migrate():
    FeedbackDB.__table__.create(engine, checkfirst=True)


if __name__ == "__main__":
    migrate()
