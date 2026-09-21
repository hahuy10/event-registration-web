-- ========================================================
-- SCHEMA CSDL - Module 3: Bộ lọc & Tìm kiếm + Trang chủ
-- Các bảng Category, Location, Event dùng CHUNG với Module 2
-- (Người 2 - Quản lý Sự kiện là chủ sở hữu ghi/sửa/xóa dữ liệu này;
--  Module 3 chỉ SELECT/đọc dữ liệu để hiển thị & lọc)
-- ========================================================

CREATE TABLE IF NOT EXISTS category (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS location (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    address  TEXT
);

CREATE TABLE IF NOT EXISTS event (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    description   TEXT,
    banner_image  TEXT,
    event_date    TEXT NOT NULL,        -- format: YYYY-MM-DD
    category_id   INTEGER NOT NULL,
    location_id   INTEGER NOT NULL,
    is_featured   INTEGER DEFAULT 0,    -- 0 = false, 1 = true
    created_by    INTEGER,              -- FK -> user.id (Module 1)
    FOREIGN KEY (category_id) REFERENCES category(id),
    FOREIGN KEY (location_id) REFERENCES location(id)
);

-- Index tăng tốc lọc/tìm kiếm (Tiêu chí tối ưu truy vấn)
CREATE INDEX IF NOT EXISTS idx_event_date       ON event(event_date);
CREATE INDEX IF NOT EXISTS idx_event_category   ON event(category_id);
CREATE INDEX IF NOT EXISTS idx_event_location   ON event(location_id);
CREATE INDEX IF NOT EXISTS idx_event_cat_date    ON event(category_id, event_date);
