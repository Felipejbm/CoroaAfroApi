import unittest
from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import test_company_session as company_tests
from main import app
from config import Settings
from database import Base
from models import IaConversaDB, IaMensagemDB
from schemas.IaSchema.IaSchema import IaConversaCriar
from routers.feedbackRoute import FeedbackEntrada
from routers.mentorSolicitacaoRoute import SolicitacaoEntrada
from routers.metasRoute import METRICAS_INSTAGRAM, MetaEntrada

class RevisaoApiTests(unittest.TestCase):
    def setUp(self): company_tests.CompanySessionTests.setUp(self)
    def tearDown(self): company_tests.CompanySessionTests.tearDown(self)
    def test_health_unique_and_database_failure(self):
        routes=[r for r in app.routes if getattr(r,'path',None)=='/health' and 'GET' in getattr(r,'methods',set())]
        self.assertEqual(len(routes),1)
        with patch('database.engine.connect',side_effect=SQLAlchemyError('private diagnostic')):
            r=self.client.get('/health')
        self.assertEqual(r.status_code,503)
        self.assertNotIn('private diagnostic',r.text)
    def test_cookie_configuration(self):
        self.assertFalse(Settings(_env_file=None,session_cookie_secure=False).session_cookie_secure)
        with self.assertRaises(ValidationError):
            Settings(_env_file=None,session_cookie_secure=False,session_cookie_samesite='none')
    def test_password_tables_do_not_conflict(self):
        self.assertIn('token_hash',Base.metadata.tables['password_reset'].columns)
        self.assertIn('codigo_hash',Base.metadata.tables['password_reset_codigo'].columns)
    def test_reset_not_exposed_publicly(self):
        with patch('routers.authRoute.get_settings',return_value=SimpleNamespace(password_reset_demo_mode=True)):
            r=self.client.post('/auth/password-reset/request',json={'email':'teste1@example.com','papel':'empreendedor'})
        self.assertEqual(r.status_code,503)
        self.assertNotIn('demo_code',r.text)
    def test_local_demo_single_use(self):
        with TestClient(app,client=('127.0.0.1',40000),headers={'Origin':'https://coroa-afro.vercel.app'}) as client:
            with patch('routers.authRoute.get_settings',return_value=SimpleNamespace(password_reset_demo_mode=True)):
                result=client.post('/auth/password-reset/request',json={'email':'teste1@example.com','papel':'empreendedor'})
                self.assertEqual(result.status_code,200,result.text)
                code=result.json()['demo_code']
                data={'email':'teste1@example.com','papel':'empreendedor','codigo':code,'nova_senha':'nova-senha-12345'}
                self.assertEqual(client.post('/auth/password-reset/confirm',json=data).status_code,200)
                self.assertEqual(client.post('/auth/password-reset/confirm',json=data).status_code,400)
    def test_inputs_reject_blank_and_invalid_email(self):
        with self.assertRaises(ValidationError): IaConversaCriar(titulo='   ')
        with self.assertRaises(ValidationError): FeedbackEntrada(nota=5,comentario=' '*20)
        with self.assertRaises(ValidationError): FeedbackEntrada(nota=5,comentario='Um comentario valido',autoriza_publicacao='yes')
        with self.assertRaises(ValidationError): SolicitacaoEntrada(nome='Mentor',email='nao-email',senha='senha1234',especialidade='Gestao',biografia='Uma biografia profissional valida')
        self.assertTrue(all(len(v)<=30 for v in METRICAS_INSTAGRAM.values()))
    def test_recent_history_in_chronological_order(self):
        company_tests.CompanySessionTests.login(self)
        with self.sessions() as db:
            conversa=IaConversaDB(id_empreendedor=1,titulo='Historico')
            db.add(conversa);db.flush();id=conversa.id_conversa
            db.add_all([IaMensagemDB(id_conversa=id,papel='usuario',conteudo=str(n)) for n in range(60)])
            db.commit()
        r=self.client.get(f'/ia/conversas/{id}/mensagens?limite=5')
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual([m['conteudo'] for m in r.json()],['55','56','57','58','59'])
    def test_admin_unicode_password_and_cookie(self):
        cfg=Settings(_env_file=None,admin_email='admin@example.com',admin_password='senhã-segura-123',session_cookie_secure=False,session_cookie_samesite='lax')
        with patch('routers.adminRoute.get_settings',return_value=cfg):
            r=self.client.post('/admin/login',json={'email':'admin@example.com','senha':'senhã-segura-123'})
            self.assertEqual(r.status_code,200,r.text)
            self.assertEqual(self.client.get('/admin/me').status_code,200)
            self.assertEqual(self.client.post('/admin/logout').status_code,200)
            self.assertEqual(self.client.get('/admin/me').status_code,401)

    def test_instagram_unit_is_server_controlled(self):
        meta=MetaEntrada(titulo="Interações",tipo="instagram",metrica="interacoes_recentes",unidade="interações nas 5 publicações recentes",valor_inicial=0,valor_atual=0,valor_alvo=100)
        self.assertEqual(meta.unidade,"interações")
