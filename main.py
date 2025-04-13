from fastapi import FastAPI, Request
from bot import telegram_app  # Your Telegram bot integration
from telegram import Update
import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """Set the Telegram webhook URL on startup"""
    webhook_full_url = f"{os.getenv('WEBHOOK_URL')}/webhook"
    await telegram_app.bot.set_webhook(url=webhook_full_url)
    print(f"🚀 Webhook set to: {webhook_full_url}")

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook requests from Telegram"""
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# Entry point for running the FastAPI app with Uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
