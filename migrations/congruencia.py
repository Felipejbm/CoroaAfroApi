"""Auditoria e migração conservadora do MySQL. Faça backup antes de --apply.
DDL tem commit implícito: o script pode ser executado novamente após falha.
Não remove tabelas, campos nem registros. Interrompe ao detectar dados incompatíveis.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import inspect, text, Boolean, Numeric
from database import engine, Base
import models


def equivalent(expected, actual):
    if isinstance(expected, Boolean) and str(actual) in {"TINYINT", "BOOLEAN", "BOOL"}:
        return True
    if isinstance(expected, Numeric) and isinstance(actual, Numeric):
        return expected.precision == actual.precision and expected.scale == actual.scale
    return str(expected.compile(dialect=engine.dialect)).upper() == str(actual).upper()


def audit():
    if engine.dialect.name not in {"mysql", "mariadb"}:
        raise RuntimeError("Esta migração exige MySQL/MariaDB.")
    ins = inspect(engine)
    q = engine.dialect.identifier_preparer.quote
    commands, errors = [], []
    if set(ins.get_table_names()) != set(Base.metadata.tables):
        errors.append("Conjunto de tabelas diferente dos modelos; revisão manual necessária.")
    with engine.connect() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in ins.get_table_names():
                continue
            name = q(table.name)
            cols = {c["name"]: c for c in ins.get_columns(table.name)}
            if set(cols) != set(table.columns.keys()):
                errors.append(f"Colunas divergentes: {table.name}")
                continue
            pk = ins.get_pk_constraint(table.name)["constrained_columns"]
            if pk != [c.name for c in table.primary_key.columns]:
                errors.append(f"Chave primária divergente: {table.name}")
            for col in table.columns:
                db = cols[col.name]
                auto = col is table.autoincrement_column
                if not col.nullable and conn.execute(text(f"SELECT COUNT(*) FROM {name} WHERE {q(col.name)} IS NULL")).scalar():
                    errors.append(f"NULL em {table.name}.{col.name}")
                limit = getattr(col.type, "length", None)
                if limit and conn.execute(text(f"SELECT COUNT(*) FROM {name} WHERE CHAR_LENGTH({q(col.name)}) > :limit"), {"limit": limit}).scalar():
                    errors.append(f"Dados excedem limite de {table.name}.{col.name}")
                if not equivalent(col.type, db["type"]) or col.nullable != db["nullable"] or auto != bool(db.get("autoincrement")):
                    # All conversions here preserve values; refuse unexpected conversions.
                    before, after = str(db["type"]), str(col.type.compile(dialect=engine.dialect))
                    safe = equivalent(col.type, db["type"]) or (before.startswith("VARCHAR") and after.startswith("VARCHAR")) or (before == "DATE" and after == "DATETIME")
                    if not safe:
                        errors.append(f"Conversão não aprovada: {table.name}.{col.name}: {before} -> {after}")
                        continue
                    default = " DEFAULT " + str(db["default"]) if db.get("default") is not None else ""
                    commands.append(f"ALTER TABLE {name} MODIFY COLUMN {q(col.name)} {after} {'NULL' if col.nullable else 'NOT NULL'}{default}{' AUTO_INCREMENT' if auto else ''}")
            uniques = {tuple(u["column_names"]) for u in ins.get_unique_constraints(table.name)} | {tuple(i["column_names"]) for i in ins.get_indexes(table.name) if i["unique"]} | {tuple(pk)}
            required = {tuple(c.name for c in u.columns) for u in table.constraints if u.__class__.__name__ == "UniqueConstraint"} | {tuple(c.name for c in i.columns) for i in table.indexes if i.unique}
            for fields in required:
                group = ', '.join(q(c) for c in fields)
                nonnull = ' AND '.join(q(c) + ' IS NOT NULL' for c in fields)
                count = conn.execute(text(f"SELECT COUNT(*) FROM (SELECT {group} FROM {name} WHERE {nonnull} GROUP BY {group} HAVING COUNT(*) > 1) d")).scalar()
                if count:
                    errors.append(f"Duplicidade em {table.name}: {fields}")
                if fields not in uniques:
                    idxname = ('uq_' + table.name + '_' + '_'.join(fields))[:64]
                    commands.append(f"CREATE UNIQUE INDEX {q(idxname)} ON {name} ({group})")
            actual_fk = {(tuple(f["constrained_columns"]), f["referred_table"], tuple(f["referred_columns"])) for f in ins.get_foreign_keys(table.name)}
            for fk in table.foreign_key_constraints:
                local = tuple(e.parent.name for e in fk.elements)
                remote = tuple(e.column.name for e in fk.elements)
                target = fk.referred_table.name
                if (local, target, remote) not in actual_fk:
                    errors.append(f"FK ausente: {table.name}.{local}")
                join = ' AND '.join(f'a.{q(a)}=b.{q(b)}' for a,b in zip(local,remote))
                nonnull = ' AND '.join(f'a.{q(a)} IS NOT NULL' for a in local)
                n = conn.execute(text(f"SELECT COUNT(*) FROM {name} a LEFT JOIN {q(target)} b ON {join} WHERE {nonnull} AND b.{q(remote[0])} IS NULL")).scalar()
                if n:
                    errors.append(f"Vínculos órfãos: {table.name}.{local}: {n}")
            for ck in table.constraints:
                if ck.__class__.__name__ == 'CheckConstraint':
                    if ck.name not in {x['name'] for x in ins.get_check_constraints(table.name)}:
                        errors.append(f"CHECK ausente: {ck.name}")
                    if conn.execute(text(f"SELECT COUNT(*) FROM {name} WHERE NOT ({ck.sqltext})")).scalar():
                        errors.append(f"Violação de CHECK: {ck.name}")
    return commands, errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    commands, errors = audit()
    for error in errors:
        print('BLOQUEIO:', error)
    for command in commands:
        print(command + ';')
    if errors:
        raise SystemExit(1)
    if args.apply:
        with engine.connect() as conn:
            if conn.execute(text('SELECT @@innodb_force_recovery')).scalar():
                raise RuntimeError('Banco em recuperação; migração bloqueada.')
            conn.execute(text("SET SESSION sql_mode = CONCAT_WS(',', @@sql_mode, 'NO_AUTO_VALUE_ON_ZERO', 'STRICT_ALL_TABLES')"))
            conn.execute(text('SET SESSION lock_wait_timeout=10'))
            conn.commit()
            for command in commands:
                conn.execute(text(command))
                conn.commit()
        commands, errors = audit()
    print(f'Pendências estruturais: {len(commands)}; inconsistências: {len(errors)}')
    if args.apply and (commands or errors):
        raise SystemExit(1)
