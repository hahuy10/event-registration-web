import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from models import User


def strong_password(form, field):
    """Mật khẩu phải đủ dài, có chữ hoa, chữ thường và số."""
    pwd = field.data or ""
    if len(pwd) < 8:
        raise ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")
    if not re.search(r"[A-Z]", pwd):
        raise ValidationError("Mật khẩu phải có ít nhất 1 chữ in hoa.")
    if not re.search(r"[a-z]", pwd):
        raise ValidationError("Mật khẩu phải có ít nhất 1 chữ thường.")
    if not re.search(r"\d", pwd):
        raise ValidationError("Mật khẩu phải có ít nhất 1 chữ số.")


class RegisterForm(FlaskForm):
    username = StringField(
        "Tên đăng nhập",
        validators=[DataRequired("Vui lòng nhập tên đăng nhập."), Length(3, 50)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired("Vui lòng nhập email."), Email("Email không hợp lệ."), Length(max=120)],
    )
    password = PasswordField("Mật khẩu", validators=[DataRequired(), strong_password])
    confirm = PasswordField(
        "Nhập lại mật khẩu",
        validators=[DataRequired(), EqualTo("password", "Mật khẩu nhập lại không khớp.")],
    )
    submit = SubmitField("Đăng ký")

    def validate_username(self, field):
        if not re.fullmatch(r"[A-Za-z0-9_.]+", field.data or ""):
            raise ValidationError("Tên đăng nhập chỉ gồm chữ, số, dấu _ và .")
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Tên đăng nhập đã tồn tại.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("Email đã được sử dụng.")


class LoginForm(FlaskForm):
    identity = StringField(
        "Tên đăng nhập hoặc Email", validators=[DataRequired("Vui lòng nhập thông tin.")]
    )
    password = PasswordField("Mật khẩu", validators=[DataRequired("Vui lòng nhập mật khẩu.")])
    remember = BooleanField("Ghi nhớ đăng nhập")
    submit = SubmitField("Đăng nhập")


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Mật khẩu hiện tại", validators=[DataRequired()])
    password = PasswordField("Mật khẩu mới", validators=[DataRequired(), strong_password])
    confirm = PasswordField(
        "Nhập lại mật khẩu mới",
        validators=[DataRequired(), EqualTo("password", "Mật khẩu nhập lại không khớp.")],
    )
    submit = SubmitField("Đổi mật khẩu")


class RoleForm(FlaskForm):
    """Form nhỏ để admin đổi quyền — chủ yếu để có token CSRF."""
    role = SelectField("Vai trò", choices=[("user", "User"), ("admin", "Admin")])
    submit = SubmitField("Lưu")
