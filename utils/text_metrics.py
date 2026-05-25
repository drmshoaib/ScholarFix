"""Lightweight readability metrics used by the Streamlit app."""

from __future__ import annotations

import re


def count_syllables(word: str) -> int:
    """Estimate syllables in an English word without external dependencies."""
    word = re.sub(r"[^a-zA-Z]", "", word).lower()
    if not word:
        return 0

    vowels = "aeiouy"
    count = 0
    previous_was_vowel = False
    for character in word:
        is_vowel = character in vowels
        if is_vowel and not previous_was_vowel:
            count += 1
        previous_was_vowel = is_vowel

    if word.endswith("e") and count > 1:
        count -= 1

    return max(count, 1)


def readability_metrics(text: str) -> dict[str, float | int | None]:
    """Return approximate word, sentence, and Flesch reading-ease metrics."""
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return {
            "words": 0,
            "sentences": 0,
            "avg_sentence_len": 0.0,
            "flesch": None,
        }

    sentences = [sentence.strip() for sentence in re.split(r"[.!?]+", clean) if sentence.strip()]
    words = re.findall(r"\b[\w'-]+\b", clean)

    sentence_count = max(len(sentences), 1)
    word_count = max(len(words), 1)
    syllables = sum(count_syllables(word) for word in words)
    avg_sentence_len = word_count / sentence_count
    flesch = 206.835 - 1.015 * avg_sentence_len - 84.6 * (syllables / word_count)

    return {
        "words": word_count,
        "sentences": len(sentences),
        "avg_sentence_len": round(avg_sentence_len, 1),
        "flesch": round(flesch, 1),
    }


def flesch_label(score: float | None) -> str:
    """Map a Flesch score to a readable label."""
    if score is None:
        return "N/A"
    if score >= 90:
        return "Very easy"
    if score >= 80:
        return "Easy"
    if score >= 70:
        return "Fairly easy"
    if score >= 60:
        return "Standard"
    if score >= 50:
        return "Fairly difficult"
    if score >= 30:
        return "Difficult"
    return "Very confusing"
