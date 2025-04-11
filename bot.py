from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from backend import insert_new_user, get_user_data, update_referrals, handle_withdrawal
import os
from dotenv import load_dotenv
import mysql.connector

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram Bot App
telegram_app = Application.builder().token(BOT_TOKEN).build()

# Connect to MySQL (for referral check in show_referrals)
def get_db_connection():
    try:
        db = mysql.connector.connect(
            host=os.getenv("MYSQLHOST"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            database=os.getenv("MYSQLDATABASE"),
            port=int(os.getenv("MYSQLPORT", 3306))
        )
        return db
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        return None

# Menu Keyboard Builder
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    user_data = get_user_data(telegram_id)

    if not user_data:
        if referrer_id:
            referrer_data = get_user_data(referrer_id)
            if referrer_data:
                insert_new_user(telegram_id, name, referrer_id)
                update_referrals(referrer_id)
        insert_new_user(telegram_id, name)

    referrals, balance = user_data
    markup = build_menu_keyboard(referrals, balance)
    welcome_text = f"Welcome, {name}! 🎉\n\nChoose an option below to continue:"
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=markup)

# Button Click Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "watch_ads":
        ad_link = "https://www.profitableratecpm.com/j4wa6ksu?key=6ad2b237a51106f25754b3e61fbf8cb2"
        keyboard = InlineKeyboardMarkup([ 
            [InlineKeyboardButton("▶️ Watch Ad", url=ad_link)]
        ])
        await query.message.reply_text(
            "🎥 Click the button below to watch the full ad and earn ₦100.\n\n⚠️ Do not minimize or exit until it finishes.",
            reply_markup=keyboard
        )

    elif data == "refer":
        link = f"https://t.me/{context.bot.username}?start=ref{user_id}"
        await query.message.reply_text(
            f"🔗 Your referral link:\n{link}\n\nEarn ₦200 for every person who joins using your link!"
        )

    elif data == "withdraw":
        if handle_withdrawal(user_id):
            await query.message.reply_text("✅ Withdrawal request accepted. We'll process your payment soon.")
        else:
            await query.message.reply_text("❌ You need at least 20 referrals and ₦6,000 balance to withdraw.")

    elif data == "show_referrals":
        db = get_db_connection()
        if db:
            cursor = db.cursor(buffered=True)
            cursor.execute("SELECT name FROM users WHERE referred_by = %s", (user_id,))
            referred = cursor.fetchall()
            if referred:
                names = "\n".join(f"• {r[0]}" for r in referred)
                await query.message.reply_text(f"👥 Your referrals:\n{names}")
            else:
                await query.message.reply_text("😕 No referrals yet.")
            db.close()

    elif data == "reload":
        await start(update, context)

    elif data == "no_action":
        await query.answer("✅ Balance displayed.")

# Handle Text Replies (Withdraw Flow)
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

        db = get_db_connection()
        if db:
            cursor = db.cursor(buffered=True)
            cursor.execute(
                "UPDATE users SET account_number = %s, account_name = %s, bank_name = %s WHERE telegram_id = %s",
                (account_number, account_name, bank_name, user_id)
            )
            db.commit()
            db.close()

        user_stage[user_id] = None
        context.user_data.clear()

        await update.message.reply_text("✅ Bank details saved!")
        await update.message.reply_text(
            "🧾 *Next Step: Payment Required*\n\nSend ₦4,000 to:\n*Account Name:* John Doe\n*Account Number:* 1234567890\n*Bank:* First Bank\n\n✅ We’ll process your withdrawal within 6 hours after payment.",
            parse_mode="Markdown"
        )

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(button_handler))
telegram_app.add_handler(MessageHandler(filters.TEXT, handle_text))
