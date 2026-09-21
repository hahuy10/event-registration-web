import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()  # đọc file .env

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")


def send_confirmation_email(to_email: str, full_name: str) -> dict:
    subject = "Xác nhận đăng ký sự kiện"
    body = f"""Xin chào {full_name},

Bạn đã đăng ký thành công sự kiện.
Cảm ơn bạn đã tham gia!

Trân trọng,
Ban tổ chức sự kiện.
"""

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return {"success": True, "message": f"Đã gửi email xác nhận tới {to_email}"}
    except Exception as e:
        return {"success": False, "message": f"Gửi email thất bại: {e}"}
