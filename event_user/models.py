import secrets
from datetime import datetime, timedelta

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # KHÔNG BAO GIỜ lưu mật khẩu gốc, chỉ lưu chuỗi băm
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' | 'admin'
    active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))

    # Chống dò mật khẩu (brute force)
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime)

    # Thay đổi token này -> mọi phiên đang đăng nhập của user bị vô hiệu
    session_token = db.Column(db.String(64), nullable=False,
                              default=lambda: secrets.token_hex(32))

    # ---------- Mật khẩu ----------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password, method="scrypt")

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # ---------- Khóa tài khoản ----------
    @property
    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > datetime.utcnow()

    def register_failed_login(self) -> None:
        self.failed_attempts += 1
        if self.failed_attempts >= current_app.config["MAX_LOGIN_ATTEMPTS"]:
            self.locked_until = datetime.utcnow() + timedelta(
                minutes=current_app.config["LOCKOUT_MINUTES"]
            )
            self.failed_attempts = 0

    def reset_failed_login(self) -> None:
        self.failed_attempts = 0
        self.locked_until = None

    def rotate_session_token(self) -> None:
        """Gọi khi đổi mật khẩu hoặc muốn đăng xuất khỏi mọi thiết bị."""
        self.session_token = secrets.token_hex(32)

    # ---------- Phân quyền ----------
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    # ---------- Flask-Login ----------
    @property
    def is_active(self) -> bool:
        # Tài khoản bị admin vô hiệu hóa thì không đăng nhập được
        return self.active

    def get_id(self) -> str:
        # Nhúng session_token vào id phiên để có thể thu hồi phiên từ server
        return f"{self.id}|{self.session_token}"

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


@login_manager.user_loader
def load_user(user_id: str):
    try:
        raw_id, token = user_id.split("|", 1)
        user = db.session.get(User, int(raw_id))
    except (ValueError, AttributeError):
        return None

    # Token không khớp -> phiên đã bị thu hồi
    if user is None or not secrets.compare_digest(user.session_token, token):
        return None
    if not user.active:
        return None
    return user
