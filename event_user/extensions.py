from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."
login_manager.login_message_category = "warning"

# "strong": Flask-Login sẽ so khớp dấu vân tay (IP + User-Agent) của phiên,
# nếu khác thì hủy phiên -> chống đánh cắp / dùng lại cookie phiên.
login_manager.session_protection = "strong"
