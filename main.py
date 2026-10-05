import gspread
from google.oauth2.service_account import Credentials
import logging
from typing import Final
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import html
from typing import Optional, List
from datetime import datetime, timedelta
from telegram import Message, Chat, Bot, User
from telegram.error import BadRequest
from telegram import ChatPermissions
from datetime import datetime
from zoneinfo import ZoneInfo
import json


#BOT SETUP
TOKEN = os.getenv("BOT_TOKEN")

authorized_id = 1136321264      
log_chat_id = -1004401300468
application = ApplicationBuilder().token(TOKEN).build()

#google sheet api setup
scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]
credentials_info = json.loads(
    os.environ["GOOGLE_CREDENTIALS"]
)

creds = Credentials.from_service_account_info(
    credentials_info,
    scopes=scopes
)

client = gspread.authorize(creds)
sheet_id = "1dCl8y5736oWlLBSv35gll2PnuXWxntEaxtZ4d6KskDI"
workbook = client.open_by_key(sheet_id)
sheet = workbook.worksheet("October")
#Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="yahoo"
    )

#add expense function
raw_categories = sheet.get_values('L15:L22')
valid_categories = [str(item).strip().lower() for row in raw_categories for item in row if item]

async def add_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #cek user
    user = update.effective_user
    if user.id != authorized_id:
        await update.message.reply_text(
        "Anda bukan admin bot"
        )
        return
    #cek jumlah argumen
    if len(context.args) < 3:
        await update.message.reply_text(
            "Format command salah, gunakan /addexpenses <nominal> <kategori> <keterangan>"
        )
        return
    nominals = context.args[0]
    category = context.args[1].strip().lower()
    description = " ".join(context.args[2:])

    #validasi argumen
    try:
        nominal = float(nominals)
        if nominal <= 0:
            await update.message.reply_text("nominal harus lebih dari 0")
            return
    except ValueError:
        await update.message.reply_text("mohon input angka")
        return

    if category not in valid_categories:
        await update.message.reply_text(
            "kategori tidak valid\n"
            "Kategori yang tersedia:\n"
            + "\n".join(f"- {x}" for x in valid_categories)
        )
        return
    #input ke sheets
    timezone = ZoneInfo("Asia/Jakarta")
    date = datetime.now(timezone).strftime("%d/%m/%Y")
    expenses_row = len(sheet.col_values(8)) + 1
    try:
        sheet.update_cell(expenses_row, 7, date)
        sheet.update_cell(expenses_row, 8, nominal)
        sheet.update_cell(expenses_row, 9, description)
        sheet.update_cell(expenses_row, 10, category)
    except Exception as e:
        await update.message.reply_text(
            "❌ Google Sheet Error, gagal menyimpan pengeluaran ke database."
        )
        return
    await update.message.reply_text(
        "✅ Pengeluaran berhasil dicatat!\n\n"
        f"📅 Tanggal: {date}\n"
        f"💰 Nominal: {nominal:,.0f}\n" 
        f"📂 Kategori: {category}\n"
        f"📝 Keterangan: {description}"
    )

    #log keuangan
    changelog_message = (
        "💸 <b>NEW EXPENSE</b>\n\n"
        f"📅 Tanggal: {date}\n"
        f"💰 Nominal: Rp{nominal:,.0f}\n"
        f"📂 Kategori: {category}\n"
        f"📝 Keterangan: {description}"
    )
    await context.bot.send_message(
        chat_id=log_chat_id,
        text=changelog_message,
        parse_mode="HTML"
    )
members = {}

tagtrigger = '@all'

async def member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Simpan member
    if user:
        members[user.id] = user.full_name

    # Cek apakah pesan adalah @all
    if update.message and update.message.text == tagtrigger:

        mentions = []

        for user_id, name in members.items():
            mentions.append(
                f'<a href="tg://user?id={user_id}">{html.escape(name)}</a>'
            )

        if not mentions:
            await update.message.reply_text(
                "Belum ada member yang terdaftar."
            )
            return

        text = " ".join(mentions)

        await update.message.reply_text(
            text,
            parse_mode="HTML"
        )


#reg member tag
tagtrigger = '@all'
async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mentions = []
    if update.message.text == tagtrigger:
        for user_id, name in members.items():
            mentions.append(
                f'<a href="tg://user?id={user_id}">{name}</a>'
            )

        text = " ".join(mentions)

        await update.message.reply_text(
            text,
            parse_mode="HTML"
        )
#template member tag
async def tagmembertemplate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="@salamsalmansalmon @Arachuna @Celll7 @IoremipsumdoIorsitamet @MyAsuna @dikadikak @noctyreID @sayaaica @raiimikoo @rakagooning @reraret19 @Slooooooooooth @aWanderers @Radius_1st @Firman_NF2PC @pinocopino"
    )

#get_user_id_command
async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        name = target_user.full_name
        user_id = target_user.id
        username = f"@{target_user.username}" if target_user.username else "No public username"
        response = (
            f"👤 User Info (Replied)\n"
            f"🔹 Name: {name}\n"
            f"🔹 Username: {username}\n"
            f"🆔 User ID: {user_id}"
        )
        await update.message.reply_text(response, parse_mode="Markdown")
    else:
        # If not a reply, return the ID of the person who typed the command
        sender = update.message.from_user
        response = (
            f"ℹ️ Reply to someone's message with /id to get their ID.\n"
            f"Your own ID is: {sender.id}"
        )
        await update.message.reply_text(response, parse_mode="Markdown")


if __name__ == '__main__':

    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler("start", start)

    tag_all_template_handler = CommandHandler("tagall", tagmembertemplate)
    

    addexpenses_handler = CommandHandler("addexpenses", add_expenses)

    member_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    member_handler
    )

    get_user_id_handler = CommandHandler("getid", get_user_id)
    
    application.add_handler(start_handler)
    application.add_handler(get_user_id_handler)
    application.add_handler(tag_all_template_handler)
    application.add_handler(member_handler)
    application.add_handler(addexpenses_handler)

    application.run_polling()
