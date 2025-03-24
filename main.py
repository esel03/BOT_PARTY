import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import json
import os

load_dotenv() 


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


CATEGORY, SECTOR, TEXT = range(3)


MAIN_MENU = ReplyKeyboardMarkup([["Написать жалобу"]], resize_keyboard=True)


CATEGORIES = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Дороги", callback_data="roads"),
            InlineKeyboardButton("ЖКХ", callback_data="housing"),
        ],
        [
            InlineKeyboardButton("Мигранты", callback_data="migrants"),
            InlineKeyboardButton("Другое", callback_data="other"),
        ],
    ]
)


SECTORS = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Сектор 1", callback_data="sector1")],
        [InlineKeyboardButton("Сектор 2", callback_data="sector2")],
        [InlineKeyboardButton("Сектор 3", callback_data="sector3")],
    ]
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Выберите действие:",reply_markup=MAIN_MENU)


async def category_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите категорию жалобы:",reply_markup=CATEGORIES)
    return CATEGORY


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["category"] = query.data
    
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=open("sektor-gaza-istoriya-gruppy.jpeg", "rb"),
        caption="Выберите сектор:",
        reply_markup=SECTORS
    )
    return SECTOR


async def sector_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["sector"] = query.data
    await query.message.reply_text("Напишите жалобу")
    return TEXT

import json
from datetime import datetime
import os
import glob

async def data_to_json(data):
    category = data.get('category')
    sector = data.get('sector')
    text = data.get('text')
    folder_path = os.path.join(os.getcwd(), category)
    os.makedirs(folder_path, exist_ok=True)
    current_date = datetime.now().strftime("%Y-%m-%d")
    existing_files = glob.glob(os.path.join(folder_path, f"{current_date}_*.json"))
    complaint_number = len(existing_files) + 1
    file_name = f"{current_date}_{complaint_number}.json"
    file_path = os.path.join(folder_path, file_name)
    data = {
        'category': category,
        'sector': sector,
        'text': text,
        'timestamp': datetime.now().isoformat()
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["text"] = update.message.text
    data = context.user_data    
    await update.message.reply_text(
        "Спасибо, ваша жалоба принята.\n\n"
        f"Категория: {data['category']}\n"
        f"Сектор: {data['sector']}\n"
        f"Текст: {data['text']}"
    )
    await data_to_json(data)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог прерван", reply_markup=MAIN_MENU)
    return ConversationHandler.END


def main():
    application = ApplicationBuilder().token(os.getenv('TOKEN')).build()

    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^Написать жалобу$"), category_choose)],
        states={
            CATEGORY: [CallbackQueryHandler(category_handler)],
            SECTOR: [CallbackQueryHandler(sector_handler)],
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conversation_handler)

    application.run_polling()


if __name__ == "__main__":
    main()