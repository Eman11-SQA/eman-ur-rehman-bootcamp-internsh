import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import Config

def create_database():
    conn = psycopg2.connect(
        dbname="postgres",
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE {Config.DB_NAME} WITH OWNER = {Config.DB_USER}")
        print("Database created successfully!")
    except Exception as e:
        print("Database may already exist:", e)
    cursor.close()
    conn.close()

def create_tables():
    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT NOT NULL,
            disease VARCHAR(200),
            contact VARCHAR(30),
            Status   VARCHAR(200),
            visit_date TEXT
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created successfully!")

if __name__ == "__main__":
    create_database()
    create_tables()
