"""Testes isolados: não conecta ao MySQL nem chama a Meta."""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SESSION_COOKIE_SECURE"] = "false"
import unittest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable
from main import app
from database import Base, get_db
from models import AuthSessionDB, EmpreendedorDB, MetaInstagramConnectionDB
from security import COOKIE_NAME, token_hash


class CompanySessionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        def db_override():
            with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = db_override
        with self.sessions() as db:
            for n in (1, 2):
                db.add(EmpreendedorDB(id_empreendedor=n, nome=f"Teste {n}", email=f"teste{n}@example.com",
                                      senha="senha-teste", telefone="11999999999"))
            db.commit()
        self.client = TestClient(app, headers={"Origin": "http://localhost:5173"})
        self.company = dict(nome="Empresa teste", data_fundacao="2020-01-01", cnpj="",
                            segmento="moda", rua="Rua teste", numero="S/N", bairro="Centro",
                            cidade="Mauá", estado="SP", cep="09300-000", porte="MEI", num_funcionarios=0)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def login(self, n=1):
        r = self.client.post("/auth/login", json={"email": f"teste{n}@example.com", "senha": "senha-teste"})
        self.assertEqual(r.status_code, 200, r.text)
        return r

    def test_login_logout_and_password_migration(self):
        r = self.login()
        self.assertIn("httponly", r.headers["set-cookie"].lower())
        self.assertNotIn("senha-teste", r.text)
        self.assertEqual(self.client.get("/auth/me").json()["id"], 1)
        with self.sessions() as db:
            self.assertTrue(db.get(EmpreendedorDB, 1).senha.startswith("pbkdf2_sha256$"))
        self.assertEqual(self.client.post("/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/auth/me").status_code, 401)

    def test_no_session(self):
        for url in ("/auth/me", "/empresa", "/empresa/minha", "/empreendedor",
                    "/empreendedor/1", "/instagram/profile?empreendedor_id=1"):
            self.assertEqual(self.client.get(url).status_code, 401, url)
        self.assertEqual(self.client.post("/empresa/criar-empresa", json=self.company).status_code, 401)

    def meta_payload(self, **changes):
        return {"titulo": "Crescer no Instagram", "unidade": "seguidores", "valor_inicial": "100.00",
                "valor_atual": "150.00", "valor_alvo": "200.00", "prazo": "2099-12-31", **changes}

    def test_goals_create_edit_archive_restore(self):
        self.assertEqual(self.client.get("/metas").status_code, 401)
        self.assertEqual(self.client.post("/metas", json=self.meta_payload()).status_code, 401)
        self.login()
        self.assertEqual(self.client.get("/metas").json(), [])
        r = self.client.post("/metas", json=self.meta_payload())
        self.assertEqual(r.status_code, 201, r.text)
        meta = r.json()
        self.assertEqual(meta["progresso"], 50)
        self.assertEqual(meta["origem"], "manual")
        self.assertEqual(self.client.get("/metas").json()[0]["id"], meta["id"])
        for version, archived, status in ((1, True, "arquivada"), (2, False, "atingida")):
            r = self.client.patch(f"/metas/{meta['id']}", json=self.meta_payload(valor_atual="220", arquivada=archived, versao=version))
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()["status"], status)
            self.assertEqual(r.json()["progresso"], 100)
        self.assertEqual(self.client.patch(f"/metas/{meta['id']}", json=self.meta_payload(versao=1)).status_code, 409)
        self.assertEqual(self.client.get("/metas").json()[0]["versao"], 3)

    def test_goals_owner_role_and_origin(self):
        self.login()
        meta = self.client.post("/metas", json=self.meta_payload()).json()
        self.login(2)
        self.assertEqual(self.client.get("/metas").json(), [])
        self.assertEqual(self.client.patch(f"/metas/{meta['id']}", json=self.meta_payload(versao=1)).status_code, 404)
        self.assertEqual(self.client.post("/metas", headers={"Origin": "https://untrusted.invalid"}, json=self.meta_payload()).status_code, 403)
        self.seed_mentors(); self.mentor_login()
        self.assertEqual(self.client.get("/metas").status_code, 401)

    def test_goals_validation_and_overdue(self):
        self.login()
        for changes in ({"titulo": " "}, {"unidade": ""}, {"valor_atual": "-1"}, {"valor_alvo": "100"},
                        {"valor_alvo": "NaN"}, {"valor_alvo": "Infinity"}, {"valor_atual": "1.001"},
                        {"valor_alvo": "1000000000000"}, {"prazo": "invalido"}, {"id_empreendedor": 2}):
            r = self.client.post("/metas", json=self.meta_payload(**changes))
            self.assertEqual(r.status_code, 422, r.text)
        r = self.client.post("/metas", json=self.meta_payload(valor_atual="50", prazo="2000-01-01"))
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["progresso"], 0)
        self.assertEqual(r.json()["status"], "prazo_encerrado")

    def seed_mentors(self):
        from models import MentorDB, MentorAccessDB, MentoriaDB
        from security import hash_password
        password_hash = hash_password("senha-mentor-teste")
        with self.sessions() as db:
            for n in (1, 2):
                db.add(MentorDB(id_mentor=n, nome=f"Mentor {n}", especialidade="Marketing", biografia=""))
                db.flush()
                db.add(MentorAccessDB(id_mentor=n, email=f"mentor{n}@example.com", senha_hash=password_hash, ativo=True))
            db.add(MentoriaDB(id_mentor=1, id_empreendedor=1, ativo=True))
            db.commit()

    def mentor_login(self, n=1):
        return self.client.post("/auth/login", json={"email": f"mentor{n}@example.com",
                               "senha": "senha-mentor-teste", "papel": "mentor"})

    def test_mentor_login_and_scope(self):
        self.seed_mentors()
        self.assertEqual(self.mentor_login().status_code, 200)
        self.assertEqual(self.client.get("/auth/me").json()["papel"], "mentor")
        self.assertEqual(self.client.get("/mentoria/mentorados").json(), [{"id": 1, "nome": "Teste 1", "empresa": None}])
        self.assertEqual(self.client.get("/mentoria/mentorados/1").status_code, 200)
        self.assertEqual(self.client.get("/mentoria/mentorados/2").status_code, 404)
        for url in ("/empresa/minha", "/empreendedor/1", "/instagram/profile"):
            self.assertEqual(self.client.get(url).status_code, 401, url)
        self.assertEqual(self.mentor_login(2).status_code, 200)
        self.assertEqual(self.client.get("/mentoria/mentorados").json(), [])
        self.assertEqual(self.client.get("/mentoria/mentorados/1").status_code, 404)

    def test_mentor_revoked_access_and_link(self):
        from models import MentorAccessDB, MentoriaDB
        self.seed_mentors(); self.mentor_login()
        with self.sessions() as db:
            db.get(MentoriaDB, (1, 1)).ativo = False; db.commit()
        self.assertEqual(self.client.get("/mentoria/mentorados/1").status_code, 404)
        with self.sessions() as db:
            db.get(MentorAccessDB, 1).ativo = False; db.commit()
        self.assertEqual(self.client.get("/auth/me").status_code, 403)
        self.assertEqual(self.mentor_login().status_code, 401)

    def test_role_cannot_be_self_granted(self):
        self.seed_mentors()
        self.login()
        self.assertEqual(self.client.get("/mentoria/mentorados").status_code, 401)
        self.assertEqual(self.client.post("/auth/login", json={"email": "teste1@example.com", "senha": "senha-teste", "papel": "mentor"}).status_code, 401)
        self.assertEqual(self.client.post("/auth/login", json={"email": "teste1@example.com", "senha": "senha-teste", "papel": "admin"}).status_code, 422)

    def test_mentor_expiration_logout_and_switch(self):
        from models import MentorSessionDB
        self.seed_mentors(); self.mentor_login()
        old_cookie = self.client.cookies.get(COOKIE_NAME)
        self.login()
        with self.sessions() as db:
            self.assertIsNone(db.get(MentorSessionDB, token_hash(old_cookie)))
        self.mentor_login()
        with self.sessions() as db:
            session = db.get(MentorSessionDB, token_hash(self.client.cookies.get(COOKIE_NAME)))
            session.expires_at = datetime.utcnow() - timedelta(seconds=1); db.commit()
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.mentor_login()
        self.assertEqual(self.client.post("/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/mentoria/mentorados").status_code, 401)

    def test_legacy_modules_fail_closed(self):
        for url in ("/mentor", "/trilha", "/atividade", "/postagem"):
            self.assertEqual(self.client.get(url).status_code, 401, url)
        self.login()
        for url in ("/mentor", "/trilha", "/atividade", "/postagem"):
            self.assertEqual(self.client.get(url).status_code, 503, url)

    def test_company_create_edit_duplicate(self):
        self.login()
        self.assertEqual(self.client.get("/empresa/minha").status_code, 404)
        r = self.client.post("/empresa/criar-empresa", json=self.company)
        self.assertEqual(r.status_code, 201, r.text)
        cid = r.json()["Empresa"]["id_empresa"]
        self.assertEqual(self.client.get("/empresa/minha").json()["id_empresa"], cid)
        r = self.client.patch(f"/empresa/{cid}", json={**self.company, "nome": "Nome atualizado"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["nome"], "Nome atualizado")
        self.assertEqual(self.client.post("/empresa/criar-empresa", json=self.company).status_code, 409)

    def test_owner_isolation(self):
        self.login()
        cid = self.client.post("/empresa/criar-empresa", json=self.company).json()["Empresa"]["id_empresa"]
        self.login(2)
        self.assertEqual(self.client.get("/empresa").json(), [])
        self.assertEqual(self.client.get(f"/empresa/{cid}").status_code, 404)
        self.assertEqual(self.client.patch(f"/empresa/{cid}", json=self.company).status_code, 404)
        self.assertEqual(self.client.get("/empreendedor/1").status_code, 404)
        self.assertEqual(self.client.get("/instagram/profile?empreendedor_id=1").status_code, 403)

    def test_invalid_company(self):
        self.login()
        for changed in ({"num_funcionarios": -1}, {"nome": " "}, {"cnpj": "123"},
                        {"nome": "x" * 151}, {"segmento": "qualquer texto"}, {"porte": "aleatorio"},
                        {"estado": "XX"}, {"cidade": " "}, {"rua": ""}, {"cep": "12345"},
                        {"id_usuario": 5}, {"endereco": "formato antigo"},
                        {"data_fundacao": "2999-01-01"}, {"id_empreendedor": 2}):
            r = self.client.post("/empresa/criar-empresa", json={**self.company, **changed})
            self.assertEqual(r.status_code, 422, r.text)

    def test_company_real_column_mapping_and_blank_cnpj(self):
        from models import EmpresaDB, UsuarioDB, EmpreendedorUsuarioDB
        self.assertIn("nome_empresa", EmpresaDB.__table__.c)
        self.assertIn("numero_funcionarios", EmpresaDB.__table__.c)
        self.assertNotIn("nome", EmpresaDB.__table__.c)
        for n in (1, 2):
            self.login(n)
            r = self.client.post("/empresa/criar-empresa", json=self.company)
            self.assertEqual(r.status_code, 201, r.text)
            empresa = r.json()["Empresa"]
            self.assertEqual(empresa["cep"], "09300000")
            self.assertEqual(empresa["segmento_label"], "Moda e acessórios")
            self.assertIn("Mauá", empresa["endereco"])
            self.assertNotIn("id_usuario", empresa)
            with self.sessions() as db:
                row = db.get(EmpresaDB, empresa["id_empresa"])
                self.assertIsNone(row.cnpj)
                bridge = db.get(EmpreendedorUsuarioDB, n)
                self.assertEqual(row.id_usuario, bridge.id_usuario)
                self.assertTrue(db.get(UsuarioDB, bridge.id_usuario).senha.startswith("pbkdf2_sha256$"))

    def test_company_does_not_claim_existing_usuario(self):
        from models import UsuarioDB, EmpreendedorUsuarioDB
        with self.sessions() as db:
            db.add(UsuarioDB(nome="Pessoa antiga", email="teste1@example.com", senha="outro-hash"))
            db.commit()
        self.login()
        self.assertEqual(self.client.post("/empresa/criar-empresa", json=self.company).status_code, 409)
        with self.sessions() as db:
            self.assertIsNone(db.get(EmpreendedorUsuarioDB, 1))
            self.assertEqual(db.query(UsuarioDB).count(), 1)

    def test_profile_sync_and_company_cnpj_conflict_rollback(self):
        from models import UsuarioDB, EmpreendedorUsuarioDB
        self.login()
        payload = {**self.company, "cnpj": "12.345.678/0001-90"}
        self.assertEqual(self.client.post("/empresa/criar-empresa", json=payload).status_code, 201)
        self.assertEqual(self.client.patch("/empreendedor/1", json={"nome": "Nome sincronizado"}).status_code, 200)
        with self.sessions() as db:
            self.assertEqual(db.get(UsuarioDB, db.get(EmpreendedorUsuarioDB, 1).id_usuario).nome, "Nome sincronizado")
        self.login(2)
        self.assertEqual(self.client.post("/empresa/criar-empresa", json=payload).status_code, 409)
        with self.sessions() as db:
            self.assertIsNone(db.get(EmpreendedorUsuarioDB, 2))
            self.assertIsNone(db.query(UsuarioDB).filter_by(email="teste2@example.com").first())

    def test_legacy_company_address_preserved(self):
        from models import EmpresaDB
        self.login()
        cid = self.client.post("/empresa/criar-empresa", json=self.company).json()["Empresa"]["id_empresa"]
        with self.sessions() as db:
            row = db.get(EmpresaDB, cid)
            row.endereco = "Endereço antigo sem estrutura"
            row.rua = None
            row.data_fundacao = None
            row.num_funcionarios = None
            db.commit()
        r = self.client.get("/empresa/minha")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["endereco"], "Endereço antigo sem estrutura")
        self.assertIsNone(r.json()["data_fundacao"])
        r = self.client.patch(f"/empresa/{cid}", json=self.company)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["endereco_legado"], "Endereço antigo sem estrutura")

    def test_profile_edit(self):
        self.login()
        r = self.client.patch("/empreendedor/1", json={"nome": "Novo nome"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.client.get("/auth/me").json()["nome"], "Novo nome")
        self.assertNotIn("senha", self.client.get("/empreendedor").text)

    def test_expired_and_fake_session(self):
        self.login()
        with self.sessions() as db:
            session = db.get(AuthSessionDB, token_hash(self.client.cookies[COOKIE_NAME]))
            session.expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.client.cookies.clear()
        self.client.cookies.set(COOKIE_NAME, "fake")
        self.assertEqual(self.client.get("/auth/me").status_code, 401)

    def test_cross_origin(self):
        self.login()
        r = self.client.post("/empresa/criar-empresa", json=self.company, headers={"Origin": "https://evil.example"})
        self.assertEqual(r.status_code, 403)

    def test_forged_oauth_callback(self):
        self.login()
        self.assertEqual(self.client.get("/auth/meta/callback?state=forged&code=fake").status_code, 400)

    def test_mysql_schema(self):
        for table in Base.metadata.sorted_tables:
            str(CreateTable(table).compile(dialect=mysql.dialect()))

    def test_signup_never_returns_password(self):
        payload = dict(nome="Nova conta", email="nova@example.com", senha="senha-nova",
                       telefone="11999999999", data_cadastro="2026-08-30")
        r = self.client.post("/empreendedor", json=payload)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertNotIn("senha", r.text)
        with self.sessions() as db:
            user = db.query(EmpreendedorDB).filter_by(email="nova@example.com").one()
            self.assertTrue(user.senha.startswith("pbkdf2_sha256$"))
        self.assertEqual(self.client.post("/empreendedor", json=payload).status_code, 409)

    def test_oauth_callback_is_single_use(self):
        self.login()
        fake = Mock()
        fake.authorization_url.return_value = "https://www.facebook.com/dialog/oauth?state=test-state"
        fake.read_state.return_value = 1
        fake.exchange_code = AsyncMock(return_value=("fake-user-token", None))
        fake.discover_instagram_accounts = AsyncMock(return_value=[dict(
            facebook_page_id="123", facebook_page_name="Teste",
            instagram_business_account_id="456", instagram_username="teste",
            page_access_token="fake-page-token",
        )])
        fake.encrypt_token.return_value = "encrypted-test-token"
        with patch("routers.instagramRoute._service", return_value=fake):
            self.assertEqual(self.client.get("/auth/meta", follow_redirects=False).status_code, 307)
            r = self.client.get("/auth/meta/callback?state=test-state&code=fake", follow_redirects=False)
            self.assertIn(r.status_code, (200, 303), r.text)
            self.assertNotIn("fake-page-token", r.text)
            self.assertEqual(self.client.get("/auth/meta/callback?state=test-state&code=fake").status_code, 400)
        with self.sessions() as db:
            connection = db.query(MetaInstagramConnectionDB).one()
            self.assertEqual(connection.id_empreendedor, 1)
            self.assertEqual(connection.access_token_encrypted, "encrypted-test-token")


if __name__ == "__main__":
    unittest.main()
