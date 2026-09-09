import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import engine
from models import MentoriaAvaliacaoDB


if __name__ == "__main__":
    MentoriaAvaliacaoDB.__table__.create(engine, checkfirst=True)
    print("Estrutura de avaliações de mentoria preparada.")
