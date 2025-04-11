import mysql.connector
from mysql.connector import Error

# Railway Public Connection Details
host = "yamabiko.proxy.rlwy.net"
port = 40129
user = "root"
password = "ZszcxNQMfdmYQEKquORFpQVIfnRCHjqh"
database = "railway"

try:
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )

    if conn.is_connected():
        print("✅ Connected to MySQL database!")

        cursor = conn.cursor()

        create_users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            balance DECIMAL(10, 2) DEFAULT 0,
            referrals INT DEFAULT 0,
            referred_by BIGINT DEFAULT NULL,
            account_number VARCHAR(255),
            account_name VARCHAR(255),
            bank_name VARCHAR(255)
        )
        """

        cursor.execute(create_users_table_query)
        conn.commit()
        print("✅ 'users' table created successfully.")

except Error as e:
    print("❌ MySQL Error:", e)

finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
        print("🔒 MySQL connection closed.")
