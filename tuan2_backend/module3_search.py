"""
module3_search.py
==================================================
MODULE 3 - Bộ lọc & Tìm kiếm + Trang chủ
Người phụ trách: Người 3
==================================================
Chức năng:
  1. Trang chủ: hiển thị sự kiện nổi bật + sự kiện sắp diễn ra
  2. Tìm kiếm theo từ khóa (tên sự kiện)
  3. Lọc theo: ngày (khoảng from-to), loại sự kiện, địa điểm
  4. Kết hợp tìm kiếm + lọc + phân trang

Được viết dưới dạng Flask Blueprint để nhóm trưởng dễ dàng
"register" (đăng ký) vào app chính (app.py) khi ghép các module lại.
"""
from flask import Blueprint, render_template, request
from datetime import date
from db import get_connection

# Blueprint riêng cho Module 3, url_prefix để tách biệt với module khác
bp_module3 = Blueprint("module3", __name__)

PAGE_SIZE = 6  # số sự kiện hiển thị mỗi trang kết quả tìm kiếm


# ----------------------------------------------------------------------
# 1. TRANG CHỦ
# ----------------------------------------------------------------------
@bp_module3.route("/")
def home():
    conn = get_connection()

    # Sự kiện nổi bật: is_featured = 1, lấy mới nhất trước
    featured_events = conn.execute(
        """SELECT e.*, c.name AS category_name, l.name AS location_name
           FROM event e
           JOIN category c ON e.category_id = c.id
           JOIN location l ON e.location_id = l.id
           WHERE e.is_featured = 1
           ORDER BY e.event_date ASC
           LIMIT 4"""
    ).fetchall()

    # Sự kiện sắp diễn ra: ngày >= hôm nay, sắp xếp gần nhất lên trước
    today_str = date.today().isoformat()
    upcoming_events = conn.execute(
        """SELECT e.*, c.name AS category_name, l.name AS location_name
           FROM event e
           JOIN category c ON e.category_id = c.id
           JOIN location l ON e.location_id = l.id
           WHERE e.event_date >= ?
           ORDER BY e.event_date ASC
           LIMIT 8""",
        (today_str,),
    ).fetchall()

    # Danh mục & địa điểm để đổ vào dropdown của thanh tìm kiếm trên Trang chủ
    categories = conn.execute("SELECT * FROM category ORDER BY name").fetchall()
    locations = conn.execute("SELECT * FROM location ORDER BY name").fetchall()

    conn.close()
    return render_template(
        "home.html",
        featured_events=featured_events,
        upcoming_events=upcoming_events,
        categories=categories,
        locations=locations,
    )


# ----------------------------------------------------------------------
# 2. TÌM KIẾM & LỌC (kết hợp)
# ----------------------------------------------------------------------
def build_search_query(args):
    """
    Xây dựng câu truy vấn SQL động dựa trên các tham số lọc được truyền vào.
    Chỉ thêm điều kiện WHERE nào có giá trị -> tránh lọc "rỗng" làm sai kết quả.
    Trả về (sql_where, params, filters_dict) để dùng lại cho cả query đếm tổng
    và query lấy dữ liệu theo trang.
    """
    conditions = ["1=1"]   # điều kiện luôn đúng, để nối thêm AND cho gọn
    params = []

    keyword = args.get("q", "").strip()
    date_from = args.get("date_from", "").strip()
    date_to = args.get("date_to", "").strip()
    category_id = args.get("category_id", "").strip()
    location_id = args.get("location_id", "").strip()

    if keyword:
        # Tìm theo tên HOẶC mô tả có chứa từ khóa (không phân biệt hoa/thường)
        conditions.append("(e.name LIKE ? OR e.description LIKE ?)")
        like_kw = f"%{keyword}%"
        params.extend([like_kw, like_kw])

    if date_from:
        conditions.append("e.event_date >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("e.event_date <= ?")
        params.append(date_to)

    if category_id:
        conditions.append("e.category_id = ?")
        params.append(category_id)

    if location_id:
        conditions.append("e.location_id = ?")
        params.append(location_id)

    where_sql = " AND ".join(conditions)
    filters = {
        "q": keyword,
        "date_from": date_from,
        "date_to": date_to,
        "category_id": category_id,
        "location_id": location_id,
    }
    return where_sql, params, filters


@bp_module3.route("/search")
def search():
    conn = get_connection()

    where_sql, params, filters = build_search_query(request.args)

    # ---- Đếm tổng số kết quả (để tính tổng số trang) ----
    total_row = conn.execute(
        f"SELECT COUNT(*) AS total FROM event e WHERE {where_sql}", params
    ).fetchone()
    total_results = total_row["total"]

    # ---- Xử lý phân trang ----
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    total_pages = max((total_results + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE

    # ---- Lấy dữ liệu trang hiện tại ----
    results = conn.execute(
        f"""SELECT e.*, c.name AS category_name, l.name AS location_name
            FROM event e
            JOIN category c ON e.category_id = c.id
            JOIN location l ON e.location_id = l.id
            WHERE {where_sql}
            ORDER BY e.event_date ASC
            LIMIT ? OFFSET ?""",
        params + [PAGE_SIZE, offset],
    ).fetchall()

    categories = conn.execute("SELECT * FROM category ORDER BY name").fetchall()
    locations = conn.execute("SELECT * FROM location ORDER BY name").fetchall()
    conn.close()

    return render_template(
        "search.html",
        results=results,
        total_results=total_results,
        page=page,
        total_pages=total_pages,
        filters=filters,
        categories=categories,
        locations=locations,
    )
