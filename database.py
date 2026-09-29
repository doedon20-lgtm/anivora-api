import sqlite3
from pathlib import Path
from datetime import datetime


DATABASE_PATH = Path("anivora.db")


def connect():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():

    connection = connect()
    cursor = connection.cursor()

    # Developer accounts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS developers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # API keys
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            developer_id INTEGER NOT NULL,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            requests INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,

            FOREIGN KEY (developer_id)
            REFERENCES developers(id)
        )
    """)

    # API request logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            developer_id INTEGER,
            api_key_id INTEGER,
            endpoint TEXT NOT NULL,
            model TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (developer_id)
            REFERENCES developers(id),

            FOREIGN KEY (api_key_id)
            REFERENCES api_keys(id)
        )
    """)

    connection.commit()
    connection.close()


def create_developer(name, email):

    connection = connect()
    cursor = connection.cursor()

    created_at = datetime.utcnow().isoformat() + "Z"

    cursor.execute("""
        INSERT INTO developers (
            name,
            email,
            created_at
        )
        VALUES (?, ?, ?)
    """, (
        name,
        email,
        created_at
    ))

    developer_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return developer_id


def get_developer(developer_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM developers
        WHERE id = ?
    """, (developer_id,))

    developer = cursor.fetchone()

    connection.close()

    return developer


def create_api_key(
    developer_id,
    key,
    name
):

    connection = connect()
    cursor = connection.cursor()

    created_at = datetime.utcnow().isoformat() + "Z"

    cursor.execute("""
        INSERT INTO api_keys (
            developer_id,
            key,
            name,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        developer_id,
        key,
        name,
        created_at
    ))

    key_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return key_id


def get_api_key(key):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM api_keys
        WHERE key = ?
        AND active = 1
    """, (key,))

    api_key = cursor.fetchone()

    connection.close()

    return api_key


def increment_requests(key_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE api_keys
        SET requests = requests + 1
        WHERE id = ?
    """, (key_id,))

    connection.commit()
    connection.close()


def log_request(
    developer_id,
    api_key_id,
    endpoint,
    model,
    status
):

    connection = connect()
    cursor = connection.cursor()

    created_at = datetime.utcnow().isoformat() + "Z"

    cursor.execute("""
        INSERT INTO api_requests (
            developer_id,
            api_key_id,
            endpoint,
            model,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        developer_id,
        api_key_id,
        endpoint,
        model,
        status,
        created_at
    ))

    connection.commit()
    connection.close()


if __name__ == "__main__":

    create_tables()

    print("================================")
    print("       AniVora Database")
    print("================================")
    print("")
    print("Database:", DATABASE_PATH)
    print("Tables created successfully.")
    print("")
