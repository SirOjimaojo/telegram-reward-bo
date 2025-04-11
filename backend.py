import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MySQL
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

# Insert a new user into the database
def insert_new_user(telegram_id, name, referrer_id=None):
    db = get_db_connection()
    if db:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (telegram_id, name, balance, referrals, referred_by) VALUES (%s, %s, %s, %s, %s)",
            (telegram_id, name, 0, 0, referrer_id)
        )
        db.commit()
        db.close()

# Get user data (referrals and balance)
def get_user_data(telegram_id):
    db = get_db_connection()
    if db:
        cursor = db.cursor(buffered=True)
        cursor.execute("SELECT referrals, balance FROM users WHERE telegram_id = %s", (telegram_id,))
        result = cursor.fetchone()
        db.close()
        return result
    return None

# Update user referrals
def update_referrals(referrer_id):
    db = get_db_connection()
    if db:
        cursor = db.cursor()
        cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE telegram_id = %s", (referrer_id,))
        db.commit()
        db.close()

# Handle user withdrawal
def handle_withdrawal(user_id):
    db = get_db_connection()
    if db:
        cursor = db.cursor(buffered=True)
        cursor.execute("SELECT account_number, account_name, bank_name, referrals, balance FROM users WHERE telegram_id = %s", (user_id,))
        result = cursor.fetchone()
        db.close()
        if result and result[3] >= 20 and result[4] >= 6000:
            return True
    return False