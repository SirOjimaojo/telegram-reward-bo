from fastapi import FastAPI, Request
from bot import telegram_app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Set webhook on FastAPI startup
@app.on_event("startup")
async def on_startup():
    webhook_full_url = f"{os.getenv('WEBHOOK_URL')}/webhook"
    await telegram_app.bot.set_webhook(url=webhook_full_url)
    print(f"🚀 Webhook set to: {webhook_full_url}")

# Webhook listener
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
