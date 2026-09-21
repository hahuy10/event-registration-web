# ── Thêm vào cuối models.py của Module 1 ──────────────────────────

class Event(db.Model):
    __tablename__ = "events"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(255), nullable=False)
    description  = db.Column(db.Text)
    banner_image = db.Column(db.String(255))
    event_date   = db.Column(db.String(20))   # format: YYYY-MM-DD
    category_id  = db.Column(db.Integer)
    location_id  = db.Column(db.Integer)
    is_featured  = db.Column(db.Boolean, default=False)
    created_by   = db.Column(db.Integer, db.ForeignKey("users.id"))

    registrations = db.relationship("Registration", backref="event", lazy=True)


class Registration(db.Model):
    __tablename__ = "registrations"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id      = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    status        = db.Column(db.String(20), default="registered")
    # status: "registered" hoặc "cancelled"