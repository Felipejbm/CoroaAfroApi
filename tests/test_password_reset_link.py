"""Recuperação real, com entrega externa simulada."""
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from types import SimpleNamespace
from pydantic import SecretStr
import test_company_session as fixtures
from models import PasswordResetTokenDB, EmpreendedorDB, MentorDB, MentorAccessDB, MentorSessionDB
from security import token_hash, verify_password
from services.password_reset_email import send_reset_email


class PasswordResetLinkTests(unittest.TestCase):
    def setUp(self):
        fixtures.CompanySessionTests.setUp(self)
        self.configured = patch("routers.passwordResetRoute.configured", return_value=True)
        self.delivery = patch("routers.passwordResetRoute.send_reset_email")
        self.configured.start()
        self.mail = self.delivery.start()
        self.addCleanup(self.configured.stop)
        self.addCleanup(self.delivery.stop)

    def tearDown(self):
        fixtures.CompanySessionTests.tearDown(self)

    def request_link(self, email="teste1@example.com", papel="empreendedor"):
        return self.client.post("/auth/recuperar-senha", json={"email": email, "papel": papel})

    def reset(self, token):
        return self.client.post("/auth/redefinir-senha", json={"token": token, "senha": "Nova senha segura 2026"})

    def test_generic_response_and_hashed_storage(self):
        result = self.request_link()
        token = self.mail.call_args.args[1]
        self.assertEqual(result.status_code, 202)
        self.assertNotIn(token, result.text)
        self.assertEqual(result.headers["cache-control"], "no-store")
        self.mail.reset_mock()
        self.assertEqual(self.request_link("ausente@example.com").json(), result.json())
        self.mail.assert_not_called()
        with self.sessions() as db:
            record = db.get(PasswordResetTokenDB, token_hash(token))
            self.assertIsNotNone(record)
            self.assertEqual(record.expires_at - record.criado_em, timedelta(minutes=30))

    def test_single_use_and_session_revocation(self):
        fixtures.CompanySessionTests.login(self)
        self.request_link()
        token = self.mail.call_args.args[1]
        self.assertEqual(self.reset(token).status_code, 200)
        self.assertEqual(self.reset(token).status_code, 400)
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        with self.sessions() as db:
            self.assertTrue(verify_password("Nova senha segura 2026", db.get(EmpreendedorDB, 1).senha))

    def test_expired_link(self):
        self.request_link()
        token = self.mail.call_args.args[1]
        with self.sessions() as db:
            db.get(PasswordResetTokenDB, token_hash(token)).expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.reset(token).status_code, 400)

    def test_changed_password_or_email_invalidates_link(self):
        for field, value in (("senha", "changed-password"), ("email", "changed@example.com")):
            self.request_link()
            token = self.mail.call_args.args[1]
            with self.sessions() as db:
                setattr(db.get(EmpreendedorDB, 1), field, value)
                db.commit()
            self.assertEqual(self.reset(token).status_code, 400)

    def test_validation_configuration_and_limit(self):
        self.assertEqual(self.request_link("invalid").status_code, 422)
        self.assertEqual(self.reset("bad").status_code, 422)
        with patch("routers.passwordResetRoute.configured", return_value=False):
            self.assertEqual(self.request_link().status_code, 503)
        for _ in range(6):
            self.assertEqual(self.request_link().status_code, 202)
        self.assertEqual(self.mail.call_count, 5)
        token = self.mail.call_args.args[1]
        self.assertEqual(self.client.post("/auth/redefinir-senha", json={"token": token, "senha": "            a"}).status_code, 422)

    def test_mentor_and_revocation(self):
        with self.sessions() as db:
            db.add(MentorDB(id_mentor=77, nome="Mentor", especialidade="Gestão", biografia="Mentor de teste"))
            db.flush()
            db.add(MentorAccessDB(id_mentor=77, email="mentor@example.com", senha_hash="senha", ativo=True))
            db.add(MentorSessionDB(id_mentor=77, token_hash=token_hash("session"), expires_at=datetime.utcnow()+timedelta(hours=1)))
            db.commit()
        self.assertEqual(self.request_link("mentor@example.com", "mentor").status_code, 202)
        self.assertEqual(self.reset(self.mail.call_args.args[1]).status_code, 200)
        with self.sessions() as db:
            self.assertEqual(db.query(MentorSessionDB).count(), 0)
            self.assertTrue(verify_password("Nova senha segura 2026", db.get(MentorAccessDB, 77).senha_hash))

    def test_transport_rejection_and_success(self):
        cfg = SimpleNamespace(brevo_api_key=SecretStr("test-secret"), smtp_from="sender@example.com", frontend_origin="https://front.example.com")
        with patch("services.password_reset_email.get_settings", return_value=cfg), patch("services.password_reset_email.httpx.Client") as factory:
            client = factory.return_value.__enter__.return_value
            client.post.return_value.status_code = 400
            with self.assertLogs("services.password_reset_email", level="ERROR") as logs:
                self.assertFalse(send_reset_email("teste1@example.com", "private-token"))
            self.assertNotIn("private-token", str(logs.output))
            self.assertNotIn("test-secret", str(logs.output))
            client.post.return_value.status_code = 201
            self.assertTrue(send_reset_email("teste1@example.com", "private-token"))
            payload = client.post.call_args.kwargs
            self.assertIn("https://front.example.com/redefinir-senha#token=private-token", payload["json"]["textContent"])
            self.assertEqual(payload["headers"]["api-key"], "test-secret")
