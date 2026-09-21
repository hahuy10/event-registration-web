from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import User
from decorators import admin_required
from forms import RoleForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("admin/users.html", pagination=pagination, form=RoleForm())


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def change_role(user_id):
    form = RoleForm()
    if not form.validate_on_submit():
        flash("Yêu cầu không hợp lệ.", "danger")
        return redirect(url_for("admin.users"))

    user = db.get_or_404(User, user_id)

    if user.id == current_user.id:
        flash("Bạn không thể tự đổi quyền của chính mình.", "warning")
        return redirect(url_for("admin.users"))

    # Không để hệ thống mất admin cuối cùng
    if user.is_admin and form.role.data != "admin":
        if User.query.filter_by(role="admin").count() <= 1:
            flash("Phải còn ít nhất một tài khoản Admin.", "warning")
            return redirect(url_for("admin.users"))

    user.role = form.role.data
    user.rotate_session_token()   # buộc user đó đăng nhập lại với quyền mới
    db.session.commit()
    flash(f"Đã đổi quyền của {user.username} thành {user.role}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    form = RoleForm()           # dùng lại để kiểm tra CSRF
    if not form.csrf_token.validate(form):
        flash("Yêu cầu không hợp lệ.", "danger")
        return redirect(url_for("admin.users"))

    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Bạn không thể tự khóa tài khoản của mình.", "warning")
        return redirect(url_for("admin.users"))

    user.active = not user.active
    if not user.active:
        user.rotate_session_token()   # đá user ra khỏi mọi phiên đang mở
    db.session.commit()
    flash(
        f"Đã {'mở khóa' if user.active else 'vô hiệu hóa'} tài khoản {user.username}.",
        "success",
    )
    return redirect(url_for("admin.users"))
