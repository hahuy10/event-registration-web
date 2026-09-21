<<<<<<< HEAD
# Hệ thống tài khoản Flask — Đăng ký / Đăng nhập / Phân quyền / Bảo mật phiên

## 1. Cài đặt

```bash
cd auth_app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Tạo file `.env` cùng thư mục:

```
SECRET_KEY=dan-mot-chuoi-ngau-nhien-that-dai
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db
```

Sinh SECRET_KEY: `python -c "import secrets;print(secrets.token_hex(32))"`

## 2. Chạy

```bash
python app.py
```

Mở http://127.0.0.1:5000

Tài khoản **đầu tiên đăng ký sẽ tự động là Admin**. Hoặc tạo admin bằng lệnh:

```bash
flask --app app create-admin
```

## 3. Cấu trúc

| File | Vai trò |
|---|---|
| `config.py` | Toàn bộ cấu hình bảo mật (cookie, timeout, khóa tài khoản) |
| `models.py` | Model `User`: băm mật khẩu, vai trò, token phiên |
| `forms.py` | Validate dữ liệu + sinh token CSRF |
| `auth.py` | Đăng ký, đăng nhập, đăng xuất, đổi mật khẩu |
| `admin.py` | Khu vực quản trị: đổi vai trò, khóa/mở tài khoản |
| `decorators.py` | `@admin_required`, `@role_required(...)` |
| `app.py` | Application factory, security headers, lệnh CLI |

## 4. Các biện pháp bảo mật đã áp dụng

**Mật khẩu**
- Băm bằng `scrypt` + salt ngẫu nhiên, không lưu mật khẩu gốc.
- Bắt buộc ≥ 8 ký tự, có chữ hoa, chữ thường và số.

**Chống dò mật khẩu**
- Sai 5 lần → khóa tài khoản 15 phút (`MAX_LOGIN_ATTEMPTS`, `LOCKOUT_MINUTES`).
- Thông báo lỗi chung chung, không tiết lộ tài khoản nào tồn tại.

**Phiên đăng nhập**
- Cookie: `HttpOnly` (JS không đọc được), `Secure` (chỉ HTTPS), `SameSite=Lax`.
- `session.clear()` trước khi cấp phiên mới → chống **Session Fixation**.
- Tự hết hạn sau 30 phút không hoạt động, gia hạn khi còn thao tác.
- `session_protection = "strong"` → cookie bị mang sang máy khác sẽ bị hủy.
- `session_token` lưu trong DB: đổi mật khẩu / bị khóa / bị đổi quyền → **mọi phiên cũ bị vô hiệu ngay**.

**Khác**
- CSRF token cho mọi form (Flask-WTF); đăng xuất bắt buộc dùng POST.
- Chống Open Redirect ở tham số `?next=`.
- Header: `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `HSTS`.
- Dùng ORM (SQLAlchemy) và auto-escape của Jinja2 → chống SQL Injection, XSS.

## 5. Phân quyền

```python
from decorators import admin_required, role_required

@app.route("/khu-vuc-admin")
@login_required
@admin_required
def only_admin(): ...

@app.route("/bao-cao")
@login_required
@role_required("admin", "manager")   # mở rộng nhiều vai trò
def report(): ...
```

Trong template: `{% if current_user.is_admin %} ... {% endif %}`

## 6. Khi đưa lên server thật

1. Đặt `FLASK_ENV=production` (bật `SESSION_COOKIE_SECURE`) và chạy sau HTTPS.
2. `SECRET_KEY` lấy từ biến môi trường, không commit lên Git.
3. Đổi sang PostgreSQL/MySQL thay cho SQLite.
4. Chạy bằng Gunicorn: `gunicorn -w 4 "app:app"` đặt sau Nginx.
5. Cân nhắc thêm: xác minh email, đặt lại mật khẩu qua email, 2FA, ghi log đăng nhập.
=======
 event-registration-web
>>>>>>> 51d0b85109e876ebaeeb2f934f92aacbdf81a8a5
