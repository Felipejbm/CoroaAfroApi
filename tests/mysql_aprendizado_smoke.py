"""Teste opt-in da mentoria no MySQL real, revertendo todos os registros criados."""
import argparse
import secrets
from uuid import uuid4
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from database import engine, get_db
from main import app
from models import EmpreendedorDB, MentorDB, MentorAccessDB, MentoriaDB
from security import hash_password


def verificar():
    if engine.dialect.name not in {'mysql', 'mariadb'} or engine.url.database != 'coroa-afro':
        raise RuntimeError('Teste limitado ao MySQL coroa-afro.')
    tabelas = {'empreendedor', 'mentor', 'mentor_access', 'mentor_session', 'auth_session',
               'mentoria_mensagem', 'mentoria_catalogo', 'mentoria_vinculo', 'mentoria_trilha', 'mentoria_aula', 'mentoria_atribuicao', 'mentoria_progresso'}
    with engine.connect() as preflight:
        engines = dict(preflight.execute(text('SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()')).all())
        if any(engines.get(t) != 'InnoDB' for t in tabelas):
            raise RuntimeError('Todas as tabelas precisam ser InnoDB para rollback seguro.')
        triggers = preflight.execute(text('SELECT EVENT_OBJECT_TABLE FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()'))
        if any(row[0] in tabelas for row in triggers):
            raise RuntimeError('Triggers encontrados; revisão necessária antes do teste.')
    marcador = secrets.token_hex(10)
    email_aluno = f'aluno-{marcador}@example.invalid'
    email_mentor = f'mentor-{marcador}@example.invalid'
    senha = secrets.token_urlsafe(24)
    trilha_id = None
    mentor_id = None
    conn = engine.connect()
    transaction = conn.begin()
    sessions = sessionmaker(bind=conn, join_transaction_mode='create_savepoint')
    def override():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = override
    try:
        with sessions() as db:
            aluno = EmpreendedorDB(nome='Teste transacional', email=email_aluno, senha=hash_password(senha), telefone='11900000000')
            mentor = MentorDB(nome='Teste transacional', especialidade='Teste', biografia='')
            db.add_all([aluno, mentor]); db.flush()
            aluno_id, mentor_id = aluno.id_empreendedor, mentor.id_mentor
            db.add(MentorAccessDB(id_mentor=mentor_id, email=email_mentor, senha_hash=hash_password(senha), ativo=True))

            db.commit()
        with TestClient(app, headers={'Origin': 'http://localhost:5173'}) as client:
            assert client.post('/auth/login', json={'email': email_mentor, 'senha': senha, 'papel': 'mentor'}).status_code == 200
            dados = {'categoria': 'instagram', 'publico_alvo': 'Iniciantes', 'titulo': 'Trilha transacional', 'descricao': '', 'aulas': [{'titulo': 'Aula teste', 'conteudo': 'Conteúdo teste.'}]}
            r = client.post('/mentoria/trilhas', json=dados)
            assert r.status_code == 201, f'Criar trilha: {r.status_code}'
            trilha_id = r.json()['id']
            url = f'/mentoria/trilhas/{trilha_id}'
            r = client.put(url, json={**dados, 'titulo': 'Trilha revisada', 'versao': 1})
            assert r.status_code == 200, f'Editar trilha: {r.status_code}'
            r = client.post(url + '/publicar', json={'versao': r.json()['versao']})
            assert r.status_code == 200
            aula_id = r.json()['aulas'][0]['id']
            assert client.put(url + f'/mentorados/{aluno_id}').status_code == 403
            with sessions() as db:
                assert db.get(MentoriaDB, (mentor_id, aluno_id)) is None
            assert client.post('/auth/login', json={'email': email_aluno, 'senha': senha}).status_code == 200
            catalogo = client.get('/mentoria/catalogo?categoria=instagram').json()
            assert any(t['id'] == trilha_id for t in catalogo['itens'])
            for _ in range(2):
                assert client.post(f'/mentoria/catalogo/{trilha_id}/inscricao').status_code == 200
            with sessions() as db:
                assert db.get(MentoriaDB, (mentor_id, aluno_id)).ativo
            assert client.get('/mentoria/minhas-trilhas').json()[0]['progresso'] == 0
            r = client.put(f'/mentoria/minhas-trilhas/{trilha_id}/aulas/{aula_id}', json={'concluida': True})
            assert r.status_code == 200 and r.json()['progresso'] == 100
            chat_url = f'/mentoria/chat/conversas/{mentor_id}/{aluno_id}/mensagens'
            envio = {'texto': 'Dúvida de teste 😀', 'chave_envio': str(uuid4())}
            primeira = client.post(chat_url, json=envio)
            assert primeira.status_code == 200, f'Envio no chat: {primeira.status_code}'
            assert client.post(chat_url, json=envio).json()['id'] == primeira.json()['id']
            assert client.post('/auth/login', json={'email': email_mentor, 'senha': senha, 'papel': 'mentor'}).status_code == 200
            assert client.get(f'/mentoria/mentorados/{aluno_id}/trilhas').json()[0]['progresso'] == 100
            assert len(client.get('/mentoria/chat/conversas').json()) == 1
            assert client.get(chat_url).json()['mensagens'][0]['texto'] == envio['texto']
            assert not client.get(chat_url).json()['mensagens'][0]['minha']
            assert client.post(chat_url, json={'texto': 'Resposta de teste', 'chave_envio': str(uuid4())}).status_code == 200
            assert client.post('/auth/login', json={'email': email_aluno, 'senha': senha}).status_code == 200
            assert len(client.get(chat_url).json()['mensagens']) == 2
            with sessions() as db:
                db.get(MentoriaDB, (mentor_id, aluno_id)).ativo = False; db.commit()
            assert client.get(chat_url).status_code == 404
            assert client.post(chat_url, json={'texto': 'Bloqueada', 'chave_envio': str(uuid4())}).status_code == 404
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        conn.close()
        with engine.connect() as check:
            assert check.execute(text('SELECT COUNT(*) FROM empreendedor WHERE email=:email'), {'email': email_aluno}).scalar() == 0
            assert check.execute(text('SELECT COUNT(*) FROM mentor_access WHERE email=:email'), {'email': email_mentor}).scalar() == 0
            if mentor_id:
                assert check.execute(text('SELECT COUNT(*) FROM mentor WHERE id_mentor=:id'), {'id': mentor_id}).scalar() == 0
                assert check.execute(text('SELECT COUNT(*) FROM mentoria_mensagem WHERE id_mentor=:id'), {'id': mentor_id}).scalar() == 0
            if trilha_id:
                for tabela in ('mentoria_trilha', 'mentoria_aula', 'mentoria_atribuicao', 'mentoria_catalogo'):
                    coluna = 'id' if tabela == 'mentoria_trilha' else 'id_trilha'
                    assert check.execute(text(f'SELECT COUNT(*) FROM {tabela} WHERE {coluna}=:id'), {'id': trilha_id}).scalar() == 0
        print('Rollback verificado: contas e trilhas de teste não ficaram salvas.')
    print('PASSOU: trilhas, inscrição, vínculo, progresso e chat privado no MySQL real.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    if parser.parse_args().run:
        verificar()
    else:
        print('Nada executado. Use --run. IDs auto_increment podem ter lacunas após rollback.')
