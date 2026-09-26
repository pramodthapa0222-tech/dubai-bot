import os, threading
from flask import Flask, render_template_string
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or ""
OPENAI_KEY = os.getenv("OPENAI_API_KEY") or ""
OWNER_ID = os.getenv("OWNER_ID") or ""
PAYONEER_LINK = os.getenv("PAYONEER_LINK") or "https://payoneer.com"
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER") or ""

client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

web = Flask(__name__)

DASHBOARD_HTML = """
<h1>🤖 Bot Dashboard - LIVE</h1>
<p>Bot Status: ✅ Running</p>
<p>AI Status: {{ai_status}}</p>
<p>Owner: {{owner}}</p>
<hr>
<a href="{{payoneer}}">Payoneer Link</a> | <a href="https://wa.me/{{wa}}">WhatsApp</a>
<hr>
<p>Commands: /start /help /dashboard /pay /ai [your question]</p>
"""

@web.route("/")
def home():
    return render_template_string(
        DASHBOARD_HTML,
        ai_status="✅ Connected" if client else "❌ No OPENAI_API_KEY",
        owner=OWNER_ID or "Not Set",
        payoneer=PAYONEER_LINK,
        wa=WHATSAPP_NUMBER,
    )

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Bot Live ✅\n\n"
        f"/start - Start\n"
        f"/help - Help\n"
        f"/dashboard - Get dashboard link\n"
        f"/pay - Payment link\n"
        f"/ai [question] - Ask AI\n"
        f"Just send any message - I reply with AI"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send any message. Use /ai your question for AI reply. /dashboard for web panel.")

async def dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your dashboard is LIVE on Render URL: {os.environ.get('RENDER_EXTERNAL_URL','')}")

async def pay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💳 Pay here: {PAYONEER_LINK}\n📱 WhatsApp: {WHATSAPP_NUMBER}")

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text.startswith("/ai "):
        user_text = user_text[4:]
    if not client:
        await update.message.reply_text(f"Echo (AI not set): {user_text}\n\nAdd OPENAI_API_KEY in Secrets to enable AI.")
        return
    try:
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": user_text}])
        await update.message.reply_text(resp.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"AI Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()

    if not BOT_TOKEN:
        print("FATAL: No BOT_TOKEN in Secrets")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(CommandHandler("dashboard", dashboard_cmd))
        app.add_handler(CommandHandler("pay", pay_cmd))
        app.add_handler(CommandHandler("ai", ai_reply))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
        print("Bot polling started...")
        app.run_polling()
