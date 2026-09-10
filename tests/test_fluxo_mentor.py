import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["SESSION_COOKIE_SAMESITE"] = "lax"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"
import unittest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from database import Base, get_db
from models import MentorDB, MentorAccessDB, MentorSessionDB, EmpreendedorDB, AuthSessionDB, IaMentorConversaDB
from security import token_hash, COOKIE_NAME, verify_password
from services.ia_service import get_ia_service, IaResultado

class FakeIA:
    async def gerar_resposta(self, **kwargs):
        assert kwargs["contexto"]["papel"] == "mentor"
        assert "empresa" not in kwargs["contexto"]
        return IaResultado(texto="Roteiro de aula de teste", tokens_entrada=1, tokens_saida=1)

class FluxoMentorTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://", connect_args={"check_same_thread":False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions=sessionmaker(bind=self.engine)
        def db_override():
            with self.sessions() as db: yield db
        app.dependency_overrides[get_db]=db_override
        app.dependency_overrides[get_ia_service]=lambda: FakeIA()
        with self.sessions() as db:
            for i in (1,2):
                db.add(MentorDB(id_mentor=i,nome=f"Mentor {i}",especialidade="Gestão",biografia=""))
                db.add(MentorAccessDB(id_mentor=i,email=f"mentor{i}@example.com",senha_hash="senha-teste",ativo=True,administrador=i==1))
                db.add(MentorSessionDB(token_hash=token_hash(f"mentor{i}"),id_mentor=i,expires_at=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(hours=1)))
            db.add(EmpreendedorDB(id_empreendedor=1,nome="Empreendedor",email="e@example.com",senha="x",telefone="11999999999"))
            db.add(AuthSessionDB(token_hash=token_hash("empreendedor"),id_empreendedor=1,expires_at=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(hours=1)))
            db.commit()
        self.client=TestClient(app,headers={"Origin":"http://localhost:5173"})
        self.identidade("mentor1")
    def identidade(self, value):
        self.client.cookies.clear()
        self.client.cookies.set(COOKIE_NAME,value)
    def tearDown(self):
        self.client.close();app.dependency_overrides.clear();self.engine.dispose()
    def test_admin_creation_validation_and_revoke(self):
        dados=dict(nome="Novo mentor",email="novo@example.com",especialidade="Marketing",biografia="",senha="senha-inicial-123")
        r=self.client.post("/mentoria/admin/mentores",json=dados)
        self.assertEqual(r.status_code,201,r.text)
        self.assertFalse(r.json()["administrador"])
        self.assertNotIn("senha",r.text)
        with self.sessions() as db:
            self.assertTrue(verify_password(dados["senha"],db.get(MentorAccessDB,r.json()["id"]).senha_hash))
        self.assertEqual(self.client.post("/mentoria/admin/mentores",json=dados).status_code,409)
        self.assertEqual(self.client.post("/mentoria/admin/mentores",json={**dados,"administrador":True}).status_code,422)
        self.assertEqual(self.client.patch("/mentoria/admin/mentores/1/acesso",json={"ativo":False}).status_code,409)
        self.assertEqual(self.client.patch("/mentoria/admin/mentores/2/acesso",json={"ativo":False}).status_code,200)
        self.identidade("mentor2")
        self.assertEqual(self.client.get("/mentoria/perfil").status_code,401)
    def test_non_admin_and_entrepreneur_forbidden(self):
        self.identidade("mentor2")
        self.assertEqual(self.client.get("/mentoria/admin/mentores").status_code,403)
        self.identidade("empreendedor")
        self.assertIn(self.client.get("/mentoria/admin/mentores").status_code,(401,403))
        self.assertIn(self.client.get("/ia/mentor/conversas").status_code,(401,403))
    def test_profile_and_csrf(self):
        dados=dict(nome="Nome atualizado",email="mentor1@example.com",especialidade="Finanças",biografia="Descrição")
        self.assertEqual(self.client.patch("/mentoria/perfil",json=dados).status_code,200)
        self.assertTrue(self.client.get("/auth/me").json()["administrador"])
        self.assertEqual(self.client.get("/auth/me").json()["nome"],dados["nome"])
        self.assertEqual(self.client.patch("/mentoria/perfil",json={**dados,"administrador":False}).status_code,422)
        self.assertEqual(self.client.patch("/mentoria/perfil",json=dados,headers={"Origin":"https://evil.example"}).status_code,403)
    def test_ai_ownership_history_and_archive(self):
        r=self.client.post("/ia/mentor/conversas",json={"titulo":"Preparar aula"})
        self.assertEqual(r.status_code,201,r.text)
        id=r.json()["id_conversa"]
        self.assertEqual(self.client.post(f"/ia/mentor/conversas/{id}/mensagens",json={"conteudo":"Preparar uma aula"}).status_code,200)
        self.assertEqual(len(self.client.get(f"/ia/mentor/conversas/{id}/mensagens").json()),2)
        self.identidade("mentor2")
        self.assertEqual(self.client.get("/ia/mentor/conversas").json(),[])
        self.assertEqual(self.client.get(f"/ia/mentor/conversas/{id}/mensagens").status_code,404)
        self.identidade("empreendedor")
        self.assertEqual(self.client.get("/ia/conversas").json(),[])
        self.identidade("mentor1")
        self.assertEqual(self.client.patch(f"/ia/mentor/conversas/{id}/arquivar").status_code,204)
        self.assertEqual(self.client.get("/ia/mentor/conversas").json(),[])
