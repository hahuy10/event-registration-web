"""
app.py
File chạy demo ĐỘC LẬP cho Module 3.
Khi ghép vào project chung của nhóm, Nhóm trưởng chỉ cần:
    from module3_search import bp_module3
    app.register_blueprint(bp_module3)
trong app.py chính của cả nhóm (thay vì chạy file này).
"""
from flask import Flask
from module3_search import bp_module3
import os

app = Flask(__name__)
app.register_blueprint(bp_module3)

if __name__ == "__main__":
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "events.db")):
        print("Chưa có database, đang tạo dữ liệu mẫu...")
        from seed_data import init_db
        init_db()

    app.run(debug=True, port=5000)
