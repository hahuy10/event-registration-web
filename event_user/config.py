import os
from datetime import timedelta


class Config:
    # --- Khóa bí mật dùng để ký cookie phiên ---
    # BẮT BUỘC đặt biến môi trường SECRET_KEY khi chạy thật.
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------- BẢO MẬT PHIÊN ĐĂNG NHẬP ----------
    # Cookie không cho JavaScript đọc -> chống đánh cắp session bằng XSS
    SESSION_COOKIE_HTTPONLY = True
    # Chỉ gửi cookie qua HTTPS. Khi dev ở localhost (http) đặt biến
    # FLASK_ENV=development để tắt, nếu không sẽ không đăng nhập được.
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") != "development"
    # Chống CSRF ở tầng cookie
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_NAME = "sid"

    # Phiên hết hạn sau 30 phút KHÔNG hoạt động (idle timeout)
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    # Mỗi request hợp lệ sẽ gia hạn lại thời gian sống của cookie
    SESSION_REFRESH_EACH_REQUEST = True

    # Token CSRF cho form hết hạn sau 1 giờ
    WTF_CSRF_TIME_LIMIT = 3600

    # ---------- CHÍNH SÁCH ĐĂNG NHẬP ----------
    MAX_LOGIN_ATTEMPTS = 5              # sai quá số lần này thì khóa
    LOCKOUT_MINUTES = 15                # thời gian khóa tài khoản
    PASSWORD_MIN_LENGTH = 8
