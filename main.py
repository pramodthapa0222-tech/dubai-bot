import os
import time
import logging
import threading

from flask import Flask, render_template_string
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or ""
OPENAI_KEY = os.getenv("OPENAI_API_KEY") or ""
PAYONEER_LINK = os.getenv("PAYONEER_LINK") or "https://payoneer.com"
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER") or ""
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") or ""

# Optional: comma-separated Telegram user IDs allowed to use AI (empty = everyone)
ALLOWED_IDS = {
    int(x) for x in (os.getenv("ALLOWED_USER_IDS") or os.getenv("OWNER_ID") or "").split(",")
    if x.strip().isdigit()
}
COOLDOWN_SECONDS = 5
_last_call: dict[int, float] = {}

# Async client so OpenAI calls don't block the Telegram event loop
client = AsyncOpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# ---------- Web dashboard ----------
web = Flask(__name__)

DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bot Dashboard</title>
</head>
<body>
  <h1>🤖 Bot Dashboard - LIVE</h1>
  <p>Bot Status: ✅ Running</p>
  <p>AI Status: {{ ai_status }}</p>
  <hr>
  <a href="{{ payoneer }}">Payoneer Link</a>
  {% if wa %} | <a href="https://wa.me/{{ wa }}">WhatsApp</a>{% endif %}
  <hr>
  <p>Commands: /start /help /dashboard /pay /ai [your question]</p>
</body>
</html>
"""


@web.route("/")
def home():
    return render_template_string(
        DASHBOARD_HTML,
        ai_status="✅ Connected" if client else "❌ No OPENAI_API_KEY",
        payoneer=PAYONEER_LINK,
        wa=WHATSAPP_NUMBER.lstrip("+"),
    )


@web.route("/health")
def health():
    return "ok"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)


# ---------- Telegram handlers ----------
async def reply_long(update: Update, text: str):
    """Telegram caps messages at 4096 chars."""
    text = text or "(empty reply)"
    for i in range(0, len(text), 4000):
        await update.effective_message.reply_text(text[i:i + 4000])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Bot Live ✅\n\n"
        "/start - Start\n"
        "/help - Help\n"
        "/dashboard - Get dashboard link\n"
        "/pay - Payment link\n"
        "/ai [question] - Ask AI\n"
        "Just send any message - I reply with AI"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Send any message. Use /ai your question for AI reply. /dashboard for web panel."
    )


async def dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if RENDER_URL:
        await update.effective_message.reply_text(f"Your dashboard: {RENDER_URL}")
    else:
        await update.effective_message.reply_text("Dashboard URL not configured (RENDER_EXTERNAL_URL missing).")


async def pay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"💳 Pay here: {PAYONEER_LINK}"
    if WHATSAPP_NUMBER:
        msg += f"\n📱 WhatsApp: {WHATSAPP_NUMBER}"
    await update.effective_message.reply_text(msg)


async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    if not msg or not user:
        return

    # For /ai, context.args holds the text (also works for /ai@BotName in groups)
    if context.args is not None:
        user_text = " ".join(context.args).strip()
    else:
        user_text = (msg.text or "").strip()

    if not user_text:
        await msg.reply_text("Usage: /ai your question")
        return

    if ALLOWED_IDS and user.id not in ALLOWED_IDS:
        await msg.reply_text("Sorry, you're not authorized to use AI replies.")
        return

    if not client:
        await msg.reply_text(f"Echo (AI not set): {user_text}\n\nAdd OPENAI_API_KEY to enable AI.")
        return

    # Simple per-user rate limit to protect your OpenAI credits
    now = time.monotonic()
    if now - _last_call.get(user.id, 0) < COOLDOWN_SECONDS:
        await msg.reply_text("Slow down a little - try again in a few seconds.")
        return
    _last_call[user.id] = now

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_text}],
        )
        await reply_long(update, resp.choices[0].message.content)
    except Exception:
        log.exception("OpenAI request failed")
        await msg.reply_text("Sorry, the AI request failed. Please try again later.")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Unhandled error", exc_info=context.error)


if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()

    if not BOT_TOKEN:
        log.critical("FATAL: No BOT_TOKEN set")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(CommandHandler("dashboard", dashboard_cmd))
        app.add_handler(CommandHandler("pay", pay_cmd))
        app.add_handler(CommandHandler("ai", ai_reply))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
        app.add_error_handler(on_error)
        log.info("Bot polling started...")
        app.run_polling()
