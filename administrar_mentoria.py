import argparse
from getpass import getpass
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import SessionLocal
from models import EmpreendedorDB, MentorAccessDB, MentorDB, MentorSessionDB, MentoriaDB
from security import hash_password

def validate_mentor_creation_args(nome: str, email: str, especialidade: str) -> str | None:
    if not nome or len(nome) > 255:
        return "Nome inválido ou excede 255 caracteres."
    if not especialidade or len(especialidade) > 50:
        return "Especialidade é obrigatória e deve ter no máximo 50 caracteres."
    if "@" not in email or len(email) > 255:
        return "E-mail em formato inválido ou excede 255 caracteres."
    return None

def confirm_action(message: str) -> bool:
    """Solicita confirmação explícita 'SIM' do usuário."""
    return input(f"{message} Digite SIM: ").strip() == "SIM"

def handle_criar_mentor(args: argparse.Namespace, db: Session, parser: argparse.ArgumentParser):
    nome = args.nome.strip()
    email = args.email.strip().lower()
    especialidade = args.especialidade.strip()

    error_msg = validate_mentor_creation_args(nome, email, especialidade)
    if error_msg:
        parser.error(error_msg)

    if db.query(MentorAccessDB).filter_by(email=email).first():
        parser.error("Já existe acesso de mentor cadastrado para este e-mail.")

    print(f"Autorizar novo mentor: {nome} ({email})")
    if not confirm_action("Confirma a autorização pela equipe?"):
        print("Cancelado. Nada foi alterado.")
        return

    password = getpass("Senha inicial (mínimo 12 caracteres): ")
    if len(password) < 12 or len(password) > 1024 or password != getpass("Confirme a senha: "):
        parser.error("Senhas não conferem ou tamanho inválido. Nada foi salvo.")

    mentor = MentorDB(nome=nome, especialidade=especialidade, biografia=args.biografia)
    db.add(mentor)
    db.flush()

    db.add(
        MentorAccessDB(
            id_mentor=mentor.id_mentor,
            email=email,
            senha_hash=hash_password(password),
            ativo=True,
        )
    )
    db.commit()
    print(f"Mentor autorizado com sucesso. ID: {mentor.id_mentor}.")


def handle_desativar_mentor(args: argparse.Namespace, db: Session, parser: argparse.ArgumentParser):
    mentor = db.get(MentorDB, args.mentor)
    access = db.get(MentorAccessDB, args.mentor)

    if not mentor or not access:
        parser.error("Mentor autorizado não encontrado.")

    if not confirm_action(f"Desativar acesso de {mentor.nome}?"):
        print("Cancelado.")
        return

    access.ativo = False
    db.query(MentorSessionDB).filter_by(id_mentor=mentor.id_mentor).delete()
    db.commit()
    print("Mentor desativado com sucesso.")


def handle_vincular(args: argparse.Namespace, db: Session, parser: argparse.ArgumentParser):
    mentor = db.get(MentorDB, args.mentor)
    access = db.get(MentorAccessDB, args.mentor)

    if not mentor or not access:
        parser.error("Mentor autorizado não encontrado.")

    user = db.get(EmpreendedorDB, args.empreendedor)
    if not user or (not access.ativo and not args.remover):
        parser.error("Empreendedor não encontrado ou mentor desativado.")

    action_label = "Remover vínculo" if args.remover else "Autorizar acompanhamento"
    if not confirm_action(f"{action_label}: {mentor.nome} → {user.nome}?"):
        print("Cancelado.")
        return

    key = (mentor.id_mentor, user.id_empreendedor)
    relation = db.get(MentoriaDB, key)

    if not relation:
        relation = MentoriaDB(id_mentor=key[0], id_empreendedor=key[1])
        db.add(relation)

    relation.ativo = not args.remover
    db.commit()
    print("Alteração de vínculo concluída.")

def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Autorizar mentores e vínculos (uso local da equipe).")
    commands = parser.add_subparsers(dest="acao", required=True)

    create = commands.add_parser("criar-mentor", help="Cria e autoriza um novo mentor")
    create.add_argument("--nome", required=True, help="Nome do mentor")
    create.add_argument("--email", required=True, help="E-mail de acesso")
    create.add_argument("--especialidade", required=True, help="Especialidade do mentor")
    create.add_argument("--biografia", default="", help="Biografia do mentor (opcional)")

    disable = commands.add_parser("desativar-mentor", help="Desativa o acesso de um mentor")
    disable.add_argument("--mentor", type=int, required=True, help="ID do mentor")

    link = commands.add_parser("vincular", help="Vincula ou desvincula um mentor a um empreendedor")
    link.add_argument("--mentor", type=int, required=True, help="ID do mentor")
    link.add_argument("--empreendedor", type=int, required=True, help="ID do empreendedor")
    link.add_argument("--remover", action="store_true", help="Remove o vínculo existente")

    return parser

def main():
    parser = build_cli_parser()
    args = parser.parse_args()

    handlers = {
        "criar-mentor": handle_criar_mentor,
        "desativar-mentor": handle_desativar_mentor,
        "vincular": handle_vincular,
    }

    with SessionLocal() as db:
        handler = handlers[args.acao]
        handler(args, db, parser)


if __name__ == "__main__":
    try:
        main()
    except IntegrityError:
        raise SystemExit("Não foi possível salvar: registro duplicado ou vínculo inválido.")