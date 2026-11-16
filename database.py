
import sqlite3
from datetime import datetime

DB_NAME = "poems.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT,
            theme TEXT,
            language TEXT,
            style TEXT,
            content TEXT,
            created_at TEXT,
            favourite INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def save_content(
    content_type,
    theme,
    language,
    style,
    content,
    favourite=False
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO poems (
            content_type, theme, language,
            style, content, created_at, favourite
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        content_type,
        theme,
        language,
        style,
        content,
        datetime.now().strftime("%d-%m-%Y %H:%M"),
        int(favourite)
    ))

    conn.commit()
    conn.close()


def get_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM poems
        ORDER BY id DESC
    """)

    records = cursor.fetchall()
    conn.close()

    return records


def get_favourites():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM poems
        WHERE favourite = 1
        ORDER BY id DESC
    """)

    records = cursor.fetchall()
    conn.close()

    return records


def delete_content(poem_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM poems WHERE id = ?",
        (poem_id,)
    )

    conn.commit()
    conn.close()


def toggle_favourite(poem_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE poems
        SET favourite = ?
        WHERE id = ?
    """, (int(status), poem_id))

    conn.commit()
    conn.close()
