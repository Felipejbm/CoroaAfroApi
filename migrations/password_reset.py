"""Cria a estrutura de recuperação de senha sem alterar contas existentes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import engine
from models import PasswordResetDB


def migrar():
    PasswordResetDB.__table__.create(engine, checkfirst=True)
    print("Estrutura de recuperação de senha preparada.")


if __name__ == "__main__":
    migrar()
