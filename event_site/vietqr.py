"""Sinh chuỗi VietQR (chuẩn EMVCo QR của NAPAS) để quét bằng app ngân hàng.

Chuỗi này đem đi render thành ảnh QR bằng thư viện `qrcode`.
"""


def _tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for ch in data.encode("utf-8"):
        crc ^= ch << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def build_vietqr_payload(bank_bin: str, account_no: str, amount=None,
                         description: str = "", account_name: str = "") -> str:
    """Tạo payload VietQR.

    bank_bin  : mã BIN ngân hàng (VD Vietcombank 970436, Techcombank 970407,
                MB Bank 970422, BIDV 970418, ACB 970416, VietinBank 970415)
    account_no: số tài khoản nhận tiền
    amount     : số tiền (VND, số nguyên). None = QR không cố định số tiền
    description: nội dung chuyển khoản (không dấu, ngắn gọn)
    """
    merchant = _tlv("00", "A000000727") + _tlv(
        "01", _tlv("00", bank_bin) + _tlv("01", account_no)
    ) + _tlv("02", "QRIBFTTA")

    payload = _tlv("00", "01")
    payload += _tlv("01", "12" if amount else "11")  # 12 = QR dùng một lần
    payload += _tlv("38", merchant)
    payload += _tlv("53", "704")  # VND
    if amount:
        payload += _tlv("54", str(int(amount)))
    payload += _tlv("58", "VN")
    if account_name:
        payload += _tlv("59", account_name[:25])
    if description:
        payload += _tlv("62", _tlv("08", description[:25]))

    payload += "6304"
    return payload + crc16_ccitt(payload)


def no_accent(text: str) -> str:
    """Bỏ dấu tiếng Việt cho nội dung chuyển khoản."""
    import unicodedata

    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")
