"""Mots de passe, tokens JWT et contrôle des rôles."""
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend.app.core.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> bytes:
    # bcrypt est volontairement LENT : ça rend les attaques par force brute très coûteuses.
    # gensalt() ajoute un "sel" aléatoire : deux mêmes mots de passe ont des hash différents.
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


# Utilisateurs de démonstration. En vrai : une table "users" en base, et aucun mot de passe dans le code.
USERS = {
    "admin": {"password_hash": hash_password("admin123"), "role": "admin"},
    "analyste": {"password_hash": hash_password("analyste123"), "role": "analyst"},
}


def authenticate(username: str, password: str) -> dict | None:
    user = USERS.get(username)
    if user and bcrypt.checkpw(password.encode(), user["password_hash"]):
        return user
    return None


def create_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "role": role, "exp": expire}    # "sub" = le sujet (qui est connecté)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


# Dit à FastAPI : "le token arrive dans l'en-tête Authorization: Bearer <token>".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dépendance : FastAPI l'exécute AVANT la route et lui passe le résultat."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])  # vérifie signature + expiration
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalide ou expiré")
    return {"username": payload["sub"], "role": payload["role"]}


def require_role(*roles: str):
    """Fabrique une dépendance qui n'accepte que certains rôles.  Ex. : Depends(require_role("admin"))."""
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Votre rôle ne permet pas cette action")
        return user
    return checker
