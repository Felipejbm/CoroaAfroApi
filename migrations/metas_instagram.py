"""Adiciona suporte a metas automáticas do Instagram sem alterar metas existentes."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text

from database import engine


COLUNAS = {
    "tipo": "VARCHAR(16) NOT NULL DEFAULT 'manual'",
    "origem": "VARCHAR(16) NOT NULL DEFAULT 'manual'",
    "metrica": "VARCHAR(40) NULL",
    "ultima_sincronizacao": "DATETIME NULL",
}


def migrar(aplicar: bool = False):
    if engine.dialect.name not in {"mysql", "mariadb"}:
        raise RuntimeError("Migração destinada ao MySQL/MariaDB.")
    existentes = {coluna["name"] for coluna in inspect(engine).get_columns("meta_empreendedor")}
    comandos = [
        f"ALTER TABLE meta_empreendedor ADD COLUMN `{nome}` {definicao}"
        for nome, definicao in COLUNAS.items()
        if nome not in existentes
    ]
    prazo = next(coluna for coluna in inspect(engine).get_columns("meta_empreendedor") if coluna["name"] == "prazo")
    if not prazo["nullable"]:
        comandos.append("ALTER TABLE meta_empreendedor MODIFY COLUMN prazo DATE NULL")
    for comando in comandos:
        print(comando)
    if not aplicar:
        print("Simulação: nenhum comando aplicado. Use --apply após revisar.")
        return
    with engine.begin() as conexao:
        for comando in comandos:
            conexao.execute(text(comando))
    print("Migração concluída. Metas existentes permaneceram como manuais.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    migrar(parser.parse_args().apply)
