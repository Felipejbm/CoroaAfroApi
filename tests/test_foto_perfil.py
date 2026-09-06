"""Upload, leitura e isolamento da foto; usa apenas SQLite em memória."""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SESSION_COOKIE_SECURE"] = "false"

from io import BytesIO
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateTable

from database import Base, get_db
from main import app
from models import EmpreendedorDB
from services.foto_perfil import LIMITE_FOTO


def imagem(formato="PNG", cor="red", tamanho=(800, 600)):
    buffer = BytesIO()
    Image.new("RGB", tamanho, cor).save(buffer, format=formato)
    return buffer.getvalue()


class FotoPerfilTests(unittest.TestCase):
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
                db.add(EmpreendedorDB(id_empreendedor=n, nome=f"Pessoa {n}",
                                     email=f"pessoa{n}@example.com", senha="senha-teste", telefone="11999999999"))
            db.commit()
        self.client = TestClient(app, headers={"Origin": "http://localhost:5173"})

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def login(self, n=1):
        resposta = self.client.post("/auth/login", json={"email": f"pessoa{n}@example.com", "senha": "senha-teste"})
        self.assertEqual(resposta.status_code, 200, resposta.text)

    def upload(self, conteudo=None, tipo="image/png", **kwargs):
        return self.client.put("/empreendedor/me/foto", files={
            "foto": ("foto.png", imagem() if conteudo is None else conteudo, tipo),
        }, **kwargs)

    def test_upload_persiste_e_reaparece_em_nova_sessao(self):
        self.login()
        self.assertIsNone(self.client.get("/auth/me").json()["foto_perfil_url"])
        self.assertEqual(self.client.get("/empreendedor/me/foto").status_code, 404)
        resposta = self.upload()
        self.assertEqual(resposta.status_code, 200, resposta.text)
        url = resposta.json()["foto_perfil_url"]
        self.assertNotIn("foto_perfil", resposta.json())
        self.client.post("/auth/logout")
        self.login()
        self.assertEqual(self.client.get("/auth/me").json()["foto_perfil_url"], url)
        foto = self.client.get(url)
        self.assertEqual(foto.status_code, 200)
        self.assertEqual(foto.headers["content-type"], "image/jpeg")
        self.assertIn("no-store", foto.headers["cache-control"])
        with Image.open(BytesIO(foto.content)) as normalizada:
            self.assertEqual(normalizada.size, (512, 384))
            self.assertEqual(normalizada.format, "JPEG")
            self.assertFalse(normalizada.getexif())
        with self.sessions() as db:
            self.assertEqual(db.get(EmpreendedorDB, 1).foto_perfil, foto.content)

    def test_substituicao_e_formatos(self):
        self.login()
        anterior = None
        for formato, tipo, cor in [("PNG", "image/png", "red"), ("JPEG", "image/jpeg", "blue"), ("WEBP", "image/webp", "green")]:
            resposta = self.upload(imagem(formato, cor), tipo)
            self.assertEqual(resposta.status_code, 200, resposta.text)
            url = resposta.json()["foto_perfil_url"]
            self.assertNotEqual(url, anterior)
            anterior = url

    def test_validacao_nao_sobrescreve_foto_anterior(self):
        self.login()
        self.upload()
        anterior = self.client.get("/empreendedor/me/foto").content
        for conteudo, tipo, status in [
            (b"", "image/png", 422),
            (b"nao sou imagem", "image/jpeg", 422),
            (b"<svg/>", "image/svg+xml", 422),
            (imagem("GIF"), "image/png", 422),
            (b"x" * (LIMITE_FOTO + 1), "image/png", 413),
        ]:
            self.assertEqual(self.upload(conteudo, tipo).status_code, status)
            self.assertEqual(self.client.get("/empreendedor/me/foto").content, anterior)
        with patch("services.foto_perfil.MAX_PIXELS", 1):
            self.assertEqual(self.upload().status_code, 422)

    def test_sessao_origem_e_isolamento(self):
        self.assertEqual(self.upload().status_code, 401)
        self.assertEqual(self.client.get("/empreendedor/me/foto").status_code, 401)
        self.login()
        self.assertEqual(self.upload(headers={"Origin": "https://outro.example"}).status_code, 403)
        self.upload()
        self.login(2)
        self.assertIsNone(self.client.get("/auth/me").json()["foto_perfil_url"])
        self.assertEqual(self.client.get("/empreendedor/me/foto").status_code, 404)
        self.assertEqual(self.client.get("/empreendedor/1/foto").status_code, 404)

    def test_mysql_usa_mediumblob(self):
        sql = str(CreateTable(EmpreendedorDB.__table__).compile(dialect=mysql.dialect()))
        self.assertIn("foto_perfil MEDIUMBLOB", sql)


if __name__ == "__main__":
    unittest.main()
