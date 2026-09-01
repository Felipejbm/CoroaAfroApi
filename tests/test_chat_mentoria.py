import unittest
from uuid import uuid4
from datetime import datetime, timedelta
import test_company_session as fixtures
from models import MentoriaDB, MentorAccessDB, AuthSessionDB, MentoriaMensagemDB
from security import COOKIE_NAME, token_hash


class ChatTests(unittest.TestCase):
    setUp = fixtures.CompanySessionTests.setUp
    tearDown = fixtures.CompanySessionTests.tearDown
    login = fixtures.CompanySessionTests.login
    seed_mentors = fixtures.CompanySessionTests.seed_mentors
    mentor_login = fixtures.CompanySessionTests.mentor_login
    url = '/mentoria/chat/conversas/1/1/mensagens'

    def enviar(self, texto='Olá, mentor!', chave=None, url=None):
        return self.client.post(url or self.url, json={'texto': texto, 'chave_envio': chave or str(uuid4())})

    def test_conversa_e_mensagens_dos_dois_participantes(self):
        self.seed_mentors(); self.login()
        r = self.client.get('/mentoria/chat/conversas')
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.headers['cache-control'], 'no-store')
        self.assertEqual(len(r.json()), 1)
        self.assertEqual(r.json()[0]['nome'], 'Mentor 1')
        self.assertIsNone(r.json()[0]['ultima_mensagem'])
        self.assertNotIn('email', r.text)
        r = self.enviar('Olá! 😀\nDúvida sobre a aula.')
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()['minha'])
        self.assertTrue(r.json()['criado_em'].endswith('+00:00'))
        self.mentor_login()
        self.assertEqual(self.client.get('/mentoria/chat/conversas').json()[0]['nome'], 'Teste 1')
        self.assertFalse(self.client.get(self.url).json()['mensagens'][0]['minha'])
        self.assertEqual(self.enviar('Pode perguntar!').status_code, 200)
        self.login()
        mensagens = self.client.get(self.url).json()['mensagens']
        self.assertEqual([m['minha'] for m in mensagens], [True, False])
        self.assertEqual(mensagens[1]['texto'], 'Pode perguntar!')
        self.assertEqual(self.client.get('/mentoria/chat/conversas').json()[0]['ultima_mensagem']['id'], mensagens[1]['id'])

    def test_isolamento_e_sem_vinculo(self):
        self.seed_mentors(); self.login(); self.enviar('Privada')
        self.login(2)
        self.assertEqual(self.client.get('/mentoria/chat/conversas').json(), [])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.enviar().status_code, 404)
        self.assertEqual(self.enviar(url='/mentoria/chat/conversas/1/2/mensagens').status_code, 404)
        self.mentor_login(2)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.enviar().status_code, 404)
        self.assertEqual(self.client.get('/mentoria/chat/conversas').json(), [])

    def test_idempotencia_por_dupla_e_remetente(self):
        self.seed_mentors(); self.login()
        chave = str(uuid4())
        primeira = self.enviar(chave=chave)
        segunda = self.enviar(chave=chave)
        self.assertEqual(primeira.json()['id'], segunda.json()['id'])
        self.assertEqual(self.enviar('Texto diferente', chave).status_code, 409)
        self.mentor_login()
        self.assertEqual(self.enviar('Resposta', chave).status_code, 200)
        with self.sessions() as db:
            self.assertEqual(db.query(MentoriaMensagemDB).count(), 2)

    def test_validacao_origem_sessao_e_autoria(self):
        self.assertEqual(self.client.get('/mentoria/chat/conversas').status_code, 401)
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.enviar().status_code, 401)
        self.seed_mentors(); self.login()
        for dados in ({'texto': ' '}, {'texto': 'x' * 4001}, {'chave_envio': 'errado'}, {'remetente': 'mentor'}, {'id_mentor': 2}):
            r = self.client.post(self.url, json={'texto': 'Teste', 'chave_envio': str(uuid4()), **dados})
            self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(self.client.post(self.url, json={'texto': 'Teste', 'chave_envio': str(uuid4())}, headers={'Origin': 'https://evil.invalid'}).status_code, 403)
        self.assertEqual(self.enviar('<script>alert(1)</script>').json()['texto'], '<script>alert(1)</script>')
        with self.sessions() as db:
            db.get(AuthSessionDB, token_hash(self.client.cookies.get(COOKIE_NAME))).expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.enviar().status_code, 401)

    def test_revogacao_preserva_historico_sem_liberar_acesso(self):
        self.seed_mentors(); self.login(); self.enviar()
        with self.sessions() as db:
            db.get(MentoriaDB, (1, 1)).ativo = False; db.commit()
        self.assertEqual(self.client.get('/mentoria/chat/conversas').json(), [])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.enviar().status_code, 404)
        with self.sessions() as db:
            self.assertEqual(db.query(MentoriaMensagemDB).count(), 1)
            db.get(MentoriaDB, (1, 1)).ativo = True
            db.get(MentorAccessDB, 1).ativo = False; db.commit()
        self.assertEqual(self.client.get('/mentoria/chat/conversas').json(), [])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.enviar().status_code, 404)

    def test_paginacao_e_polling_sem_lacunas(self):
        self.seed_mentors(); self.login()
        with self.sessions() as db:
            for i in range(105):
                db.add(MentoriaMensagemDB(id_mentor=1, id_empreendedor=1, remetente='mentor', texto=f'Mensagem {i}', chave_envio=str(uuid4()), criado_em=datetime.utcnow()))
            db.commit()
        recente = self.client.get(self.url).json()
        self.assertEqual(len(recente['mensagens']), 50)
        self.assertTrue(recente['tem_mais'])
        antigas = self.client.get(self.url, params={'antes': recente['mensagens'][0]['id']}).json()
        inicio = self.client.get(self.url, params={'antes': antigas['mensagens'][0]['id']}).json()
        self.assertEqual(len(inicio['mensagens']), 5)
        self.assertFalse(inicio['tem_mais'])
        ids = [m['id'] for parte in (inicio, antigas, recente) for m in parte['mensagens']]
        self.assertEqual(len(set(ids)), 105)
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(self.client.get(self.url, params={'depois': 0}).json()['mensagens']), 50)
        self.assertEqual(self.client.get(self.url, params={'depois': ids[-1]}).json()['mensagens'], [])
        r = self.enviar('Nova')
        self.assertEqual(self.client.get(self.url, params={'depois': ids[-1]}).json()['mensagens'][0]['id'], r.json()['id'])
        self.assertEqual(self.client.get(self.url, params={'antes': 1, 'depois': 1}).status_code, 422)
        self.assertEqual(self.client.get(self.url, params={'antes': -1}).status_code, 422)
