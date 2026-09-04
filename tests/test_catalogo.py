import unittest
import test_aprendizado as aprendizado
import test_company_session as fixtures
from models import (MentoriaDB, MentorAccessDB, MentoriaAtribuicaoDB,
                    MentoriaCatalogoDB, MentoriaTrilhaDB, MentoriaProgressoDB)


class CatalogoTests(unittest.TestCase):
    setUp = fixtures.CompanySessionTests.setUp
    tearDown = fixtures.CompanySessionTests.tearDown
    login = fixtures.CompanySessionTests.login
    mentor_login = fixtures.CompanySessionTests.mentor_login
    seed_mentors = fixtures.CompanySessionTests.seed_mentors
    preparar = aprendizado.AprendizadoTests.preparar
    payload = aprendizado.AprendizadoTests.payload
    criar = aprendizado.AprendizadoTests.criar
    publicar = aprendizado.AprendizadoTests.publicar

    def test_catalogo_filtro_preview_e_paginacao(self):
        self.preparar()
        t = self.publicar(self.criar())
        self.criar()  # Rascunho não aparece.
        self.login(2)
        self.assertEqual(self.client.get('/mentoria/catalogo/categorias').status_code, 200)
        r = self.client.get('/mentoria/catalogo?categoria=instagram')
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.headers['cache-control'], 'no-store')
        self.assertEqual(r.json()['total'], 1)
        item = r.json()['itens'][0]
        self.assertEqual(item['id'], t['id'])
        self.assertEqual(item['mentor']['nome'], 'Mentor 1')
        self.assertEqual(item['publico_alvo'], 'Iniciantes')
        self.assertFalse(item['inscrito'])
        self.assertNotIn('conteudo', item['aulas'][0])
        self.assertNotIn('video_url', item['aulas'][0])
        self.assertNotIn('email', item['mentor'])
        self.assertEqual(self.client.get('/mentoria/catalogo?categoria=vendas').json()['total'], 0)
        self.assertEqual(self.client.get('/mentoria/catalogo?categoria=invalida').status_code, 422)
        self.assertEqual(self.client.get('/mentoria/catalogo?pagina=0').status_code, 422)
        self.assertEqual(self.client.get('/mentoria/catalogo?pagina=2').json()['itens'], [])

    def test_inscricao_cria_vinculo_sem_convite_e_nao_duplica(self):
        self.preparar()
        t = self.publicar(self.criar())
        segunda = self.publicar(self.criar())
        self.login(2)
        with self.sessions() as db:
            self.assertIsNone(db.get(MentoriaDB, (1, 2)))
        url = f"/mentoria/catalogo/{t['id']}/inscricao"
        for _ in range(2):
            self.assertEqual(self.client.post(url).status_code, 200)
        aula = t['aulas'][0]['id']
        self.client.put(f"/mentoria/minhas-trilhas/{t['id']}/aulas/{aula}", json={'concluida': True})
        self.assertEqual(self.client.post(url).json()['progresso'], 50)
        self.assertEqual(self.client.post(f"/mentoria/catalogo/{segunda['id']}/inscricao").status_code, 200)
        with self.sessions() as db:
            self.assertEqual(db.query(MentoriaDB).filter_by(id_mentor=1, id_empreendedor=2).count(), 1)
            self.assertEqual(db.query(MentoriaAtribuicaoDB).filter_by(id_empreendedor=2).count(), 2)
            self.assertTrue(db.get(MentoriaProgressoDB, (aula, 2)).concluida)
        self.mentor_login()
        self.assertIn(2, [a['id'] for a in self.client.get('/mentoria/mentorados').json()])
        self.assertEqual(len(self.client.get('/mentoria/mentorados/2/trilhas').json()), 2)

    def test_varios_mentores_sem_vazamento_de_progresso(self):
        self.preparar()
        primeira = self.publicar(self.criar())
        self.mentor_login(2)
        segunda = self.publicar(self.criar())
        self.login(2)
        for t in (primeira, segunda):
            self.assertEqual(self.client.post(f"/mentoria/catalogo/{t['id']}/inscricao").status_code, 200)
        self.assertEqual(len(self.client.get('/mentoria/minhas-trilhas').json()), 2)
        for n, t in ((1, primeira), (2, segunda)):
            self.mentor_login(n)
            trilhas = self.client.get('/mentoria/mentorados/2/trilhas').json()
            self.assertEqual([x['id'] for x in trilhas], [t['id']])

    def test_bloqueios_sessao_papel_e_origem(self):
        self.assertEqual(self.client.get('/mentoria/catalogo').status_code, 401)
        self.assertEqual(self.client.post('/mentoria/catalogo/1/inscricao').status_code, 401)
        self.preparar()
        t = self.publicar(self.criar())
        rascunho = self.criar()
        self.assertEqual(self.client.get('/mentoria/catalogo').status_code, 401)
        self.assertEqual(self.client.post(f"/mentoria/catalogo/{t['id']}/inscricao").status_code, 401)
        self.assertEqual(self.client.put(f"/mentoria/trilhas/{t['id']}/mentorados/2").status_code, 403)
        self.login(2)
        self.assertEqual(self.client.post(f"/mentoria/catalogo/{rascunho['id']}/inscricao").status_code, 404)
        self.assertEqual(self.client.post(f"/mentoria/catalogo/{t['id']}/inscricao", headers={'Origin': 'https://evil.invalid'}).status_code, 403)
        with self.sessions() as db:
            db.add(MentoriaDB(id_mentor=1, id_empreendedor=2, ativo=False)); db.commit()
        self.assertEqual(self.client.get('/mentoria/catalogo').json()['total'], 0)
        self.assertEqual(self.client.post(f"/mentoria/catalogo/{t['id']}/inscricao").status_code, 403)
        with self.sessions() as db:
            self.assertFalse(db.get(MentoriaDB, (1, 2)).ativo)
            db.get(MentorAccessDB, 1).ativo = False; db.commit()
        self.assertEqual(self.client.post(f"/mentoria/catalogo/{t['id']}/inscricao").status_code, 404)

    def test_classificar_publicada_e_preservar_legado(self):
        self.preparar()
        t = self.publicar(self.criar())
        with self.sessions() as db:
            db.query(MentoriaCatalogoDB).filter_by(id_trilha=t['id']).delete(); db.commit()
        self.login(2)
        self.assertEqual(self.client.get('/mentoria/catalogo?categoria=geral').json()['total'], 1)
        self.client.post(f"/mentoria/catalogo/{t['id']}/inscricao")
        self.client.put(f"/mentoria/minhas-trilhas/{t['id']}/aulas/{t['aulas'][0]['id']}", json={'concluida': True})
        self.mentor_login()
        url = f"/mentoria/trilhas/{t['id']}/catalogo"
        payload = {'categoria': 'vendas', 'publico_alvo': 'Pequenos negócios', 'versao': t['versao']}
        r = self.client.patch(url, json=payload)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['aulas'], t['aulas'])
        self.assertEqual(self.client.patch(url, json=payload).status_code, 409)
        self.mentor_login(2)
        self.assertEqual(self.client.patch(url, json={**payload, 'versao': r.json()['versao']}).status_code, 404)
        self.login(2)
        self.assertEqual(self.client.get('/mentoria/catalogo?categoria=vendas').json()['total'], 1)
        self.assertEqual(self.client.get('/mentoria/minhas-trilhas').json()[0]['progresso'], 50)

    def test_paginacao_limita_catalogo(self):
        self.preparar()
        with self.sessions() as db:
            for i in range(13):
                db.add(MentoriaTrilhaDB(id_mentor=1, titulo=f'Trilha {i}', descricao='', publicada=True))
            db.commit()
        self.login(2)
        primeira = self.client.get('/mentoria/catalogo').json()
        segunda = self.client.get('/mentoria/catalogo?pagina=2').json()
        self.assertEqual(primeira['total'], 13)
        self.assertEqual(len(primeira['itens']), 12)
        self.assertEqual(len(segunda['itens']), 1)
        self.assertFalse({t['id'] for t in primeira['itens']} & {t['id'] for t in segunda['itens']})
