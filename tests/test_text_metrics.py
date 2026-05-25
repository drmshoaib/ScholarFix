"""Tests for readability helpers."""

from __future__ import annotations

from utils.text_metrics import count_syllables, flesch_label, readability_metrics


def test_count_syllables_handles_empty_and_words() -> None:
    assert count_syllables("") == 0
    assert count_syllables("review") >= 1
    assert count_syllables("academic") >= 3


def test_readability_metrics_preserve_expected_shape() -> None:
    metrics = readability_metrics("This is a short sentence. This is another.")

    assert metrics["words"] == 8
    assert metrics["sentences"] == 2
    assert metrics["avg_sentence_len"] == 4.0
    assert isinstance(metrics["flesch"], float)


def test_readability_metrics_empty_text() -> None:
    metrics = readability_metrics("   ")

    assert metrics == {
        "words": 0,
        "sentences": 0,
        "avg_sentence_len": 0.0,
        "flesch": None,
    }
    assert flesch_label(metrics["flesch"]) == "N/A"


def test_flesch_label_boundaries() -> None:
    assert flesch_label(95) == "Very easy"
    assert flesch_label(65) == "Standard"
    assert flesch_label(20) == "Very confusing"
