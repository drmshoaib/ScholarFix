"""OpenAI-backed rewriting helpers."""

from __future__ import annotations

import logging
import os

import openai

from config import OPENAI_MODEL

LOGGER = logging.getLogger(__name__)


def get_client() -> openai.OpenAI:
    """Create an OpenAI client from the local environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Check your .env file.")
    return openai.OpenAI(api_key=api_key)


def suggest_rewording(
    text: str,
    scope: str = "full",
    tone: str = "Neutral",
    level: str = "Undergraduate",
    model: str | None = None,
    max_chars: int = 3000,
) -> str:
    """Rewrite a manuscript excerpt while preserving technical meaning."""
    trimmed = text[:max_chars]

    prompt = (
        "You are an expert academic editor.\n\n"
        f"Rewrite the following {scope} section of an academic document.\n"
        f"Make it suitable for a {level.lower()} audience with a {tone.lower()} tone.\n"
        "Ensure grammar, clarity, sentence structure, and academic style are improved, "
        "while keeping all technical meaning unchanged.\n\n"
        f"---\n{trimmed}\n---"
    )

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        LOGGER.exception("OpenAI rewrite request failed")
        return f"Error during rewording: {exc}"
