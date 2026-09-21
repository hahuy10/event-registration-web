"""Website đăng ký sự kiện — Flask + SQLite.

Chạy:  pip install -r requirements.txt  &&  python app.py
Quản trị mặc định: admin / admin123  (đổi trong config bên dưới)
"""
import io
import os
import csv
import random
import string
from datetime import datetime
from functools import wraps

import qrcode
from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_file, session, url_for, Response)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from vietqr import build_vietqr_payload, no_accent

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "doi-chuoi-bi-mat-nay-khi-chay-that"),
    SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(BASE_DIR, "events.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,  # banner tối đa 8MB
    UPLOAD_FOLDER=UPLOAD_DIR,
)

# ---- Thông tin tài khoản nhận tiền (hiện trên mã QR + hoá đơn) ----
PAYEE = {
    "bank_name": "Vietcombank",
    "bank_bin": "970436",
    "account_no": "0071000123456",
    "account_name": "CONG TY SU KIEN VIET",
}
ORG = {
    "name": "Công ty TNHH Sự Kiện Việt",
    "address": "12 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh",
    "tax_code": "0312345678",
    "email": "hotro@sukienviet.vn",
    "hotline": "1900 1234",
}
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin123"))

db = SQLAlchemy(app)


# ----------------------------------------------------------------- MODELS
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(300), default="")
    description = db.Column(db.Text, default="")
    location = db.Column(db.String(200), default="")
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime)
    capacity = db.Column(db.Integer, default=100)          # 0 = không giới hạn
    price = db.Column(db.Integer, default=0)               # 0 = miễn phí
    banner = db.Column(db.String(255))
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    registrations = db.relationship(
        "Registration", backref="event", cascade="all, delete-orphan", lazy=True
    )

    @property
    def is_free(self):
        return (self.price or 0) <= 0

    @property
    def sold(self):
        return sum(r.quantity for r in self.registrations
                   if r.status in ("paid", "pending"))

    @property
    def seats_left(self):
        if not self.capacity:
            return None
        return max(self.capacity - self.sold, 0)

    @property
    def is_past(self):
        return self.start_at < datetime.now()

    @property
    def sold_out(self):
        return self.seats_left is not None and self.seats_left <= 0


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), default="")
    note = db.Column(db.String(300), default="")
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Integer, default=0)
    amount = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="pending")   # pending | paid | cancelled
    invoice_no = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.now)
    paid_at = db.Column(db.DateTime)

    @property
    def status_label(self):
        return {"pending": "Chờ thanh toán",
                "paid": "Đã thanh toán",
                "cancelled": "Đã huỷ"}.get(self.status, self.status)

    @property
    def transfer_content(self):
        return no_accent(f"SK {self.code}")


# ----------------------------------------------------------------- HELPERS
def gen_code(prefix="DK", n=6):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = prefix + "".join(random.choices(alphabet, k=n))
        if not Registration.query.filter_by(code=code).first():
            return code


def next_invoice_no():
    today = datetime.now()
    count = Registration.query.filter(Registration.invoice_no.isnot(None)).count() + 1
    return f"HD{today:%Y%m}-{count:04d}"


def money(v):
    return f"{int(v or 0):,}".replace(",", ".") + " ₫"


def parse_dt(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")


def save_banner(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    name = secure_filename(file_storage.filename)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXT:
        raise ValueError("Chỉ nhận ảnh PNG, JPG, WEBP hoặc GIF.")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{datetime.now():%Y%m%d%H%M%S}-{random.randint(100, 999)}.{ext}"
    file_storage.save(os.path.join(UPLOAD_DIR, filename))
    return filename


def delete_banner(filename):
    if not filename:
        return
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        os.remove(path)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            flash("Đăng nhập để vào trang quản lý.", "warn")
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


app.jinja_env.filters["money"] = money
app.jinja_env.globals.update(ORG=ORG, PAYEE=PAYEE, now=datetime.now)


# ----------------------------------------------------------------- PUBLIC
@app.route("/")
def index():
    q = (request.args.get("q") or "").strip()
    query = Event.query.filter_by(published=True)
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Event.title.ilike(like),
                                    Event.location.ilike(like),
                                    Event.summary.ilike(like)))
    events = query.order_by(Event.start_at.asc()).all()
    upcoming = [e for e in events if not e.is_past]
    past = [e for e in events if e.is_past]
    return render_template("index.html", upcoming=upcoming, past=past, q=q)


@app.route("/su-kien/<int:event_id>")
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    if not event.published and not session.get("admin"):
        abort(404)
    return render_template("event_detail.html", event=event)


@app.route("/su-kien/<int:event_id>/dang-ky", methods=["GET", "POST"])
def register(event_id):
    event = Event.query.get_or_404(event_id)
    if event.is_past:
        flash("Sự kiện đã diễn ra, không thể đăng ký.", "warn")
        return redirect(url_for("event_detail", event_id=event.id))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        note = (request.form.get("note") or "").strip()
        try:
            quantity = max(1, int(request.form.get("quantity") or 1))
        except ValueError:
            quantity = 1

        if not full_name or not email:
            flash("Nhập họ tên và email để tiếp tục.", "error")
            return render_template("register.html", event=event, form=request.form)

        if event.seats_left is not None and quantity > event.seats_left:
            flash(f"Chỉ còn {event.seats_left} chỗ cho sự kiện này.", "error")
            return render_template("register.html", event=event, form=request.form)

        reg = Registration(
            code=gen_code(),
            event_id=event.id,
            full_name=full_name,
            email=email,
            phone=phone,
            note=note,
            quantity=quantity,
            unit_price=event.price or 0,
            amount=(event.price or 0) * quantity,
        )
        if event.is_free:
            reg.status = "paid"
            reg.paid_at = datetime.now()
            reg.invoice_no = next_invoice_no()
        db.session.add(reg)
        db.session.commit()

        if event.is_free:
            flash("Đăng ký thành công. Vé của bạn đã sẵn sàng.", "ok")
            return redirect(url_for("invoice", code=reg.code))
        return redirect(url_for("payment", code=reg.code))

    return render_template("register.html", event=event, form={})


@app.route("/thanh-toan/<code>")
def payment(code):
    reg = Registration.query.filter_by(code=code).first_or_404()
    if reg.status == "paid":
        return redirect(url_for("invoice", code=reg.code))
    return render_template("payment.html", reg=reg, event=reg.event)


@app.route("/thanh-toan/<code>/qr.png")
def payment_qr(code):
    """Ảnh QR chuyển khoản, quét được bằng mọi app ngân hàng hỗ trợ VietQR."""
    reg = Registration.query.filter_by(code=code).first_or_404()
    payload = build_vietqr_payload(
        bank_bin=PAYEE["bank_bin"],
        account_no=PAYEE["account_no"],
        amount=reg.amount,
        description=reg.transfer_content,
        account_name=PAYEE["account_name"],
    )
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/thanh-toan/<code>/xac-nhan", methods=["POST"])
def confirm_payment(code):
    """Mô phỏng callback của cổng thanh toán / ngân hàng.

    Khi tích hợp thật (VNPAY, MoMo, casso.vn…), gọi hàm mark_paid() trong webhook
    sau khi đã đối soát số tiền và nội dung chuyển khoản.
    """
    reg = Registration.query.filter_by(code=code).first_or_404()
    mark_paid(reg)
    flash("Đã ghi nhận thanh toán. Hoá đơn của bạn ở bên dưới.", "ok")
    return redirect(url_for("invoice", code=reg.code))


def mark_paid(reg):
    if reg.status != "paid":
        reg.status = "paid"
        reg.paid_at = datetime.now()
        reg.invoice_no = reg.invoice_no or next_invoice_no()
        db.session.commit()


@app.route("/ve/<code>/qr.png")
def ticket_qr(code):
    """QR chứa mã vé, dùng để quét check-in tại cửa."""
    reg = Registration.query.filter_by(code=code).first_or_404()
    img = qrcode.make(f"VE|{reg.code}|{reg.event_id}")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/hoa-don/<code>")
def invoice(code):
    reg = Registration.query.filter_by(code=code).first_or_404()
    if reg.status != "paid":
        return redirect(url_for("payment", code=reg.code))
    return render_template("invoice.html", reg=reg, event=reg.event)


@app.route("/tra-cuu", methods=["GET", "POST"])
def lookup():
    reg = None
    if request.method == "POST":
        code = (request.form.get("code") or "").strip().upper()
        reg = Registration.query.filter_by(code=code).first()
        if not reg:
            flash("Không tìm thấy mã đăng ký này. Kiểm tra lại mã trong email xác nhận.", "error")
    return render_template("lookup.html", reg=reg)


# ----------------------------------------------------------------- ADMIN
@app.route("/admin/dang-nhap", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = request.form.get("username") or ""
        pwd = request.form.get("password") or ""
        if user == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, pwd):
            session["admin"] = user
            return redirect(request.args.get("next") or url_for("admin_events"))
        flash("Sai tài khoản hoặc mật khẩu.", "error")
    return render_template("admin_login.html")


@app.route("/admin/dang-xuat")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
def admin_events():
    events = Event.query.order_by(Event.start_at.desc()).all()
    revenue = db.session.query(db.func.sum(Registration.amount)).filter(
        Registration.status == "paid").scalar() or 0
    pending = Registration.query.filter_by(status="pending").count()
    return render_template("admin_events.html", events=events,
                           revenue=revenue, pending=pending)


@app.route("/admin/su-kien/them", methods=["GET", "POST"])
@app.route("/admin/su-kien/<int:event_id>/sua", methods=["GET", "POST"])
@login_required
def event_form(event_id=None):
    event = Event.query.get_or_404(event_id) if event_id else None

    if request.method == "POST":
        f = request.form
        title = (f.get("title") or "").strip()
        start_at = parse_dt(f.get("start_at"))
        if not title or not start_at:
            flash("Cần có tên sự kiện và thời gian bắt đầu.", "error")
            return render_template("event_form.html", event=event, form=f)

        if event is None:
            event = Event(title=title, start_at=start_at)
            db.session.add(event)

        event.title = title
        event.start_at = start_at
        event.end_at = parse_dt(f.get("end_at"))
        event.summary = (f.get("summary") or "").strip()
        event.description = (f.get("description") or "").strip()
        event.location = (f.get("location") or "").strip()
        event.capacity = int(f.get("capacity") or 0)
        event.price = int(f.get("price") or 0)
        event.published = bool(f.get("published"))

        try:
            new_banner = save_banner(request.files.get("banner"))
        except ValueError as err:
            db.session.rollback()
            flash(str(err), "error")
            return render_template("event_form.html", event=None if not event_id else event, form=f)
        if new_banner:
            delete_banner(event.banner)
            event.banner = new_banner
        if f.get("remove_banner"):
            delete_banner(event.banner)
            event.banner = None

        db.session.commit()
        flash("Đã lưu sự kiện.", "ok")
        return redirect(url_for("admin_events"))

    return render_template("event_form.html", event=event, form={})


@app.route("/admin/su-kien/<int:event_id>/xoa", methods=["POST"])
@login_required
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    delete_banner(event.banner)
    db.session.delete(event)          # xoá luôn các đăng ký thuộc sự kiện
    db.session.commit()
    flash("Đã xoá sự kiện và toàn bộ đăng ký của sự kiện đó.", "ok")
    return redirect(url_for("admin_events"))


@app.route("/admin/dang-ky")
@app.route("/admin/dang-ky/<int:event_id>")
@login_required
def admin_registrations(event_id=None):
    query = Registration.query
    event = None
    if event_id:
        event = Event.query.get_or_404(event_id)
        query = query.filter_by(event_id=event_id)
    status = request.args.get("status")
    if status in ("pending", "paid", "cancelled"):
        query = query.filter_by(status=status)
    regs = query.order_by(Registration.created_at.desc()).all()
    return render_template("admin_registrations.html", regs=regs,
                           event=event, status=status)


@app.route("/admin/dang-ky/<code>/thanh-toan", methods=["POST"])
@login_required
def admin_mark_paid(code):
    reg = Registration.query.filter_by(code=code).first_or_404()
    mark_paid(reg)
    flash(f"Đã xác nhận thanh toán cho {reg.code}.", "ok")
    return redirect(request.referrer or url_for("admin_registrations"))


@app.route("/admin/dang-ky/<code>/huy", methods=["POST"])
@login_required
def admin_cancel(code):
    reg = Registration.query.filter_by(code=code).first_or_404()
    reg.status = "cancelled"
    db.session.commit()
    flash(f"Đã huỷ đăng ký {reg.code}.", "ok")
    return redirect(request.referrer or url_for("admin_registrations"))


@app.route("/admin/dang-ky/<code>/xoa", methods=["POST"])
@login_required
def admin_delete_reg(code):
    reg = Registration.query.filter_by(code=code).first_or_404()
    db.session.delete(reg)
    db.session.commit()
    flash("Đã xoá đăng ký.", "ok")
    return redirect(request.referrer or url_for("admin_registrations"))


@app.route("/admin/xuat-csv")
@login_required
def export_csv():
    rows = Registration.query.order_by(Registration.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Mã", "Sự kiện", "Họ tên", "Email", "Điện thoại",
                     "Số lượng", "Số tiền", "Trạng thái", "Số hoá đơn", "Ngày đăng ký"])
    for r in rows:
        writer.writerow([r.code, r.event.title, r.full_name, r.email, r.phone,
                         r.quantity, r.amount, r.status_label, r.invoice_no or "",
                         r.created_at.strftime("%d/%m/%Y %H:%M")])
    data = "\ufeff" + buf.getvalue()      # BOM để Excel đọc đúng tiếng Việt
    return Response(data, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=dang-ky.csv"})


# ----------------------------------------------------------------- SEED
def seed():
    if Event.query.count():
        return
    db.session.add_all([
        Event(title="Ngày hội khởi nghiệp Sài Gòn 2026",
              summary="Gặp gỡ 40 quỹ đầu tư và hơn 100 startup trong một ngày.",
              description="Buổi sáng là các phiên chia sẻ về gọi vốn vòng hạt giống. "
                          "Buổi chiều mở khu triển lãm và bàn tròn 1-1 với nhà đầu tư.\n"
                          "Vé bao gồm ăn trưa và tài liệu hội thảo.",
              location="GEM Center, 8 Nguyễn Bỉnh Khiêm, Quận 1",
              start_at=datetime(2026, 11, 14, 8, 30),
              end_at=datetime(2026, 11, 14, 17, 0),
              capacity=300, price=350000),
        Event(title="Workshop nhiếp ảnh đường phố",
              summary="Buổi thực hành 3 tiếng quanh Chợ Lớn cùng nhiếp ảnh gia Minh Trí.",
              description="Mang theo máy ảnh hoặc điện thoại. Nhóm tối đa 20 người "
                          "để ai cũng được nhận xét ảnh trực tiếp.",
              location="Điểm tập trung: Bưu điện Quận 5",
              start_at=datetime(2026, 10, 25, 15, 0),
              end_at=datetime(2026, 10, 25, 18, 0),
              capacity=20, price=180000),
        Event(title="Cà phê cuối tuần cho người học Python",
              summary="Buổi gặp miễn phí, mang laptop và câu hỏi của bạn.",
              description="Không có slide, không có diễn giả. Mọi người ngồi lại, "
                          "ai đang mắc gì thì đưa ra, cả nhóm cùng gỡ.",
              location="The Coffee House, 86 Cao Thắng, Quận 3",
              start_at=datetime(2026, 10, 4, 9, 0),
              end_at=datetime(2026, 10, 4, 11, 0),
              capacity=40, price=0),
    ])
    db.session.commit()


with app.app_context():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    db.create_all()
    seed()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
