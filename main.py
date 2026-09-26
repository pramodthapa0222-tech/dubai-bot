import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PAYONEER_LINK = os.getenv("PAYONEER_LINK", "")
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL", "")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
logging.basicConfig(level=logging.INFO)

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 View Services & Pricing", callback_data="services")],
        [InlineKeyboardButton("💬 Contact Us", callback_data="contact")]
    ])

def pay_kb():
    btns = []
    if PAYONEER_LINK:
        btns.append([InlineKeyboardButton("💳 Pay via Payoneer", url=PAYONEER_LINK)])
    if WHATSAPP_NUMBER:
        num = WHATSAPP_NUMBER.replace("+","").replace(" ","")
        btns.append([InlineKeyboardButton("📲 WhatsApp Us", url=f"https://wa.me/{num}")])
    btns.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(btns)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to *Dubai Digital Empire* 🇦🇪\n\nYour one-stop for Dubai business success. Choose below:",
        reply_markup=main_kb(), parse_mode="Markdown"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 *Pricing*\n\n📄 Resume Maker AI: $29\n🎨 Logo Maker: $19\n🤖 Bot Setup: $99\n🌐 Full Store: $149\n\nUse /pay to pay",
        parse_mode="Markdown"
    )

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💳 *Payment*\nPayoneer: {PAYONEER_LINK}\nPayPal: {PAYPAL_EMAIL}\nWhatsApp: {WHATSAPP_NUMBER}",
        reply_markup=pay_kb(), parse_mode="Markdown"
    )

async def ai_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not client:
        await update.message.reply_text("AI not set: Add OPENAI_API_KEY in Render")
        return
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Use: /ai hello")
        return
    try:
        await context.bot.send_chat_action(update.effective_chat.id, "typing")
        r = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}])
        await update.message.reply_text(r.choices[0].message.content[:4000])
    except Exception as e:
        await update.message.reply_text(f"AI Error: {e}")

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "services":
        await price(q, context)
    elif q.data == "contact":
        await q.message.reply_text(f"Contact: {WHATSAPP_NUMBER} | {PAYPAL_EMAIL}")
    elif q.data == "back":
        await q.message.reply_text("Menu:", reply_markup=main_kb())

# === THIS IS THE FIX ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("ai", ai_cmd))
    app.add_handler(CallbackQueryHandler(btn_handler))
    print("Bot LIVE - polling started")
    app.run_polling() # <-- NO await, NO asyncio.run

if __name__ == "__main__":
    main()
