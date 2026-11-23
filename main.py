"""Бот-пересыльщик вакансий из публичного Telegram-канала.

Как работает:
  1. Подключается к Telegram как обычный пользователь (отдельный аккаунт).
  2. Слушает публичный канал-источник (SOURCE_CHANNEL).
  3. Проверяет каждое новое сообщение по KEYWORDS.
  4. Подходящие пересылает в TARGET_CHAT (тебе в личку).

Запуск:
  cp .env.example .env   # заполнить своими значениями
  pip install -r requirements.txt
  python main.py         # первый раз попросит код из Telegram

ВАЖНО: используй ОТДЕЛЬНЫЙ аккаунт, не основной. Файл .session = полный
доступ к аккаунту, не коммить его в git и не показывай никому.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.types import Message

from config import Config
from filter import is_match, matched_keywords

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("forwarder")


async def copy_message(client: TelegramClient, target, message: Message) -> None:
    """Скопировать сообщение как новое (если forward запрещён каналом).

    Сохраняет текст + медиа (фото/видео/документ) с подписью.
    """
    text = message.text or ""
    if message.media:
        await client.send_file(
            target,
            file=message.media,
            caption=text or None,
        )
    else:
        await client.send_message(target, text)


async def forward(client: TelegramClient, target, message: Message) -> None:
    """Переслать сообщение: сначала пробуем forward, иначе — копия."""
    try:
        await client.forward_messages(target, message)
    except Exception as exc:  # noqa: BLE001 — fallback на копию
        log.warning("Forward не удался (%s), копирую как новое сообщение", exc)
        await copy_message(client, target, message)


async def handle_flood_wait(exc: FloodWaitError) -> None:
    wait = getattr(exc, "seconds", 60)
    log.warning("FloodWait: Telegram просит подождать %s сек.", wait)
    await asyncio.sleep(wait + 5)


async def main() -> None:
    cfg = Config.from_env()

    log.info("Источник: %s", cfg.source_channel)
    log.info("Приёмник: %s", cfg.target_chat)
    log.info(
        "Фильтр: %s",
        ", ".join(cfg.keywords) if cfg.keywords else "выключен (всё подряд)",
    )

    # Папка для сессии, чтобы файл не потерялся при рестарте в Docker
    session_dir = os.path.dirname(cfg.session_file)
    if session_dir:
        os.makedirs(session_dir, exist_ok=True)

    client = TelegramClient(cfg.session_file, cfg.api_id, cfg.api_hash)
    # Первый запуск — интерактивно введёшь код из Telegram.
    # На сервере сессию генерируют локально и копируют файл data/*.session.
    await client.start(phone=cfg.phone)

    me = await client.get_me()
    log.info("Авторизован как: %s (@%s)", me.first_name, me.username)

    # Проверяем доступ к каналу до старта слушателя
    try:
        source_entity = await client.get_entity(cfg.source_channel)
        title = getattr(source_entity, "title", None) or getattr(
            source_entity, "username", cfg.source_channel
        )
        log.info("Канал найден: %s", title)
    except Exception as exc:  # noqa: BLE001
        log.error("Не могу найти канал %s: %s", cfg.source_channel, exc)
        log.error("Проверь @username в SOURCE_CHANNEL и что аккаунт подписан на канал.")
        await client.disconnect()
        sys.exit(1)

    try:
        target_entity = await client.get_entity(cfg.target_chat)
        log.info("Приёмник найден: %s", getattr(target_entity, "title", None) or getattr(target_entity, "username", cfg.target_chat))
    except Exception as exc:  # noqa: BLE001
        log.error("Не могу найти приёмник %s: %s", cfg.target_chat, exc)
        log.error("Для лички укажи @username основного аккаунта или его числовой ID.")
        await client.disconnect()
        sys.exit(1)

    @client.on(events.NewMessage(chats=cfg.source_channel))
    async def on_new_message(event: events.NewMessage.Event) -> None:
        message = event.message
        text = message.text or ""

        if not is_match(text, cfg.keywords):
            return

        hits = matched_keywords(text, cfg.keywords)
        preview = (text[:120] + "…") if len(text) > 120 else text
        log.info(
            "Совпадение (id=%s, слова: %s): %s",
            message.id,
            ", ".join(hits) if hits else "—",
            preview.replace("\n", " "),
        )

        # Ретраи при FloodWait (лимит Telegram на отправку)
        for attempt in range(3):
            try:
                await forward(client, target_entity, message)
                break
            except FloodWaitError as exc:
                if attempt == 2:
                    log.error("FloodWait не прошёл после повторов, пропускаю id=%s", message.id)
                    break
                await handle_flood_wait(exc)
            except Exception as exc:  # noqa: BLE001
                log.error("Ошибка пересылки id=%s: %s", message.id, exc)
                break

    log.info("Слушаю новые сообщения… (Ctrl+C для остановки)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Остановлено пользователем.")
