import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import engine
from models import AdminSessionDB, MentorSolicitacaoDB
if __name__ == "__main__":
    MentorSolicitacaoDB.__table__.create(engine, checkfirst=True)
    AdminSessionDB.__table__.create(engine, checkfirst=True)
    print("Estrutura administrativa preparada.")
