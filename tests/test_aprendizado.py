"""Testes de papéis, atribuição, publicação e progresso, sem dados reais."""
import unittest
import test_company_session as fixtures
from models import MentoriaDB, MentorAccessDB, MentoriaProgressoDB


class AprendizadoTests(unittest.TestCase):
    setUp = fixtures.CompanySessionTests.setUp
    tearDown = fixtures.CompanySessionTests.tearDown
    login = fixtures.CompanySessionTests.login
    seed_mentors = fixtures.CompanySessionTests.seed_mentors
    mentor_login = fixtures.CompanySessionTests.mentor_login

    def preparar(self):
        self.seed_mentors()
        self.assertEqual(self.mentor_login().status_code, 200)

    def payload(self):
        return {"categoria": "instagram", "publico_alvo": "Iniciantes", "titulo": "Marketing inicial", "descricao": "Primeiros passos", "aulas": [
            {"titulo": "Perfil", "conteudo": "Revise sua bio.", "video_url": "https://youtu.be/exemplo"},
            {"titulo": "Planejamento", "conteudo": "Organize as publicações."}]}

    def criar(self):
        r = self.client.post("/mentoria/trilhas", json=self.payload())
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def publicar(self, t):
        r = self.client.post(f"/mentoria/trilhas/{t['id']}/publicar", json={"versao": t['versao']})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def atribuir(self, t, aluno=1):
        self.login(aluno)
        result = self.client.post(f"/mentoria/catalogo/{t['id']}/inscricao")
        self.mentor_login()
        return result

    def test_ciclo_completo_e_persistencia(self):
        self.preparar()
        t = self.criar()
        self.assertFalse(t['publicada'])
        self.assertEqual(self.atribuir(t).status_code, 404)
        t = self.publicar(t)
        self.assertEqual(self.atribuir(t).status_code, 200)
        self.assertEqual(self.atribuir(t).status_code, 200)
        self.login()
        ts = self.client.get('/mentoria/minhas-trilhas')
        self.assertEqual(ts.headers['cache-control'], 'no-store')
        self.assertEqual(ts.json()[0]['progresso'], 0)
        for i, aula in enumerate(t['aulas']):
            url = f"/mentoria/minhas-trilhas/{t['id']}/aulas/{aula['id']}"
            for _ in range(2):
                r = self.client.put(url, json={'concluida': True})
                self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual(r.json()['progresso'], (i + 1) * 50)
        self.assertEqual(self.client.get('/mentoria/minhas-trilhas').json()[0]['progresso'], 100)
        self.mentor_login()
        self.assertEqual(self.client.get('/mentoria/mentorados/1/trilhas').json()[0]['progresso'], 100)
        self.login()
        self.assertEqual(self.client.put(url, json={'concluida': False}).json()['progresso'], 50)
        with self.sessions() as db:
            self.assertEqual(db.query(MentoriaProgressoDB).count(), 2)

    def test_rascunho_edicao_conflito_e_publicacao(self):
        self.preparar()
        t = self.criar()
        url = f"/mentoria/trilhas/{t['id']}"
        payload = {**self.payload(), 'versao': t['versao'], 'titulo': 'Atualizada'}
        r = self.client.put(url, json=payload)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['versao'], 2)
        self.assertEqual(self.client.put(url, json=payload).status_code, 409)
        self.assertEqual(self.client.post(url + '/publicar', json={'versao': 1}).status_code, 409)
        t = self.publicar(r.json())
        self.assertEqual(self.client.put(url, json={**payload, 'versao': t['versao']}).status_code, 409)
        self.assertEqual(self.client.get('/mentoria/trilhas').json()[0]['titulo'], 'Atualizada')
        r = self.client.post('/mentoria/trilhas', json={'titulo': 'Sem aulas'})
        self.assertEqual(self.client.post(f"/mentoria/trilhas/{r.json()['id']}/publicar", json={'versao': 1}).status_code, 422)

    def test_isolamento_mentor_e_empreendedor(self):
        self.preparar()
        t = self.publicar(self.criar())
        self.assertEqual(self.client.put(f"/mentoria/trilhas/{t['id']}/mentorados/2").status_code, 403)
        self.assertEqual(self.atribuir(t).status_code, 200)
        self.mentor_login(2)
        self.assertEqual(self.client.get('/mentoria/trilhas').json(), [])
        self.assertEqual(self.client.put(f"/mentoria/trilhas/{t['id']}", json={**self.payload(), 'versao': t['versao']}).status_code, 404)
        self.assertEqual(self.client.get('/mentoria/mentorados/1/trilhas').status_code, 404)
        self.login(2)
        self.assertEqual(self.client.get('/mentoria/minhas-trilhas').json(), [])
        url = f"/mentoria/minhas-trilhas/{t['id']}/aulas/{t['aulas'][0]['id']}"
        self.assertEqual(self.client.put(url, json={'concluida': True}).status_code, 404)

    def test_revogacao_vinculo_e_mentor(self):
        self.preparar()
        t = self.publicar(self.criar())
        self.atribuir(t)
        self.login()
        url = f"/mentoria/minhas-trilhas/{t['id']}/aulas/{t['aulas'][0]['id']}"
        for alvo in ('vinculo', 'mentor'):
            with self.sessions() as db:
                db.get(MentoriaDB, (1, 1)).ativo = alvo != 'vinculo'
                db.get(MentorAccessDB, 1).ativo = alvo != 'mentor'
                db.commit()
            self.assertEqual(self.client.get('/mentoria/minhas-trilhas').json(), [])
            self.assertEqual(self.client.put(url, json={'concluida': True}).status_code, 404)

    def test_autenticacao_papeis_origem_e_validacao(self):
        self.assertEqual(self.client.get('/mentoria/trilhas').status_code, 401)
        self.assertEqual(self.client.get('/mentoria/minhas-trilhas').status_code, 401)
        self.preparar()
        self.assertEqual(self.client.get('/mentoria/minhas-trilhas').status_code, 401)
        self.assertEqual(self.client.post('/mentoria/trilhas', json=self.payload(), headers={'Origin': 'https://evil.invalid'}).status_code, 403)
        for url in ('javascript:alert(1)', 'http://youtube.com/a', 'https://youtube.com.evil.invalid/a', 'https://user:pass@youtube.com/a'):
            payload = self.payload()
            payload['aulas'][0]['video_url'] = url
            self.assertEqual(self.client.post('/mentoria/trilhas', json=payload).status_code, 422)
        for changes in ({'categoria': 'invalida'}, {'titulo': ' '}, {'id_mentor': 2}, {'publicada': True}, {'aulas': [{'titulo': 'X', 'conteudo': ' '}]}):
            self.assertEqual(self.client.post('/mentoria/trilhas', json={**self.payload(), **changes}).status_code, 422)
        self.login()
        self.assertEqual(self.client.post('/mentoria/trilhas', json=self.payload()).status_code, 401)

    def test_aula_de_outra_trilha_e_rascunho_invisivel(self):
        self.preparar()
        t = self.publicar(self.criar())
        outra = self.criar()
        self.atribuir(t)
        self.login()
        self.assertEqual(len(self.client.get('/mentoria/minhas-trilhas').json()), 1)
        url = f"/mentoria/minhas-trilhas/{t['id']}/aulas/{outra['aulas'][0]['id']}"
        self.assertEqual(self.client.put(url, json={'concluida': True}).status_code, 404)


if __name__ == '__main__':
    unittest.main()
