import logging
import os
from telegram import Update, Document
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes,
    ConversationHandler, filters
)
from utils import edit_pdf_fields

# Этапы разговора
PDF, NUMBER, TIME, REGION = range(4)

# Логгинг
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище для PDF
user_data_files = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне PDF файл.")
    return PDF

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = update.message.document
    if not document.file_name.endswith(".pdf"):
        await update.message.reply_text("Мне нужен PDF файл, ня...")
        return PDF

    file = await document.get_file()
    file_path = f"user_{update.message.from_user.id}.pdf"
    await file.download_to_drive(file_path)

    user_data_files[update.message.from_user.id] = file_path
    await update.message.reply_text("Получила файл! Теперь введи новый номер:")
    return NUMBER

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["number"] = update.message.text
    await update.message.reply_text("Теперь введи новое время:")
    return TIME

async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time"] = update.message.text
    await update.message.reply_text("Теперь введи регион:")
    return REGION

async def handle_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["region"] = update.message.text
    user_id = update.message.from_user.id
    file_path = user_data_files.get(user_id)

    if file_path:
        output_path = f"edited_{user_id}.pdf"
        edit_pdf_fields(
            file_path,
            output_path,
            context.user_data["number"],
            context.user_data["time"],
            context.user_data["region"]
        )
        await update.message.reply_document(document=open(output_path, "rb"))
        os.remove(file_path)
        os.remove(output_path)
    else:
        await update.message.reply_text("Упс, не нашла твой файл...")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменила, ня.")
    return ConversationHandler.END

if __name__ == "__main__":
    import os
    TOKEN = os.environ.get("BOT_TOKEN")  # вставь токен в переменные окружения

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PDF: [MessageHandler(filters.Document.PDF, handle_pdf)],
            NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_region)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
