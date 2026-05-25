"""Firebase sign-in component wrapper."""

from __future__ import annotations

import streamlit.components.v1 as components

from config import COMPONENTS_DIR


def google_login_component(height: int = 420) -> None:
    """Render the Firebase Google sign-in component."""
    html_path = COMPONENTS_DIR / "signin_component.html"
    html = html_path.read_text(encoding="utf-8")

    components.html(
        html,
        height=height,
        scrolling=False,
    )
