import unittest
from unittest.mock import patch
from datetime import timedelta
from urllib.parse import urlsplit, parse_qs
import test_company_session as fixtures
from models import PasswordResetDB, MentorAccessDB
from security import token_hash
from routers.senhaRoute import agora

class SenhaTests(unittest.TestCase):
    setUp = fixtures.CompanySessionTests.setUp
    tearDown = fixtures.CompanySessionTests.tearDown
    login = fixtures.CompanySessionTests.login
    seed_mentors = fixtures.CompanySessionTests.seed_mentors
    mentor_login = fixtures.CompanySessionTests.mentor_login

    def solicitar(self, email='teste1@example.com', papel='empreendedor'):
        with patch('routers.senhaRoute.email_configurado', return_value=True), patch('routers.senhaRoute.enviar_redefinicao') as enviar:
            r = self.client.post('/auth/recuperar-senha', json={'email': email, 'papel': papel})
            token = parse_qs(urlsplit(enviar.call_args.args[1]).fragment)['token'][0] if enviar.called else None
            return r, token

    def trocar(self, token, senha='Uma senha nova segura!'):
        return self.client.post('/auth/redefinir-senha', json={'token': token, 'senha': senha})

    def test_troca_uso_unico_e_sessoes_revogadas(self):
        self.login()
        r, token = self.solicitar()
        self.assertEqual(r.status_code, 202)
        self.assertNotIn(token, r.text)
        with self.sessions() as db:
            self.assertIsNotNone(db.get(PasswordResetDB, token_hash(token)))
            self.assertIsNone(db.get(PasswordResetDB, token))
        self.assertEqual(self.trocar(token).status_code, 200)
        self.assertEqual(self.client.get('/auth/me').status_code, 401)
        self.assertEqual(self.trocar(token).status_code, 400)
        self.assertEqual(self.client.post('/auth/login', json={'email': 'teste1@example.com', 'senha': 'senha-teste'}).status_code, 401)
        self.assertEqual(self.client.post('/auth/login', json={'email': 'teste1@example.com', 'senha': 'Uma senha nova segura!'}).status_code, 200)

    def test_privacidade_limites_e_configuracao(self):
        existente, _ = self.solicitar()
        ausente, token = self.solicitar('naoexiste@example.com')
        self.assertEqual(existente.json(), ausente.json())
        self.assertIsNone(token)
        for _ in range(4):
            self.solicitar()
        resposta, token = self.solicitar()
        self.assertEqual(resposta.status_code, 202)
        self.assertIsNone(token)
        with patch('routers.senhaRoute.email_configurado', return_value=False):
            self.assertEqual(self.client.post('/auth/recuperar-senha', json={'email': 'teste1@example.com'}).status_code, 503)

    def test_expiracao_senha_fraca_e_origem(self):
        _, token = self.solicitar()
        self.assertEqual(self.trocar(token, 'curta').status_code, 422)
        self.assertEqual(self.trocar(token, ' '*12).status_code, 422)
        self.assertEqual(self.client.post('/auth/redefinir-senha', headers={'Origin': 'https://malicioso.invalid'}, json={'token': token, 'senha': 'Uma senha nova segura!'}).status_code, 403)
        with self.sessions() as db:
            db.get(PasswordResetDB, token_hash(token)).expires_at = agora()-timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.trocar(token).status_code, 400)
        self.assertEqual(self.trocar('a'*43).status_code, 400)

    def test_nova_senha_invalida_outros_links(self):
        _, primeiro = self.solicitar()
        _, segundo = self.solicitar()
        self.assertEqual(self.trocar(primeiro).status_code, 200)
        self.assertEqual(self.trocar(segundo).status_code, 400)

    def test_mentor_e_acesso_revogado(self):
        self.seed_mentors()
        self.mentor_login()
        r, token = self.solicitar('mentor1@example.com', 'mentor')
        self.assertEqual(r.status_code, 202)
        self.assertIsNotNone(token)
        self.assertEqual(self.trocar(token).status_code, 200)
        self.assertEqual(self.client.post('/auth/login', json={'email': 'mentor1@example.com', 'papel': 'mentor', 'senha': 'Uma senha nova segura!'}).status_code, 200)
        _, token = self.solicitar('mentor1@example.com', 'mentor')
        with self.sessions() as db:
            db.get(MentorAccessDB, 1).ativo = False
            db.commit()
        self.assertEqual(self.trocar(token).status_code, 400)
        _, ausente = self.solicitar('mentor1@example.com', 'mentor')
        self.assertIsNone(ausente)

    def test_smtp_usa_tls_e_mensagem_de_seguranca(self):
        from types import SimpleNamespace
        from pydantic import SecretStr
        from services.email_service import enviar_redefinicao
        config = SimpleNamespace(smtp_host='smtp.example.com', smtp_port=587, smtp_ssl=False,
                                 smtp_username='login', smtp_password=SecretStr('chave-teste'), smtp_from='seguranca@example.com')
        with patch('services.email_service.get_settings', return_value=config), patch('services.email_service.smtplib.SMTP') as smtp:
            cliente = smtp.return_value.__enter__.return_value
            # O serviço mantém a referência da conexão durante o contexto.
            smtp.return_value.__enter__.return_value = smtp.return_value
            enviar_redefinicao('destino@example.com', 'https://app.example.com/redefinir-senha#token=segredo')
            smtp.return_value.starttls.assert_called_once()
            smtp.return_value.login.assert_called_once_with('login', 'chave-teste')
            mensagem = smtp.return_value.send_message.call_args.args[0]
            self.assertEqual(mensagem['To'], 'destino@example.com')
            self.assertIn('30 minutos', mensagem.get_content())
            self.assertIn('#token=segredo', mensagem.get_content())
