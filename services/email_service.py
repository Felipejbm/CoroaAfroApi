"""Envio SMTP com TLS obrigatório. Nunca registra destinatário, senha ou token."""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from config import get_settings


def email_configurado():
    s = get_settings()
    return bool(s.smtp_host and s.smtp_from and (not s.smtp_username or s.smtp_password))


def enviar_redefinicao(destinatario: str, link: str):
    s = get_settings()
    mensagem = EmailMessage()
    mensagem['Subject'] = 'Redefinição de senha — Coroa Afro'
    mensagem['From'] = s.smtp_from
    mensagem['To'] = destinatario
    mensagem.set_content(
        'Recebemos uma solicitação para redefinir sua senha no Coroa Afro.\n\n'
        f'Para escolher uma nova senha, abra este link:\n{link}\n\n'
        'O link expira em 30 minutos e só pode ser usado uma vez.\n'
        'Se você não fez esta solicitação, ignore este e-mail. Sua senha continua a mesma.\n'
        'Não compartilhe este link. A equipe nunca pede sua senha por e-mail.\n'
    )
    try:
        cliente = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, timeout=15, context=ssl.create_default_context()) if s.smtp_ssl else smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15)
        with cliente:
            if not s.smtp_ssl:
                cliente.starttls(context=ssl.create_default_context())
            if s.smtp_username:
                cliente.login(s.smtp_username, s.smtp_password.get_secret_value())
            cliente.send_message(mensagem)
    except (OSError, smtplib.SMTPException):
        logging.getLogger(__name__).error('Falha no envio de redefinição. Confira a configuração e a disponibilidade do SMTP.')
