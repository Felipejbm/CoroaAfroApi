"""Entrega de links pelo HTTPS do Brevo; nunca registra chave ou token."""
import logging
import httpx
from pydantic import TypeAdapter, EmailStr, ValidationError
from config import get_settings

logger = logging.getLogger(__name__)


def configured():
    cfg = get_settings()
    if not cfg.brevo_api_key or not cfg.brevo_api_key.get_secret_value().strip():
        return False
    try:
        TypeAdapter(EmailStr).validate_python(cfg.smtp_from)
    except ValidationError:
        return False
    return True


def send_reset_email(email: str, token: str):
    cfg = get_settings()
    link = cfg.frontend_origin + "/redefinir-senha#token=" + token
    try:
        with httpx.Client(timeout=15.0) as client:
            result = client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": cfg.brevo_api_key.get_secret_value()},
                json={
                    "sender": {"email": cfg.smtp_from, "name": "Coroa Afro"},
                    "to": [{"email": email}],
                    "subject": "Redefina sua senha — Coroa Afro",
                    "textContent": "Para redefinir sua senha, abra: " + link
                    + "\nEste link expira em 30 minutos e pode ser usado uma vez."
                    + "\nSe você não solicitou a alteração, ignore este e-mail.",
                },
            )
        if result.status_code != 201:
            logger.error("Brevo rejeitou a recuperação: HTTP %s. Confira chave, remetente validado e limites no painel.", result.status_code)
            return False
        logger.info("Brevo aceitou o e-mail de recuperação; confira a entrega no painel transacional.")
        return True
    except httpx.HTTPError:
        logger.error("Falha de conexão HTTPS com Brevo no envio de recuperação.")
        return False
