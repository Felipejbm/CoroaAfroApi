"""Migração aditiva da estrutura real. Sem DROP, renomeações ou alterações de registros."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import inspect, text
from database import engine

COLUNAS = {
    "data_fundacao": "DATE", "segmento": "VARCHAR(32)",
    "rua": "VARCHAR(150)", "numero": "VARCHAR(20)", "complemento": "VARCHAR(100)",
    "bairro": "VARCHAR(100)", "cidade": "VARCHAR(100)", "estado": "CHAR(2)", "cep": "CHAR(8)",
}


def migrar(aplicar=False):
    if engine.dialect.name not in {"mysql", "mariadb"} or engine.url.database != "coroa_afro":
        raise RuntimeError("Migração destinada apenas ao MySQL coroa_afro.")
    insp = inspect(engine)
    existentes = {c["name"] for c in insp.get_columns("empresa")}
    obrigatorias = {"id_empresa", "id_usuario", "nome_empresa", "nome_fantasia", "numero_funcionarios", "endereco", "cnpj", "porte"}
    if not obrigatorias.issubset(existentes):
        raise RuntimeError("Estrutura de empresa diferente da inspecionada. Migração interrompida.")
    comandos = [f"ALTER TABLE empresa ADD COLUMN `{nome}` {tipo} NULL" for nome, tipo in COLUNAS.items() if nome not in existentes]
    indices = {i["name"] for i in insp.get_indexes("empresa")}
    if "ix_empresa_regiao" not in indices:
        comandos.append("CREATE INDEX ix_empresa_regiao ON empresa (estado, cidade)")
    if "ix_empresa_segmento" not in indices:
        comandos.append("CREATE INDEX ix_empresa_segmento ON empresa (segmento)")
    for sql in comandos:
        print(sql)
    if aplicar:
        # DDL MySQL pode confirmar automaticamente. Cada passo é aditivo e repetível.
        with engine.connect() as conn:
            conn.execute(text("SET SESSION lock_wait_timeout = 10"))
            for sql in comandos:
                conn.execute(text(sql))
                conn.commit()
        print("Migração concluída. Registros e endereço legado foram preservados.")
    else:
        print("Simulação: nenhum comando aplicado. Use --apply após revisar.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    migrar(parser.parse_args().apply)
