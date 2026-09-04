import hashlib
import hmac
import secrets
from fastapi import HTTPException, Request
from config import get_settings

COOKIE_NAME = "coroa_session"
PASSWORD_ITERATIONS = 600_000


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"

def verify_password(password: str, stored: str) -> bool:
    if not stored.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(password.encode(), stored.encode())
    try:
        _, iterations, salt, expected = stored.split("$")
        rounds = int(iterations)
        if rounds < 1 or rounds > 1_000_000:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), rounds)
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    own_origin = str(request.base_url).rstrip("/")
    allowed_origin = get_settings().frontend_origin.rstrip("/")

    if origin and origin not in {allowed_origin, own_origin}:
        raise HTTPException(403, "Origem da solicitação não autorizada.")
    if not origin and request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Origem da solicitação não autorizada.")