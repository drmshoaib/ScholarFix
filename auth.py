"""Firebase authentication helpers."""

from __future__ import annotations

import logging

import firebase_admin
from firebase_admin import auth, credentials

from config import FIREBASE_CREDENTIALS_PATH

LOGGER = logging.getLogger(__name__)


def _ensure_firebase_app() -> None:
    """Initialise Firebase Admin once if credentials are available."""
    if firebase_admin._apps:
        return

    if not FIREBASE_CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            "Firebase credentials were not found. Set FIREBASE_CREDENTIALS_PATH."
        )

    cred = credentials.Certificate(str(FIREBASE_CREDENTIALS_PATH))
    firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token: str) -> dict[str, str] | None:
    """Verify a Firebase ID token and return a small user dictionary."""
    try:
        _ensure_firebase_app()
        decoded = auth.verify_id_token(id_token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email"),
            "name": decoded.get("name"),
        }
    except Exception:
        LOGGER.exception("Firebase auth failed")
        return None
