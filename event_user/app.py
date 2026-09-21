import os

import click
from dotenv import load_dotenv
from flask import Flask, render_template, session
from flask_login import current_user

from config import Config
from extensions import db, csrf, login_manager

load_dotenv()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    import models  # noqa: F401  (đăng ký model + user_loader)
    from auth import auth_bp
    from admin import admin_bp
    from main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # --- Gia hạn phiên theo hoạt động của người dùng ---
    @app.before_request
    def refresh_session():
        session.permanent = True
        session.modified = True

    # --- Thêm các HTTP security header ---
    @app.after_request
    def set_security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'"
        if app.config.get("SESSION_COOKIE_SECURE"):
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resp

    # --- Trang lỗi ---
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403,
                               message="Bạn không có quyền truy cập trang này."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404,
                               message="Không tìm thấy trang."), 404

    @app.context_processor
    def inject_user():
        return {"current_user": current_user}

    # --- Lệnh CLI ---
    @app.cli.command("init-db")
    def init_db():
        """Tạo bảng trong CSDL."""
        db.create_all()
        click.echo("Đã tạo cơ sở dữ liệu.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, email, password):
        """Tạo tài khoản quản trị."""
        from models import User
        if User.query.filter((User.username == username) | (User.email == email)).first():
            click.echo("Tên đăng nhập hoặc email đã tồn tại.")
            return
        user = User(username=username, email=email.lower(), role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Đã tạo admin: {username}")

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_ENV") == "development")
