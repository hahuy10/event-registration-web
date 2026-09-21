from functools import wraps

from flask import abort, redirect, url_for, flash
from flask_login import current_user


def role_required(*roles):
    """Chỉ cho phép user có vai trò nằm trong danh sách roles truy cập."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Vui lòng đăng nhập để tiếp tục.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(view):
    return role_required("admin")(view)
