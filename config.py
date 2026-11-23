"""Конфигурация из переменных окружения (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from filter import parse_keywords

load_dotenv()


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    phone: str
    source_channel: str
    target_chat: str
    keywords: list[str]
    session_file: str
    log_level: str

    @classmethod
    def from_env(cls) -> "Config":
        api_id_raw = os.getenv("API_ID", "").strip()
        api_hash = os.getenv("API_HASH", "").strip()
        phone = os.getenv("PHONE", "").strip()
        source = os.getenv("SOURCE_CHANNEL", "").strip()
        target = os.getenv("TARGET_CHAT", "me").strip() or "me"
        session_file = os.getenv("SESSION_FILE", "data/bot.session").strip()
        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

        missing = []
        if not api_id_raw:
            missing.append("API_ID")
        if not api_hash:
            missing.append("API_HASH")
        if not phone:
            missing.append("PHONE")
        if not source:
            missing.append("SOURCE_CHANNEL")
        if missing:
            raise SystemExit(
                "Не хватает переменных в .env: "
                + ", ".join(missing)
                + "\nСкопируй .env.example в .env и заполни значения."
            )

        try:
            api_id = int(api_id_raw)
        except ValueError:
            raise SystemExit("API_ID должен быть числом.")

        return cls(
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
            source_channel=source,
            target_chat=target,
            keywords=parse_keywords(os.getenv("KEYWORDS", "")),
            session_file=session_file,
            log_level=log_level,
        )
