import json
import logging
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.db import export_to_csv, get_latest_submissions, get_submission_count, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_USERS


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.message.reply_text("Нет доступа.")
        return

    await update.message.reply_text(
        "Команды:\n"
        "/count — количество заявок\n"
        "/list — последние 10 заявок\n"
        "/export — CSV со всеми заявками"
    )


async def count_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.message.reply_text("Нет доступа.")
        return

    count = get_submission_count()
    await update.message.reply_text(f"Всего заявок: {count}")


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.message.reply_text("Нет доступа.")
        return

    rows = get_latest_submissions(limit=10)
    if not rows:
        await update.message.reply_text("Заявок пока нет.")
        return

    parts = ["<b>Последние 10 заявок:</b>\n"]
    labels = {
        "whiteWine": "Белое вино",
        "redWine": "Красное вино",
        "champagne": "Шампанское",
        "beer": "Пиво",
        "whiskey": "Виски",
        "tinctures": "Настойки",
    }

    for row in rows:
        alcohol = json.loads(row["alcohol_json"])
        selected = [label for key, label in labels.items() if alcohol.get(key)]
        alcohol_str = ", ".join(selected) if selected else "Ничего"

        parts.append(
            f"ID {row['id']}\n"
            f"Имя: {row['name']}\n"
            f"Аллергия: {row['allergy'] or '—'}\n"
            f"Алкоголь: {alcohol_str}\n"
            f"Дата: {row['created_at']}\n"
        )

    text = "\n".join(parts)

    # Telegram режет слишком длинные сообщения, поэтому отправим по частям.
    chunk_size = 3500
    for i in range(0, len(text), chunk_size):
        await update.message.reply_text(
            text[i:i + chunk_size],
            parse_mode=ParseMode.HTML,
        )


async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.message.reply_text("Нет доступа.")
        return

    file_path = export_to_csv()
    with Path(file_path).open("rb") as f:
        await update.message.reply_document(document=f, filename="submissions_export.csv")


def main() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    init_db()

    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("count", count_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("export", export_cmd))

    logger.info("Telegram bot started")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()