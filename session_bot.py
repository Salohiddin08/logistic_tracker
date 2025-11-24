import os

from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes

API_ID = int(os.environ.get("TG_API_ID", "0"))
API_HASH = os.environ.get("TG_API_HASH", "")
BOT_TOKEN = "6879789382:AAHjfRISjAkoh4AHz5wRtpet-iMl80-xldM"

ASK_PHONE, ASK_CODE = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not API_ID or not API_HASH:
        await update.message.reply_text("API_ID yoki API_HASH sozlanmagan. Administrator bilan bog'laning.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Assalomu alaykum!\n\n"
        "Men sizga Telethon uchun string session yaratib beraman. "
        "Iltimos, avval telefon raqamingizni xalqaro formatda yuboring.\n"
        "Masalan: +9989XXXXXXX"
    )
    return ASK_PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["phone"] = phone

    context.user_data["client"] = TelegramClient(StringSession(), API_ID, API_HASH)
    client: TelegramClient = context.user_data["client"]

    await client.connect()

    try:
        await client.send_code_request(phone)
    except Exception as exc:  # noqa: BLE001
        await update.message.reply_text(f"Kod yuborishda xatolik: {exc}")
        await client.disconnect()
        return ConversationHandler.END

    await update.message.reply_text("SMS yoki Telegram'dan kelgan tasdiqlash kodini yuboring (faqat raqamlar).")
    return ASK_CODE


async def ask_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    phone = context.user_data.get("phone")
    client: TelegramClient = context.user_data.get("client")

    if not client or not phone:
        await update.message.reply_text("Sessiya ma'lumotlari topilmadi. /start dan qayta urinib ko'ring.")
        return ConversationHandler.END

    try:
        await client.sign_in(phone=phone, code=code)
    except Exception as exc:  # noqa: BLE001
        await update.message.reply_text(f"Kodni tasdiqlashda xatolik: {exc}")
        await client.disconnect()
        return ConversationHandler.END

    string_session = client.session.save()
    await client.disconnect()

    await update.message.reply_text(
        "✅ String session tayyor. Iltimos, uni faqat o'zingiz uchun ishlating va hech kimga bermang.\n\n"
        "Quyidagilarni nusxa ko'chiring va saytdagi 'String Session' maydoniga qo'ying:\n\n"
        f"<code>{string_session}</code>",
        parse_mode="HTML",
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.")
    client: TelegramClient | None = context.user_data.get("client")
    if client:
        await client.disconnect()
    return ConversationHandler.END


def main() -> None:

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv)
    application.run_polling()


if __name__ == "__main__":
    main()
