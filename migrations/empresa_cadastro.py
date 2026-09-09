"""Ajusta ID automático e limites de cadastro sem excluir registros existentes."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import inspect, text
from database import engine


def migrar(aplicar=False):
    if engine.dialect.name not in {'mysql', 'mariadb'} or engine.url.database != 'coroa-afro':
        raise RuntimeError('Migração limitada ao banco coroa-afro.')
    insp = inspect(engine)
    colunas = {c['name']: c for c in insp.get_columns('empresa')}
    if insp.get_pk_constraint('empresa')['constrained_columns'] != ['id_empresa']:
        raise RuntimeError('Chave primária inesperada; nenhuma alteração aplicada.')
    comandos = []
    if not colunas['id_empresa'].get('autoincrement'):
        comandos.append('ALTER TABLE empresa MODIFY id_empresa INT NOT NULL AUTO_INCREMENT')
    for nome, tamanho in [('porte', 50), ('segmento', 32)]:
        if getattr(colunas[nome]['type'], 'length', 0) < tamanho:
            nulo = 'NULL' if colunas[nome]['nullable'] else 'NOT NULL'
            comandos.append(f'ALTER TABLE empresa MODIFY {nome} VARCHAR({tamanho}) {nulo}')
    for comando in comandos:
        print(comando)
    if aplicar:
        with engine.connect() as conn:
            if conn.execute(text('SELECT @@innodb_force_recovery')).scalar() != 0:
                raise RuntimeError('O banco está em modo de recuperação.')
            conn.execute(text('SET SESSION lock_wait_timeout = 10'))
            for comando in comandos:
                conn.execute(text(comando))
                conn.commit()
        print('Cadastro de empresa preparado. Registros preservados.')
    else:
        print('Simulação; use --apply para aplicar.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    migrar(parser.parse_args().apply)
