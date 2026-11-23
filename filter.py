"""Фильтр сообщений по ключевым словам.

Сообщение считается подходящим, если его текст (без учёта регистра)
содержит ЛЮБОЕ слово из списка. Если список пуст — подходит всё.
"""

from __future__ import annotations


def parse_keywords(raw: str | None) -> list[str]:
    """Разобрать строку KEYWORDS из .env в список слов (lowercase, без пустых)."""
    if not raw:
        return []
    return [k.strip().lower() for k in raw.split(",") if k.strip()]


def is_match(text: str | None, keywords: list[str]) -> bool:
    """True, если текст подходит под фильтр."""
    if not keywords:
        return True  # фильтр выключен — пересылать всё
    if not text:
        return False  # без текста проверять нечего
    haystack = text.lower()
    return any(kw in haystack for kw in keywords)


def matched_keywords(text: str | None, keywords: list[str]) -> list[str]:
    """Вернуть список сработавших ключевых слов (для логов)."""
    if not text or not keywords:
        return []
    haystack = text.lower()
    return [kw for kw in keywords if kw in haystack]
