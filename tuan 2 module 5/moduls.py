from extensions import db
from datetime import datetime

class Registration(db.Model):
    __tablename__ = 'registrations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    # Số lượng vé người này đăng ký (khớp với property sold của Người 2)
    quantity = db.Column(db.Integer, default=1) 
    
    # Trạng thái: 'pending', 'paid', hoặc 'cancelled' (khớp với logic Người 2)
    status = db.Column(db.String(20), default='paid') 
    
    registered_at = db.Column(db.DateTime, default=datetime.now)

    # Thiết lập Relationship ngược lại với bảng User (nếu Người 1 chưa làm)
    user = db.relationship("User", backref=db.backref("registrations", lazy=True))

    @property
    def is_cancelled(self):
        return self.status == 'cancelled'