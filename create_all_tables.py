import mysql.connector
from mysql.connector import Error

# MySQL connection details
MYSQL_HOST = "yamabiko.proxy.rlwy.net"
MYSQL_PORT = 40129
MYSQL_USER = "root"
MYSQL_PASSWORD = "ZszcxNQMfdmYQEKquORFpQVIfnRCHjqh"
MYSQL_DATABASE = "railway"

# Create a connection
try:
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT
    )

    if conn.is_connected():
        cursor = conn.cursor()

        # Drop existing tables
        cursor.execute("DROP TABLE IF EXISTS users, referrals, transactions, withdrawals, admins;")
        print("✅ Dropped previous tables.")

        # Create 'users' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            name VARCHAR(255) NOT NULL,
            balance DECIMAL(10, 2) DEFAULT 0,
            referrals INT DEFAULT 0,
            referred_by BIGINT DEFAULT NULL,
            account_number VARCHAR(255),
            account_name VARCHAR(255),
            bank_name VARCHAR(255),
            UNIQUE (telegram_id)
        );
        """)

        # Create 'referrals' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            referred_user_id BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id),
            FOREIGN KEY (referred_user_id) REFERENCES users(telegram_id)
        );
        """)

        # Create 'transactions' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            type ENUM('deposit', 'withdraw', 'referral_bonus', 'admin_credit') NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            status ENUM('pending', 'approved', 'declined') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        );
        """)

        # Create 'withdrawals' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            status ENUM('pending', 'paid', 'rejected') DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        );
        """)

        # Create 'admins' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Commit the changes
        conn.commit()

        print("✅ All tables created successfully!")

except Error as e:
    print(f"❌ MySQL Error: {e}")

finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
        print("🔌 MySQL connection closed.")
