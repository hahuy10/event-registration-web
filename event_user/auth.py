from datetime import datetime
from urllib.parse import urlparse

from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, session, current_app)
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User
from forms import RegisterForm, LoginForm, ChangePasswordForm

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def is_safe_url(target: str) -> bool:
    """Chỉ cho redirect về chính site này -> chống open redirect."""
    if not target:
        return False
    ref = urlparse(request.host_url)
    test = urlparse(target)
    return test.scheme in ("", "http", "https") and (test.netloc in ("", ref.netloc))


# ----------------------- ĐĂNG KÝ -----------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            # Người đầu tiên đăng ký sẽ là admin, còn lại là user
            role="admin" if User.query.count() == 0 else "user",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Đăng ký thành công! Mời bạn đăng nhập.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


# ----------------------- ĐĂNG NHẬP -----------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        identity = form.identity.data.strip()
        user = (User.query.filter_by(username=identity).first()
                or User.query.filter_by(email=identity.lower()).first())

        if user and user.is_locked:
            flash(
                f"Tài khoản đang bị tạm khóa do đăng nhập sai nhiều lần. "
                f"Vui lòng thử lại sau {current_app.config['LOCKOUT_MINUTES']} phút.",
                "danger",
            )
            return render_template("login.html", form=form)

        if user is None or not user.check_password(form.password.data):
            if user is not None:
                user.register_failed_login()
                db.session.commit()
            # Thông báo chung chung để không lộ tài khoản nào tồn tại
            flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")
            return render_template("login.html", form=form)

        if not user.active:
            flash("Tài khoản của bạn đã bị vô hiệu hóa.", "danger")
            return render_template("login.html", form=form)

        # --- Đăng nhập thành công ---
        # Xóa sạch session cũ trước khi cấp phiên mới -> chống Session Fixation
        session.clear()
        login_user(user, remember=form.remember.data)
        session.permanent = True          # áp dụng thời hạn idle timeout
        session["login_at"] = datetime.utcnow().isoformat()

        user.reset_failed_login()
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        db.session.commit()

        next_page = request.args.get("next")
        if not is_safe_url(next_page):
            next_page = url_for("main.dashboard")
        flash(f"Xin chào {user.username}!", "success")
        return redirect(next_page)

    return render_template("login.html", form=form)


# ----------------------- ĐĂNG XUẤT -----------------------
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("auth.login"))


# ----------------------- ĐỔI MẬT KHẨU -----------------------
@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash("Mật khẩu hiện tại không đúng.", "danger")
            return render_template("change_password.html", form=form)

        current_user.set_password(form.password.data)
        # Thu hồi toàn bộ phiên cũ trên mọi thiết bị
        current_user.rotate_session_token()
        db.session.commit()

        logout_user()
        session.clear()
        flash("Đổi mật khẩu thành công. Vui lòng đăng nhập lại.", "success")
        return redirect(url_for("auth.login"))

    return render_template("change_password.html", form=form)
