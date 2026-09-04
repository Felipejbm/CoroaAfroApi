"""Operações restritas à equipe no computador do backend. Senhas nunca vão nos argumentos."""
import argparse
from getpass import getpass
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
from models import MentorDB, MentorAccessDB, MentorSessionDB, MentoriaDB, EmpreendedorDB
from security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Autorizar mentores e vínculos (uso local da equipe).")
    commands = parser.add_subparsers(dest="acao", required=True)
    create = commands.add_parser("criar-mentor")
    create.add_argument("--nome", required=True)
    create.add_argument("--email", required=True)
    create.add_argument("--especialidade", required=True)
    create.add_argument("--biografia", default="")
    link = commands.add_parser("vincular")
    link.add_argument("--mentor", type=int, required=True)
    link.add_argument("--empreendedor", type=int, required=True)
    link.add_argument("--remover", action="store_true")
    disable = commands.add_parser("desativar-mentor")
    disable.add_argument("--mentor", type=int, required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.acao == "criar-mentor":
            email, nome, especialidade = args.email.strip().lower(), args.nome.strip(), args.especialidade.strip()
            if not nome or len(nome) > 255 or not especialidade or len(especialidade) > 50 or "@" not in email or len(email) > 255:
                parser.error("Revise nome, email e especialidade (máximo 50 caracteres).")
            if db.query(MentorAccessDB).filter_by(email=email).first():
                parser.error("Já existe acesso de mentor para esse email.")
            print(f"Autorizar novo mentor: {nome} ({email})")
            if input("Confirma a autorização pela equipe? Digite SIM: ") != "SIM":
                print("Cancelado. Nada foi alterado."); return
            password = getpass("Senha inicial (mínimo 12 caracteres): ")
            if len(password) < 12 or len(password) > 1024 or password != getpass("Confirme a senha: "):
                parser.error("Senhas não conferem ou tamanho inválido. Nada foi salvo.")
            mentor = MentorDB(nome=nome, especialidade=especialidade, biografia=args.biografia)
            db.add(mentor); db.flush()
            db.add(MentorAccessDB(id_mentor=mentor.id_mentor, email=email, senha_hash=hash_password(password), ativo=True))
            db.commit()
            print(f"Mentor autorizado. ID: {mentor.id_mentor}. A senha não será exibida.")
        else:
            mentor = db.get(MentorDB, args.mentor)
            access = db.get(MentorAccessDB, args.mentor)
            if not mentor or not access:
                parser.error("Mentor autorizado não encontrado.")
            if args.acao == "desativar-mentor":
                if input(f"Desativar acesso de {mentor.nome}? Digite SIM: ") != "SIM":
                    print("Cancelado."); return
                access.ativo = False
                db.query(MentorSessionDB).filter_by(id_mentor=mentor.id_mentor).delete()
            else:
                user = db.get(EmpreendedorDB, args.empreendedor)
                if not user or (not access.ativo and not args.remover):
                    parser.error("Empreendedor não encontrado ou mentor desativado.")
                action = "Remover vínculo" if args.remover else "Autorizar acompanhamento"
                if input(f"{action}: {mentor.nome} → {user.nome}? Digite SIM: ") != "SIM":
                    print("Cancelado."); return
                key = (mentor.id_mentor, user.id_empreendedor)
                relation = db.get(MentoriaDB, key)
                if not relation:
                    relation = MentoriaDB(id_mentor=key[0], id_empreendedor=key[1])
                    db.add(relation)
                relation.ativo = not args.remover
            db.commit()
            print("Alteração concluída.")


if __name__ == "__main__":
    try:
        main()
    except IntegrityError:
        raise SystemExit("Não foi possível salvar: registro duplicado ou vínculo inválido.")
