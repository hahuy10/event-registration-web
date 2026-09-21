import sqlite3
from database import get_connection


def is_already_registered(email: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM participants WHERE email = ?",
        (email,)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def register_participant(full_name: str, email: str, phone: str = "") -> dict:
    if not full_name or not email:
        return {"success": False, "message": "Vui lòng nhập đầy đủ Họ tên và Email."}

    if is_already_registered(email):
        return {"success": False, "message": "Email này đã đăng ký rồi."}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO participants (full_name, email, phone)
               VALUES (?, ?, ?)""",
            (full_name, email, phone)
        )
        conn.commit()
        return {"success": True, "message": "Đăng ký thành công!"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Email này đã đăng ký rồi."}
    finally:
        conn.close()


def get_participants() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants ORDER BY registered_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def cancel_registration(participant_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM participants WHERE id = ?", (participant_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0