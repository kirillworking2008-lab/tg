"""Тесты фильтра по ключевым словам."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter import is_match, matched_keywords, parse_keywords


def test_parse_keywords():
    assert parse_keywords("Вакансия, работа , ,ЗАРПЛАТА") == [
        "вакансия",
        "работа",
        "зарплата",
    ]
    assert parse_keywords("") == []
    assert parse_keywords(None) == []


def test_match_case_insensitive():
    kw = ["вакансия", "работа"]
    assert is_match("Срочно требуется ВАКАНСИЯ в офис", kw) is True
    assert is_match("Есть работа с жильём", kw) is True
    assert is_match("Новости спорта за сегодня", kw) is False


def test_empty_filter_matches_all():
    assert is_match("Любой текст", []) is True
    assert is_match("", []) is True


def test_empty_text_no_match():
    assert is_match("", ["вакансия"]) is False
    assert is_match(None, ["вакансия"]) is False


def test_matched_keywords():
    kw = ["вакансия", "работа", "зарплата"]
    assert matched_keywords("Вакансия: работа, зарплата 2000", kw) == [
        "вакансия",
        "работа",
        "зарплата",
    ]
    assert matched_keywords("Просто новости", kw) == []
