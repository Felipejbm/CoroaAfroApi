import unittest
import test_company_session as fixtures
from models import MetaEmpreendedorDB

class ValidacaoMetasTests(unittest.TestCase):
    setUp = fixtures.CompanySessionTests.setUp
    tearDown = fixtures.CompanySessionTests.tearDown
    login = fixtures.CompanySessionTests.login

    def test_unidade_e_limites_na_api(self):
        self.login()
        base = dict(titulo='Meta', unidade='seguidores', valor_inicial='0', valor_atual='0', valor_alvo='10', prazo='2026-12-31')
        for changes in ({'unidade': 'texto livre'}, {'valor_atual': '1.5'}, {'unidade': '%', 'valor_alvo': '100.01'}, {'unidade': '%', 'valor_atual': '101'}, {'unidade': 'R$', 'valor_alvo': '10.001'}):
            r = self.client.post('/metas', json={**base, **changes})
            self.assertEqual(r.status_code, 422, r.text)
        with self.sessions() as db:
            self.assertEqual(db.query(MetaEmpreendedorDB).count(), 0)
        for changes in ({'unidade': 'R$', 'valor_alvo': '1250.50'}, {'unidade': '%', 'valor_alvo': '100', 'valor_atual': '25.5'}):
            r = self.client.post('/metas', json={**base, **changes})
            self.assertEqual(r.status_code, 201, r.text)
            invalida = self.client.patch('/metas/'+str(r.json()['id']), json={**base, **changes, 'valor_alvo': '0', 'versao': r.json()['versao']})
            self.assertEqual(invalida.status_code, 422)
