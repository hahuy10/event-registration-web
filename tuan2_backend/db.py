"""
db.py
Lớp tiện ích kết nối SQLite dùng chung cho toàn bộ ứng dụng.
Trong dự án thật, file này sẽ được dùng chung bởi cả 5 module.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "events.db")


def get_connection():
    """Mở kết nối tới SQLite, trả về dòng dạng dict (row_factory)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # cho phép truy cập cột theo tên: row["name"]
    return conn
