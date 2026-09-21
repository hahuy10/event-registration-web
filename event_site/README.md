# Website đăng ký sự kiện (Flask)

## Chạy thử

```bash
cd event_site
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Mở http://127.0.0.1:5000. Lần chạy đầu tự tạo `events.db` và 3 sự kiện mẫu.

Trang quản lý: http://127.0.0.1:5000/admin — tài khoản `admin` / `admin123`.

## Cấu trúc

```
app.py                  route, model, logic đăng ký & thanh toán
vietqr.py               sinh chuỗi VietQR chuẩn EMVCo (có CRC16)
templates/              giao diện Jinja
static/css/style.css    toàn bộ CSS
static/uploads/         banner tải lên
events.db               SQLite, tự tạo khi chạy
```

## Luồng của người tham gia

1. Trang chủ → chọn sự kiện → **Đăng ký**, điền họ tên/email/số lượng.
2. Sự kiện miễn phí: vé phát hành ngay.
   Sự kiện có phí: chuyển sang trang thanh toán, hệ thống sinh mã `DKxxxxxx`.
3. Trang thanh toán hiện **mã QR VietQR** đã gắn sẵn số tài khoản, số tiền và nội dung
   chuyển khoản. Quét bằng bất kỳ app ngân hàng nào tại Việt Nam.
4. Sau khi ghi nhận thanh toán, hệ thống cấp số hoá đơn `HDyyyymm-0001` và mở trang
   **hoá đơn kèm vé điện tử** (có QR check-in, in được bằng nút "In hoá đơn").
5. Mất link? Vào **Tra cứu vé**, nhập mã đăng ký.

## Luồng của ban tổ chức

- Thêm / sửa / xoá sự kiện, upload banner (PNG, JPG, WEBP, GIF ≤ 8MB), đặt số chỗ và giá vé.
- Ẩn sự kiện khỏi trang công khai bằng cách bỏ chọn "Mở đăng ký công khai".
- Xoá sự kiện sẽ xoá kèm toàn bộ đăng ký của sự kiện đó và file banner.
- Danh sách đăng ký lọc theo trạng thái, xác nhận đã thu tiền thủ công, huỷ, xoá, tải CSV.

## Cần đổi trước khi chạy thật

| Chỗ cần sửa | Nằm ở |
|---|---|
| Số tài khoản, BIN ngân hàng, tên chủ tài khoản | `PAYEE` trong `app.py` |
| Tên công ty, MST, địa chỉ trên hoá đơn | `ORG` trong `app.py` |
| Tài khoản quản trị | biến môi trường `ADMIN_USER`, `ADMIN_PASSWORD` |
| `SECRET_KEY` | biến môi trường `SECRET_KEY` |

Mã BIN một số ngân hàng: Vietcombank 970436, VietinBank 970415, BIDV 970418,
Techcombank 970407, MB Bank 970422, ACB 970416, TPBank 970423, VPBank 970432.

## Nối cổng thanh toán thật

Hiện nút "Tôi đã chuyển khoản" xác nhận ngay để bạn thử luồng. Khi tích hợp thật
(VNPAY, MoMo, hoặc dịch vụ đối soát biến động số dư như Casso, SePay), viết một route
webhook nhận thông báo từ họ, đối chiếu số tiền và nội dung `SK <mã đăng ký>`, rồi gọi:

```python
mark_paid(reg)   # đã có sẵn trong app.py, tự cấp số hoá đơn
```

Nhớ kiểm tra chữ ký của webhook và chặn route `confirm_payment` ở bản thật.

## Gợi ý mở rộng

- Gửi email xác nhận bằng Flask-Mail kèm link hoá đơn.
- Xuất hoá đơn PDF bằng WeasyPrint thay cho lệnh in của trình duyệt.
- Hết hạn giữ chỗ: xoá đăng ký `pending` quá 30 phút bằng APScheduler.
- Trang check-in quét QR vé để điểm danh tại cửa.
