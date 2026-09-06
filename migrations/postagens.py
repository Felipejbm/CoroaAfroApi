"""Prepara postagens existentes sem apagar ou atribuir autoria a registros antigos."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import inspect, text
from database import engine
from models import PostagemChatDB, PostagemComentarioDB


def migrar(aplicar=False):
    if engine.dialect.name not in {'mysql', 'mariadb'} or engine.url.database != 'coroa-afro':
        raise RuntimeError('Migração destinada apenas ao MySQL coroa-afro.')
    insp = inspect(engine)
    comandos = []
    if insp.has_table('postagem'):
        colunas = {c['name']: c for c in insp.get_columns('postagem')}
        if not {'id_post', 'conteudo_texto', 'midia_url', 'data_publicacao'}.issubset(colunas):
            raise RuntimeError('Estrutura de postagem incompatível.')
        if not colunas['id_post'].get('autoincrement'):
            comandos.append('ALTER TABLE postagem MODIFY id_post INT NOT NULL AUTO_INCREMENT')
        if 'fk_empreendedor_id_empreendedor' not in colunas:
            comandos.append('ALTER TABLE postagem ADD COLUMN fk_empreendedor_id_empreendedor INT NULL, ADD CONSTRAINT fk_postagem_autor FOREIGN KEY (fk_empreendedor_id_empreendedor) REFERENCES empreendedor(id_empreendedor)')
        if 'id_mentor' not in colunas:
            comandos.append('ALTER TABLE postagem ADD COLUMN id_mentor INT NULL, ADD CONSTRAINT fk_postagem_mentor FOREIGN KEY (id_mentor) REFERENCES mentor(id_mentor)')
        if 'imagem' not in colunas:
            comandos.append('ALTER TABLE postagem ADD COLUMN imagem MEDIUMBLOB NULL')
        if 'imagem_hash' not in colunas:
            comandos.append('ALTER TABLE postagem ADD COLUMN imagem_hash VARCHAR(64) NULL')
        checks = {c['name'] for c in insp.get_check_constraints('postagem')}
        if 'ck_postagem_autor_unico' not in checks:
            comandos.append('ALTER TABLE postagem ADD CONSTRAINT ck_postagem_autor_unico CHECK (fk_empreendedor_id_empreendedor IS NULL OR id_mentor IS NULL)')
    if insp.has_table('postagem_comentario'):
        colunas = {c['name']: c for c in insp.get_columns('postagem_comentario')}
        if not colunas['id_empreendedor']['nullable']:
            comandos.append('ALTER TABLE postagem_comentario MODIFY id_empreendedor INT NULL')
        if 'id_mentor' not in colunas:
            comandos.append('ALTER TABLE postagem_comentario ADD COLUMN id_mentor INT NULL, ADD CONSTRAINT fk_comentario_mentor FOREIGN KEY (id_mentor) REFERENCES mentor(id_mentor)')
        checks = {c['name'] for c in insp.get_check_constraints('postagem_comentario')}
        if 'ck_comentario_autor_unico' not in checks:
            comandos.append('ALTER TABLE postagem_comentario ADD CONSTRAINT ck_comentario_autor_unico CHECK ((id_empreendedor IS NULL) <> (id_mentor IS NULL))')
    for comando in comandos:
        print(comando)
    if aplicar:
        with engine.connect() as conn:
            if conn.execute(text('SELECT @@innodb_force_recovery')).scalar() != 0:
                raise RuntimeError('Não aplicar migração em modo de recuperação do InnoDB.')
            conn.execute(text('SET SESSION lock_wait_timeout = 10'))
            for comando in comandos:
                conn.execute(text(comando))
                conn.commit()
        PostagemChatDB.__table__.create(engine, checkfirst=True)
        PostagemComentarioDB.__table__.create(engine, checkfirst=True)
        print('Estrutura de postagens e comentários preparada. Registros preservados.')
    else:
        print('Simulação. Também serão criadas as tabelas ausentes de postagens/comentários. Use --apply para aplicar.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    migrar(parser.parse_args().apply)
