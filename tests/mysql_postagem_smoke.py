"""Valida posts no MySQL real usando transação externa e rollback dos registros."""
import sys
from pathlib import Path
from secrets import token_hex
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from database import engine, get_db
from main import app
from models import EmpreendedorDB, AuthSessionDB, PostagemChatDB, PostagemComentarioDB
from security import COOKIE_NAME, token_hash
from config import get_settings


def verificar():
    if engine.dialect.name not in {'mysql', 'mariadb'} or engine.url.database != 'coroa-afro':
        raise RuntimeError('Teste limitado ao MySQL coroa-afro.')
    with engine.connect() as conn:
        tabelas = {'empreendedor', 'auth_session', 'postagem', 'postagem_comentario'}
        tipos = dict(conn.execute(text('SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()')).all())
        assert all(tipos.get(t) == 'InnoDB' for t in tabelas)
        triggers = conn.execute(text('SELECT EVENT_OBJECT_TABLE FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()')).scalars()
        assert not tabelas.intersection(triggers), 'Triggers exigem revisão antes do teste.'
        assert conn.execute(text('SELECT @@innodb_force_recovery')).scalar() == 0
    chave = token_hex(24)
    with engine.connect() as conn:
        transacao = conn.begin()
        sessions = sessionmaker(bind=conn, join_transaction_mode='create_savepoint')
        def override():
            with sessions() as db:
                yield db
        app.dependency_overrides[get_db] = override
        try:
            with sessions() as db:
                pessoa = EmpreendedorDB(nome='Validação temporária', email=f'{chave}@example.invalid', senha=token_hex(32), telefone='11900000000')
                db.add(pessoa)
                db.flush()
                db.add(AuthSessionDB(token_hash=token_hash(chave), id_empreendedor=pessoa.id_empreendedor, expires_at=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(minutes=5)))
                db.commit()
            with TestClient(app, headers={'Origin': get_settings().frontend_origin}) as client:
                client.cookies.set(COOKIE_NAME, chave)
                r = client.post('/postagem/criar-postagem', json={'conteudo_texto': '  Validação de persistência 😀  '})
                assert r.status_code == 201, r.text
                post_id = r.json()['id_post']
                r = client.post(f'/postagem/{post_id}/comentarios', json={'texto': 'Comentário persistido'})
                assert r.status_code == 201, r.text
                r = client.get(f'/postagem/{post_id}')
                assert r.status_code == 200 and len(r.json()['comments']) == 1
                assert client.post('/postagem/criar-postagem', json={'conteudo_texto': ' '}).status_code == 422
                with sessions() as db:
                    assert db.get(PostagemChatDB, post_id).conteudo_texto == 'Validação de persistência 😀'
                    assert db.query(PostagemComentarioDB).filter_by(id_post=post_id).count() == 1
                from io import BytesIO
                from PIL import Image
                arquivo = BytesIO()
                Image.new('RGB', (80, 40), 'blue').save(arquivo, format='PNG')
                r = client.patch(f'/postagem/{post_id}/com-imagem', data={'conteudo_texto': 'Texto com upload'},
                                 files={'imagem': ('teste.png', arquivo.getvalue(), 'image/png')})
                assert r.status_code == 200, r.text
                imagem_url = r.json()['imagem_upload_url']
                imagem = client.get(imagem_url)
                assert imagem.status_code == 200 and imagem.headers['content-type'] == 'image/jpeg'
                with sessions() as db:
                    assert db.get(PostagemChatDB, post_id).imagem == imagem.content
                assert client.patch(f'/postagem/{post_id}', json={'midia_url': None}).status_code == 200
                assert client.get(imagem_url).status_code == 404
                assert client.delete(f'/postagem/{post_id}').status_code == 204
                assert client.get(f'/postagem/{post_id}').status_code == 404
        finally:
            app.dependency_overrides.pop(get_db, None)
            transacao.rollback()
    with engine.connect() as conn:
        assert conn.execute(text('SELECT COUNT(*) FROM empreendedor WHERE email=:email'), {'email': f'{chave}@example.invalid'}).scalar() == 0
    print('MySQL real: criação, comentário, upload, edição, remoção de imagem e exclusão aprovados. Registros de teste revertidos.')

if __name__ == '__main__':
    verificar()
