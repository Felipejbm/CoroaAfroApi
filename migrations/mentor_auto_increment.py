import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text

from database import engine


def migrate():
    if engine.dialect.name != "mysql":
        return
    coluna = next((item for item in inspect(engine).get_columns("mentor") if item["name"] == "id_mentor"), None)
    if not coluna or coluna.get("autoincrement"):
        return
    with engine.begin() as connection:
        if connection.execute(text("SELECT COUNT(*) FROM mentor WHERE id_mentor = 0")).scalar():
            raise RuntimeError("Existe mentor com ID zero. Corrija os vínculos com uma migração específica antes de alterar o identificador.")
        connection.execute(text("ALTER TABLE mentor MODIFY id_mentor INT NOT NULL AUTO_INCREMENT"))


if __name__ == "__main__":
    migrate()
    print("Identificador automático de mentor preparado.")
