"""
seed_data.py
Khởi tạo database SQLite (events.db) từ schema.sql,
và chèn dữ liệu mẫu: 3 loại sự kiện, 4 địa điểm, 10 sự kiện thật.
Chạy 1 lần: python seed_data.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "events.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # làm mới mỗi lần seed để tránh trùng dữ liệu

    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    cur = conn.cursor()

    # ---- Loại sự kiện (Category) ----
    categories = ["Hội thảo / Workshop", "Âm nhạc", "Thể thao", "Công nghệ"]
    cur.executemany("INSERT INTO category (name) VALUES (?)", [(c,) for c in categories])

    # ---- Địa điểm (Location) ----
    locations = [
        ("Nhà văn hóa Thanh Niên", "4 Phạm Ngọc Thạch, Q.1, TP.HCM"),
        ("Trung tâm Hội nghị White Palace", "194 Hoàng Văn Thụ, Q. Phú Nhuận, TP.HCM"),
        ("SVĐ Thống Nhất", "138 Đào Duy Từ, Q.10, TP.HCM"),
        ("Đại học Bách Khoa TP.HCM", "268 Lý Thường Kiệt, Q.10, TP.HCM"),
    ]
    cur.executemany("INSERT INTO location (name, address) VALUES (?, ?)", locations)

    # ---- 10 sự kiện thật (Tiêu chí 4: mỗi người tự chuẩn bị 10 bộ dữ liệu) ----
    # (name, description, banner_image, event_date, category_id, location_id, is_featured, created_by)
    events = [
        ("Workshop Kỹ năng viết CV & Phỏng vấn", "Hướng dẫn viết CV chuẩn và luyện phỏng vấn thực tế cho sinh viên năm cuối.",
         "workshop_cv.jpg", "2026-10-05", 1, 1, 1, 1),
        ("Đêm nhạc Acoustic Sài Gòn", "Chương trình acoustic quy tụ các nghệ sĩ indie nổi bật của TP.HCM.",
         "acoustic_night.jpg", "2026-10-12", 2, 2, 1, 1),
        ("Giải chạy bộ Marathon TP.HCM 2026", "Giải marathon phong trào 5km/10km/21km dành cho mọi lứa tuổi.",
         "marathon_2026.jpg", "2026-11-02", 3, 3, 1, 1),
        ("Tech Talk: AI trong đời sống", "Chia sẻ ứng dụng thực tế của AI từ các chuyên gia trong ngành.",
         "techtalk_ai.jpg", "2026-10-20", 4, 4, 0, 1),
        ("Workshop Kỹ năng thuyết trình", "Rèn luyện kỹ năng thuyết trình tự tin trước đám đông.",
         "workshop_presentation.jpg", "2026-10-08", 1, 1, 0, 1),
        ("Liveshow Rock Underground", "Đêm diễn quy tụ các ban nhạc rock underground trẻ.",
         "rock_night.jpg", "2026-11-15", 2, 2, 0, 1),
        ("Giải bóng đá sinh viên mở rộng", "Giải bóng đá 7 người dành cho sinh viên các trường ĐH khu vực TP.HCM.",
         "football_cup.jpg", "2026-10-25", 3, 3, 0, 1),
        ("Hội thảo Chuyển đổi số cho doanh nghiệp nhỏ", "Giải pháp chuyển đổi số thực tiễn cho SME.",
         "digital_transform.jpg", "2026-11-05", 4, 4, 1, 1),
        ("Workshop Thiết kế UI/UX cho người mới bắt đầu", "Học cách tư duy thiết kế UI/UX từ A-Z qua bài tập thực hành.",
         "workshop_uiux.jpg", "2026-10-18", 4, 1, 0, 1),
        ("Đêm hội âm nhạc dân tộc", "Trình diễn nhạc cụ dân tộc kết hợp phối khí hiện đại.",
         "traditional_music.jpg", "2026-11-20", 2, 2, 0, 1),
    ]
    cur.executemany(
        """INSERT INTO event
           (name, description, banner_image, event_date, category_id, location_id, is_featured, created_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        events,
    )

    conn.commit()
    conn.close()
    print(f"Đã tạo database mẫu tại: {DB_PATH}")
    print(f"- {len(categories)} loại sự kiện")
    print(f"- {len(locations)} địa điểm")
    print(f"- {len(events)} sự kiện")


if __name__ == "__main__":
    init_db()
