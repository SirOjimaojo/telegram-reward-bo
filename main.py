from fastapi import FastAPI, Request
from bot import telegram_app  # Import your Application instance
from telegram import Update
import os
from dotenv import load_dotenv
import uvicorn
import logging

# Load environment variables
load_dotenv()

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """Initialize Telegram app and set webhook"""
    await telegram_app.initialize()  # REQUIRED before handling updates!
    webhook_full_url = f"{os.getenv('WEBHOOK_URL')}/webhook"
    await telegram_app.bot.set_webhook(url=webhook_full_url)
    logger.info(f"🚀 Webhook set to: {webhook_full_url}")

@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram updates"""
    try:
        data = await request.json()
        logger.info(f"📩 Incoming Telegram Update: {data}")
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.exception(f"❌ Exception while handling webhook: {e}")
        return {"ok": False, "error": str(e)}

# Run app if this file is executed
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
