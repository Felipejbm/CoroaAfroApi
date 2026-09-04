"""Teste opt-in da API no schema MySQL real, com savepoints e rollback integral dos registros."""
import argparse
import secrets
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from database import engine, get_db
from main import app
from models import EmpreendedorDB, UsuarioDB, EmpresaDB, EmpreendedorUsuarioDB
from security import hash_password


def verificar():
    if engine.dialect.name not in {"mysql", "mariadb"} or engine.url.database != "coroa-afro":
        raise RuntimeError("Teste limitado ao MySQL coroa-afro.")
    tabelas = {"usuario", "empreendedor", "empresa", "empresa_empreendedor", "empreendedor_usuario", "auth_session"}
    with engine.connect() as preflight:
        rows = preflight.execute(text("SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()"))
        engines = dict(rows.all())
        if any(engines.get(t) != "InnoDB" for t in tabelas):
            raise RuntimeError("Rollback exige InnoDB em todas as tabelas envolvidas.")
        triggers = preflight.execute(text("SELECT EVENT_OBJECT_TABLE FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()"))
        if any(row[0] in tabelas for row in triggers):
            raise RuntimeError("Há triggers nas tabelas envolvidas; teste interrompido para revisão.")
    assert {"nome_empresa", "numero_funcionarios", "id_usuario", "cidade", "estado"}.issubset(
        {c["name"] for c in inspect(engine).get_columns("empresa")})
    run = secrets.token_hex(10)
    emails = [f"smoke-{run}-{n}@example.invalid" for n in (1, 2)]
    senha = secrets.token_urlsafe(24)
    conn = engine.connect()
    transaction = conn.begin()
    sessions = sessionmaker(bind=conn, join_transaction_mode="create_savepoint")
    def override():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = override
    try:
        with sessions() as db:
            for email in emails:
                db.add(EmpreendedorDB(nome="Teste transacional descartável", email=email,
                                      senha=hash_password(senha), telefone="11900000000"))
            db.commit()
        with TestClient(app, headers={"Origin": "http://localhost:5173"}) as client:
            ids = []
            for email in emails:
                assert client.post("/auth/login", json={"email": email, "senha": senha}).status_code == 200
                assert client.get("/empresa/minha").status_code == 404
                payload = dict(nome="Teste transacional", nome_fantasia="Teste", data_fundacao="2025-02-10",
                    cnpj="", segmento="alimentacao", porte="MEI", num_funcionarios=2, rua="Rua de teste",
                    numero="S/N", complemento="", bairro="Centro", cidade="Mauá", estado="SP", cep="09300-000")
                result = client.post("/empresa/criar-empresa", json=payload)
                assert result.status_code == 201, f"Cadastro respondeu {result.status_code}"
                company = result.json()["Empresa"]
                ids.append(company["id_empresa"])
                assert company["cidade"] == "Mauá" and company["cnpj"] == ""
                update = client.patch(f"/empresa/{ids[-1]}", json={**payload, "complemento": "Sala 2", "segmento": "moda"})
                assert update.status_code == 200
                assert client.get("/empresa/minha").json()["complemento"] == "Sala 2"
                if len(ids) > 1:
                    assert client.get(f"/empresa/{ids[0]}").status_code == 404
                assert client.post("/empresa/criar-empresa", json=payload).status_code == 409
            with sessions() as db:
                assert db.query(UsuarioDB).filter(UsuarioDB.email.in_(emails)).count() == 2
                for cid in ids:
                    company = db.get(EmpresaDB, cid)
                    assert company.id_usuario and company.cnpj is None
                    assert db.query(EmpreendedorUsuarioDB).filter_by(id_usuario=company.id_usuario).count() == 1
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        conn.close()
        with engine.connect() as check:
            for email in emails:
                assert check.execute(text("SELECT COUNT(*) FROM empreendedor WHERE email=:email"), {"email": email}).scalar() == 0
                assert check.execute(text("SELECT COUNT(*) FROM usuario WHERE email=:email"), {"email": email}).scalar() == 0
        print("Rollback verificado: nenhum cadastro de teste ficou salvo.")
    print("PASSOU: cadastro, edição, CNPJ opcional e isolamento no MySQL real.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    if parser.parse_args().run:
        verificar()
    else:
        print("Nada executado. Use --run para o teste transacional. IDs auto_increment podem ter lacunas após rollback.")
