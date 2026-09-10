"""Migração aditiva do perfil administrativo e histórico IA do mentor."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import inspect, text
from database import engine
from models import IaMentorConversaDB, IaMentorMensagemDB

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--admin", type=int, help="ID de mentor existente autorizado pela equipe")
    args = parser.parse_args()
    if engine.dialect.name not in {"mysql", "mariadb"}:
        raise RuntimeError("Migração para MySQL/MariaDB.")
    if not args.apply:
        print("Adiciona mentor_access.administrador e duas tabelas de IA. Use --apply após backup.")
        raise SystemExit(0)
    if "administrador" not in {c["name"] for c in inspect(engine).get_columns("mentor_access")}:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE mentor_access ADD COLUMN administrador BOOLEAN NOT NULL DEFAULT 0"))
    IaMentorConversaDB.__table__.create(engine, checkfirst=True)
    IaMentorMensagemDB.__table__.create(engine, checkfirst=True)
    if args.admin is not None:
        with engine.begin() as conn:
            found = conn.execute(text("SELECT a.id_mentor FROM mentor_access a JOIN mentor m ON m.id_mentor=a.id_mentor WHERE a.id_mentor=:id AND a.ativo=1 FOR UPDATE"), {"id":args.admin}).first()
            if not found:
                raise RuntimeError("Mentor ativo não encontrado.")
            conn.execute(text("UPDATE mentor_access SET administrador=1 WHERE id_mentor=:id"), {"id":args.admin})
    print("Migração concluída.")
