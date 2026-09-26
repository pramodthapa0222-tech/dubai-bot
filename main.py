
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYONEER_LINK = os.getenv("PAYONEER_LINK", "")
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL", "")
WHATSAPP = os.getenv("WHATSAPP_NUMBER", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Dubai Bot LIVE ✅\n/price /pay /ai hello")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Pricing:\nResume $29 | Logo $19 | Bot $99 | Store $149\nType /pay")

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💳 Pay:\nPayoneer: {PAYONEER_LINK}\nPayPal: {PAYPAL_EMAIL}\nWhatsApp: {WHATSAPP}")

async def ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) or "Hello"
    await update.message.reply_text(f"You said: {text}\n(AI will be added after this Live check)")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("ai", ai))
    print("Bot polling started")
    app.run_polling()

if __name__ == "__main__":
    main()
