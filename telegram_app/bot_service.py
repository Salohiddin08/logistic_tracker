from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from telegram import InputFile
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from .exports import build_shipments_workbook_bytes


@dataclass(frozen=True)
class BotConfig:
    token: str
    admin_chat_id: int


def get_bot_config() -> BotConfig:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    admin_chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)

    if not token:
        raise ValueError('TELEGRAM_BOT_TOKEN .env faylda yo‘q')
    if not admin_chat_id:
        raise ValueError('TELEGRAM_ADMIN_CHAT_ID .env faylda yo‘q')

    return BotConfig(token=token, admin_chat_id=int(admin_chat_id))


def _is_admin_chat(chat_id: int) -> bool:
    cfg = get_bot_config()
    return int(chat_id) == int(cfg.admin_chat_id)


async def _send_export(application: Application, *, days: int) -> None:
    cfg = get_bot_config()

    if days < 1:
        days = 1
    if days > 60:
        days = 60

    today = timezone.localdate()
    date_from = today - timedelta(days=days - 1)
    date_to = today

    data = build_shipments_workbook_bytes(date_from=date_from, date_to=date_to)
    filename = f"shipments_{date_from.isoformat()}_{date_to.isoformat()}.xlsx"

    await application.bot.send_document(
        chat_id=cfg.admin_chat_id,
        document=InputFile(data, filename=filename),
        caption=f"TG Yuk Monitor eksport: {date_from.isoformat()} → {date_to.isoformat()} (days={days})",
    )


async def cmd_start(update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        return
    if not _is_admin_chat(update.effective_chat.id):
        await update.message.reply_text('Ruxsat yo‘q.')
        return

    await update.message.reply_text(
        'TG Yuk Monitor bot ishlayapti.\n'
        'Buyruqlar:\n'
        '  /export 1  - bugungi yuklar Excel\n'
        '  /export 7  - oxirgi 7 kun\n'
    )


async def cmd_export(update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        return
    if not _is_admin_chat(update.effective_chat.id):
        await update.message.reply_text('Ruxsat yo‘q.')
        return

    days = 1
    if context.args:
        try:
            days = int(context.args[0])
        except Exception:
            days = 1

    await update.message.reply_text(f'Excel tayyorlanyapti... (days={days})')
    await _send_export(context.application, days=days)
    await update.message.reply_text('Yuborildi ✅')


def build_application() -> Application:
    cfg = get_bot_config()

    application = ApplicationBuilder().token(cfg.token).build()
    application.add_handler(CommandHandler('start', cmd_start))
    application.add_handler(CommandHandler('export', cmd_export))
    return application


async def daily_sender_loop(application: Application, *, hour: int = 0, minute: int = 5) -> None:
    """Send daily Excel to admin at HH:MM local time."""
    while True:
        now = timezone.localtime()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run + timedelta(days=1)

        sleep_seconds = max(1, int((next_run - now).total_seconds()))
        await asyncio.sleep(sleep_seconds)

        try:
            await _send_export(application, days=1)
        except Exception:
            # avoid crashing the loop
            pass


async def send_export_now(*, days: int) -> None:
    """One-shot sending (used by web view)."""
    application = build_application()
    await application.initialize()
    await application.bot.initialize()
    try:
        await _send_export(application, days=days)
    finally:
        await application.shutdown()
