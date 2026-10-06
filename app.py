import os
import io
import re
import json
import math
import uuid
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# PDF
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
  st.image("sushi.jpg")


# ============================================================
# 1. CẤU HÌNH CHUNG
# ============================================================

st.set_page_config(
    page_title="N7 Sushi - POS",
    page_icon="🍣",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #fffaf7;
    }

    .main-title {
        color: #9b1c1c;
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0;
    }

    .sub-title {
        color: #555;
        text-align: center;
        font-size: 16px;
        margin-top: 0;
        margin-bottom: 25px;
    }

    .section-title {
        color: #9b1c1c;
        font-size: 25px;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 12px;
    }

    .total-box {
        background: linear-gradient(135deg, #9b1c1c, #d32f2f);
        color: white;
        padding: 22px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }

    .total-number {
        font-size: 34px;
        font-weight: 800;
    }

    .info-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #eee;
        margin-bottom: 10px;
    }

    .chat-user {
        background: #e9f5ff;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
    }

    .chat-bot {
        background: #fff;
        border: 1px solid #eee;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
    }

    div[data-testid="stMetricValue"] {
        color: #9b1c1c;
    }

    .small-note {
        color: #777;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. THÔNG TIN N7 SUSHI
# ============================================================
#
# QUAN TRỌNG:
# Các thông tin bên dưới là dữ liệu MẪU để app chạy ngay.
# Bạn hãy thay bằng menu / địa chỉ / khuyến mãi thật của N7 Sushi.
#
# Không nên để chatbot tự bịa thông tin nhà hàng.
# Chatbot được cung cấp KNOWLEDGE_BASE bên dưới làm nguồn dữ liệu.
# ============================================================

RESTAURANT = {
    "name": "N7 Sushi",
    "phone": "0900 000 000",
    "address": "Địa chỉ N7 Sushi - Vui lòng cập nhật địa chỉ thật",
    "opening_hours": "10:00 - 22:00 hàng ngày",
    "facebook": "https://facebook.com/",
    "website": "",
}


# ============================================================
# 4. MENU
# ============================================================
#
# Bạn thay / thêm món tại đây.
#
# category:
# - "Món ăn"
# - "Nước uống"
# - "Combo"
#
# bestseller=True để chatbot biết đây là best seller.
# ============================================================

MENU = [
    # -------------------------
    # SUSHI / MÓN ĂN
    # -------------------------
    {
        "code": "S01",
        "name": "Sushi cá hồi",
        "category": "Món ăn",
        "price": 69000,
        "bestseller": True,
        "description": "Sushi cá hồi tươi",
    },
    {
        "code": "S02",
        "name": "Sushi cá ngừ",
        "category": "Món ăn",
        "price": 65000,
        "bestseller": True,
        "description": "Sushi cá ngừ",
    },
    {
        "code": "S03",
        "name": "Sashimi cá hồi",
        "category": "Món ăn",
        "price": 129000,
        "bestseller": True,
        "description": "Sashimi cá hồi tươi",
    },
    {
        "code": "S04",
        "name": "Sashimi tổng hợp",
        "category": "Món ăn",
        "price": 229000,
        "bestseller": True,
        "description": "Sashimi tổng hợp nhiều loại",
    },
    {
        "code": "S05",
        "name": "Maki cá hồi bơ",
        "category": "Món ăn",
        "price": 89000,
        "bestseller": True,
        "description": "Maki cá hồi và bơ",
    },
    {
        "code": "S06",
        "name": "Maki tempura tôm",
        "category": "Món ăn",
        "price": 99000,
        "bestseller": False,
        "description": "Maki tôm tempura",
    },
    {
        "code": "S07",
        "name": "Salmon Aburi",
        "category": "Món ăn",
        "price": 109000,
        "bestseller": True,
        "description": "Cá hồi áp lửa",
    },
    {
        "code": "S08",
        "name": "Unagi Sushi",
        "category": "Món ăn",
        "price": 119000,
        "bestseller": False,
        "description": "Sushi lươn Nhật",
    },
    {
        "code": "S09",
        "name": "Gyoza",
        "category": "Món ăn",
        "price": 79000,
        "bestseller": False,
        "description": "Bánh xếp Nhật",
    },
    {
        "code": "S10",
        "name": "Edamame",
        "category": "Món ăn",
        "price": 49000,
        "bestseller": False,
        "description": "Đậu nành Nhật",
    },

    # -------------------------
    # COMBO
    # -------------------------
    {
        "code": "C02",
        "name": "Combo N7 Couple - 2 người",
        "category": "Combo",
        "price": 299000,
        "bestseller": True,
        "description": "Combo dành cho 2 người",
    },
    {
        "code": "C03",
        "name": "Combo N7 Family - 3 người",
        "category": "Combo",
        "price": 429000,
        "bestseller": True,
        "description": "Combo dành cho 3 người",
    },
    {
        "code": "C45",
        "name": "Combo N7 Party - 4-5 người",
        "category": "Combo",
        "price": 649000,
        "bestseller": True,
        "description": "Combo dành cho 4-5 người",
    },

    # -------------------------
    # NƯỚC UỐNG
    # -------------------------
    {
        "code": "D01",
        "name": "Coca-Cola",
        "category": "Nước uống",
        "price": 25000,
        "bestseller": False,
        "description": "Nước ngọt",
    },
    {
        "code": "D02",
        "name": "Sprite",
        "category": "Nước uống",
        "price": 25000,
        "bestseller": False,
        "description": "Nước ngọt",
    },
    {
        "code": "D03",
        "name": "Trà đào",
        "category": "Nước uống",
        "price": 45000,
        "bestseller": True,
        "description": "Trà đào",
    },
    {
        "code": "D04",
        "name": "Trà xanh Nhật",
        "category": "Nước uống",
        "price": 35000,
        "bestseller": False,
        "description": "Trà xanh Nhật",
    },
]

MENU_DF = pd.DataFrame(MENU)

MENU_LOOKUP = {
    item["name"]: item
    for item in MENU
}


# ============================================================
# 5. VOUCHER
# ============================================================
#
# type:
# - percent
# - fixed
#
# Ví dụ:
# N7WELCOME = giảm 10%
# N7SAVE50 = giảm 50.000đ
# ============================================================

VOUCHERS = {
    "N7WELCOME": {
        "type": "percent",
        "value": 10,
        "max_discount": 100000,
        "min_order": 200000,
        "description": "Giảm 10%, tối đa 100.000đ cho đơn từ 200.000đ",
    },
    "N7SAVE50": {
        "type": "fixed",
        "value": 50000,
        "max_discount": 50000,
        "min_order": 300000,
        "description": "Giảm 50.000đ cho đơn từ 300.000đ",
    },
    "N7VIP": {
        "type": "percent",
        "value": 15,
        "max_discount": 150000,
        "min_order": 500000,
        "description": "Giảm 15%, tối đa 150.000đ cho đơn từ 500.000đ",
    },
}


# ============================================================
# 6. KHUYẾN MÃI / COMBO CHO CHATBOT
# ============================================================

PROMOTIONS = [
    "Combo N7 Couple dành cho 2 người.",
    "Combo N7 Family dành cho 3 người.",
    "Combo N7 Party dành cho 4-5 người.",
    "Khách có thể nhập voucher trực tiếp tại màn hình thanh toán.",
    "Chương trình khuyến mãi cần được cập nhật trong biến PROMOTIONS trước khi đưa app vào sử dụng thực tế.",
]


# ============================================================
# 7. KNOWLEDGE BASE CHO CHATBOT
# ============================================================

def build_knowledge_base():
    bestseller = [
        item
        for item in MENU
        if item.get("bestseller", False)
    ]

    best_text = "\n".join(
        [
            f"- {x['name']}: {format_currency(x['price'])}"
            for x in bestseller
        ]
    )

    combo_text = "\n".join(
        [
            f"- {x['name']}: {format_currency(x['price'])} - {x['description']}"
            for x in MENU
            if x["category"] == "Combo"
        ]
    )

    menu_text = "\n".join(
        [
            f"- {x['name']} ({x['category']}): "
            f"{format_currency(x['price'])}. {x['description']}"
            for x in MENU
        ]
    )

    promo_text = "\n".join(
        [f"- {x}" for x in PROMOTIONS]
    )

    return f"""
THÔNG TIN NHÀ HÀNG:
Tên: {RESTAURANT['name']}
Địa chỉ: {RESTAURANT['address']}
Điện thoại: {RESTAURANT['phone']}
Giờ mở cửa: {RESTAURANT['opening_hours']}
Facebook: {RESTAURANT['facebook']}

BEST SELLER:
{best_text}

COMBO:
{combo_text}

KHUYẾN MÃI:
{promo_text}

MENU:
{menu_text}

VOUCHER:
{json.dumps(VOUCHERS, ensure_ascii=False, indent=2)}

QUY TẮC:
- Chỉ trả lời dựa trên dữ liệu được cung cấp.
- Nếu không có thông tin, nói rõ là chưa có thông tin.
- Không tự bịa giá, địa chỉ, giờ mở cửa hoặc chương trình khuyến mãi.
- Có thể tư vấn combo dựa trên số người khách hỏi.
"""


# ============================================================
# 8. HÀM TIỆN ÍCH
# ============================================================

def format_currency(value):
    try:
        value = float(value)
    except Exception:
        value = 0

    return f"{value:,.0f} ₫".replace(",", ".")


def parse_phone(phone):
    phone = re.sub(r"\D", "", str(phone))
    return phone


def generate_invoice_number():
    now = datetime.now()
    return f"N7-{now.strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"


def calculate_voucher(subtotal, voucher_code):
    voucher_code = str(voucher_code or "").strip().upper()

    if not voucher_code:
        return 0, "Không sử dụng voucher"

    if voucher_code not in VOUCHERS:
        return 0, f"Voucher {voucher_code} không tồn tại"

    voucher = VOUCHERS[voucher_code]

    if subtotal < voucher["min_order"]:
        return (
            0,
            f"Voucher {voucher_code} yêu cầu đơn tối thiểu "
            f"{format_currency(voucher['min_order'])}",
        )

    if voucher["type"] == "percent":
        discount = subtotal * voucher["value"] / 100
    else:
        discount = voucher["value"]

    if voucher.get("max_discount"):
        discount = min(discount, voucher["max_discount"])

    discount = min(discount, subtotal)

    return discount, (
        f"Đã áp dụng voucher {voucher_code}: "
        f"-{format_currency(discount)}"
    )


def calculate_points(total):
    """
    Quy tắc mặc định:
    10.000đ = 1 điểm.
    Có thể thay đổi tại đây.
    """
    return int(total // 10000)


# ============================================================
# 9. PDF HÓA ĐƠN
# ============================================================

def find_vietnamese_font():
    """
    Tìm DejaVu Sans trên một số hệ thống phổ biến.
    """

    possible_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def create_pdf_invoice(
    invoice_number,
    table_number,
    customer_name,
    phone,
    order_items,
    subtotal,
    discount,
    total,
    voucher_code,
    points,
):
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()

    font_path = find_vietnamese_font()

    if font_path:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            pdfmetrics.registerFont(
                TTFont("N7Font", font_path)
            )
            base_font = "N7Font"
        except Exception:
            base_font = "Helvetica"
    else:
        base_font = "Helvetica"

    title_style = ParagraphStyle(
        "N7Title",
        parent=styles["Title"],
        fontName=base_font,
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#9b1c1c"),
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "N7Normal",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=9,
        leading=13,
    )

    right_style = ParagraphStyle(
        "N7Right",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    elements = []

    elements.append(
        Paragraph(
            "N7 SUSHI",
            title_style,
        )
    )

    elements.append(
        Paragraph(
            f"{RESTAURANT['address']}<br/>"
            f"Điện thoại: {RESTAURANT['phone']}<br/>"
            f"Giờ mở cửa: {RESTAURANT['opening_hours']}",
            normal_style,
        )
    )

    elements.append(Spacer(1, 6 * mm))

    elements.append(
        Paragraph(
            f"<b>HÓA ĐƠN THANH TOÁN</b><br/>"
            f"Mã hóa đơn: {invoice_number}<br/>"
            f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>"
            f"Bàn: {table_number}<br/>"
            f"Khách hàng: {customer_name}<br/>"
            f"SĐT: {phone or '---'}",
            normal_style,
        )
    )

    elements.append(Spacer(1, 5 * mm))

    data = [
        [
            Paragraph("<b>Món</b>", normal_style),
            Paragraph("<b>SL</b>", normal_style),
            Paragraph("<b>Đơn giá</b>", normal_style),
            Paragraph("<b>Thành tiền</b>", normal_style),
        ]
    ]

    for item in order_items:
        data.append(
            [
                Paragraph(
                    f"{item['name']}<br/>"
                    f"<font size='7'>{item['note']}</font>",
                    normal_style,
                ),
                str(item["quantity"]),
                format_currency(item["price"]),
                format_currency(item["line_total"]),
            ]
        )

    table = Table(
        data,
        colWidths=[
            90 * mm,
            15 * mm,
            32 * mm,
            38 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#9b1c1c"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    base_font,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#fff7f4"),
                    ],
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 6 * mm))

    summary = [
        [
            Paragraph("Tạm tính", normal_style),
            Paragraph(format_currency(subtotal), right_style),
        ],
        [
            Paragraph(
                f"Voucher {voucher_code or ''}",
                normal_style,
            ),
            Paragraph(
                f"- {format_currency(discount)}",
                right_style,
            ),
        ],
        [
            Paragraph("<b>TỔNG THANH TOÁN</b>", normal_style),
            Paragraph(
                f"<b>{format_currency(total)}</b>",
                right_style,
            ),
        ],
        [
            Paragraph("Điểm tích lũy", normal_style),
            Paragraph(str(points), right_style),
        ],
    ]

    summary_table = Table(
        summary,
        colWidths=[120 * mm, 55 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    base_font,
                ),
                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    1,
                    colors.HexColor("#9b1c1c"),
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    elements.append(summary_table)

    elements.append(Spacer(1, 10 * mm))

    elements.append(
        Paragraph(
            "Cảm ơn quý khách đã ghé N7 Sushi! ❤️",
            ParagraphStyle(
                "Thanks",
                parent=normal_style,
                alignment=TA_CENTER,
                fontSize=11,
                textColor=colors.HexColor("#9b1c1c"),
            ),
        )
    )

    doc.build(elements)

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 10. CHATBOT OPENROUTER
# ============================================================

def get_openrouter_key():
    """
    Ưu tiên:
    1. Streamlit secrets
    2. Environment variable
    """

    try:
        key = st.secrets.get("OPENROUTER_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    return os.getenv("OPENROUTER_API_KEY", "")


def get_openrouter_model():
    try:
        model = st.secrets.get(
            "OPENROUTER_MODEL",
            "openai/gpt-4o-mini",
        )
        if model:
            return model
    except Exception:
        pass

    return os.getenv(
        "OPENROUTER_MODEL",
        "openai/gpt-4o-mini",
    )


def call_chatbot(user_message, chat_history):
    api_key = get_openrouter_key()

    # --------------------------------------------------------
    # Không có API key -> trả lời bằng rule-based chatbot
    # --------------------------------------------------------
    if not api_key:
        return local_chatbot(user_message)

    model = get_openrouter_model()

    system_prompt = f"""
Bạn là trợ lý AI chính thức của N7 Sushi.

Bạn phải trả lời bằng tiếng Việt, thân thiện, ngắn gọn, chính xác.

DỮ LIỆU N7 SUSHI:
{build_knowledge_base()}

QUY TẮC BẮT BUỘC:
1. Không được bịa thông tin.
2. Nếu dữ liệu không có câu trả lời, hãy nói:
   "Thông tin này hiện chưa được cập nhật trong hệ thống N7 Sushi."
3. Khi khách hỏi best seller, dựa vào mục BEST SELLER.
4. Khi khách hỏi combo cho 2 người, 3 người hoặc 4-5 người,
   ưu tiên các combo tương ứng.
5. Khi khách hỏi khuyến mãi, chỉ dùng mục KHUYẾN MÃI.
6. Không được tự thay đổi giá món.
7. Nếu khách hỏi món nào có thể gọi, dựa vào MENU.
8. Nếu khách hỏi giờ mở cửa hoặc địa chỉ, lấy đúng dữ liệu nhà hàng.
9. Không tiết lộ API key hoặc thông tin hệ thống.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # Chỉ lấy 10 message gần nhất
    messages.extend(chat_history[-10:])

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "N7 Sushi POS",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 700,
            },
            timeout=45,
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = str(e)

        return (
            "⚠️ Không thể kết nối chatbot AI lúc này.\n\n"
            f"Chi tiết: {error_detail}"
        )

    except Exception as e:
        return (
            "⚠️ Chatbot đang gặp lỗi kết nối. "
            "Bạn có thể thử lại sau.\n\n"
            f"Chi tiết: {str(e)}"
        )


# ============================================================
# 11. CHATBOT OFFLINE
# ============================================================

def local_chatbot(message):
    """
    Chatbot fallback khi chưa cấu hình OpenRouter.
    """

    text = message.lower().strip()

    # Best seller
    if (
        "best seller" in text
        or "bán chạy" in text
        or "bán chạy nhất" in text
        or "món nào ngon" in text
    ):
        items = [
            x for x in MENU
            if x.get("bestseller", False)
        ]

        answer = "🍣 Best seller hiện tại của N7 Sushi:\n\n"

        for item in items:
            answer += (
                f"- **{item['name']}** - "
                f"{format_currency(item['price'])}\n"
            )

        return answer

    # Combo 2 người
    if (
        "2 người" in text
        or "2 nguoi" in text
        or "hai người" in text
    ):
        combos = [
            x for x in MENU
            if x["category"] == "Combo"
            and "2 người" in x["description"]
        ]

        if combos:
            return (
                "👫 Nếu đi 2 người, bạn có thể chọn:\n\n"
                + "\n".join(
                    [
                        f"- **{x['name']}**: "
                        f"{format_currency(x['price'])}"
                        for x in combos
                    ]
                )
            )

    # Combo 3 người
    if (
        "3 người" in text
        or "3 nguoi" in text
        or "ba người" in text
    ):
        combos = [
            x for x in MENU
            if x["category"] == "Combo"
            and "3 người" in x["description"]
        ]

        if combos:
            return (
                "👨‍👩‍👧 Nếu đi 3 người, bạn có thể chọn:\n\n"
                + "\n".join(
                    [
                        f"- **{x['name']}**: "
                        f"{format_currency(x['price'])}"
                        for x in combos
                    ]
                )
            )

    # Combo 4-5 người
    if (
        "4-5" in text
        or "4 5" in text
        or "4 người" in text
        or "5 người" in text
        or "4 nguoi" in text
        or "5 nguoi" in text
    ):
        combos = [
            x for x in MENU
            if x["category"] == "Combo"
            and "4-5 người" in x["description"]
        ]

        if combos:
            return (
                "👨‍👩‍👧‍👦 Nếu đi 4-5 người, bạn có thể chọn:\n\n"
                + "\n".join(
                    [
                        f"- **{x['name']}**: "
                        f"{format_currency(x['price'])}"
                        for x in combos
                    ]
                )
            )

    # Khuyến mãi
    if (
        "khuyến mãi" in text
        or "khuyen mai" in text
        or "promotion" in text
        or "ưu đãi" in text
        or "voucher" in text
    ):
        return (
            "🎁 Thông tin khuyến mãi hiện tại:\n\n"
            + "\n".join(
                [f"- {x}" for x in PROMOTIONS]
            )
            + "\n\nBạn cũng có thể nhập mã voucher ở phần thanh toán."
        )

    # Địa chỉ
    if (
        "địa chỉ" in text
        or "dia chi" in text
        or "ở đâu" in text
        or "o dau" in text
    ):
        return (
            f"📍 Địa chỉ N7 Sushi:\n\n"
            f"{RESTAURANT['address']}"
        )

    # Giờ mở cửa
    if (
        "giờ mở cửa" in text
        or "gio mo cua" in text
        or "mấy giờ mở" in text
        or "may gio mo" in text
    ):
        return (
            f"🕐 N7 Sushi mở cửa:\n\n"
            f"{RESTAURANT['opening_hours']}"
        )

    # Số điện thoại
    if (
        "số điện thoại" in text
        or "so dien thoai" in text
        or "phone" in text
        or "hotline" in text
    ):
        return (
            f"☎️ Hotline N7 Sushi: "
            f"{RESTAURANT['phone']}"
        )

    # Menu
    if (
        "menu" in text
        or "thực đơn" in text
        or "thuc don" in text
        or "món ăn" in text
    ):
        return (
            "🍣 Một số món trong menu N7 Sushi:\n\n"
            + "\n".join(
                [
                    f"- {x['name']}: "
                    f"{format_currency(x['price'])}"
                    for x in MENU[:15]
                ]
            )
        )

    return (
        "Xin chào! 👋 Mình là trợ lý N7 Sushi.\n\n"
        "Bạn có thể hỏi mình:\n"
        "- 🍣 Best seller là gì?\n"
        "- 👫 Combo cho 2 người?\n"
        "- 👨‍👩‍👧 Combo cho 3 người?\n"
        "- 👨‍👩‍👧‍👦 Combo cho 4-5 người?\n"
        "- 🎁 Đang có khuyến mãi gì?\n"
        "- 📍 Địa chỉ quán?\n"
        "- 🕐 Giờ mở cửa?\n"
        "- 🍱 Menu có món gì?"
    )


# ============================================================
# 12. SESSION STATE
# ============================================================

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "invoice_data" not in st.session_state:
    st.session_state.invoice_data = None

if "last_invoice_pdf" not in st.session_state:
    st.session_state.last_invoice_pdf = None

if "last_invoice_number" not in st.session_state:
    st.session_state.last_invoice_number = None


# ============================================================
# 13. HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🍣 N7 SUSHI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-title">'
    "POS Order & Customer Assistant"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# 14. SIDEBAR - CHATBOT
# ============================================================

with st.sidebar:

    st.markdown("## 🤖 N7 Sushi Assistant")

    api_key_exists = bool(get_openrouter_key())

    if api_key_exists:
        st.success("AI Chatbot: Đã kết nối")
    else:
        st.info(
            "AI Chatbot: Chế độ offline\n\n"
            "Cấu hình OPENROUTER_API_KEY để bật AI."
        )

    st.markdown("---")

    # Hiển thị chat history
    for msg in st.session_state.chat_messages:

        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="chat-user">
                    <b>👤 Bạn</b><br/>
                    {msg["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f"""
                <div class="chat-bot">
                    <b>🤖 N7 Sushi</b><br/>
                    {msg["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

    chat_input = st.chat_input(
        "Hỏi N7 Sushi..."
    )

    if chat_input:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": chat_input,
            }
        )

        history_for_api = [
            {
                "role": x["role"],
                "content": x["content"],
            }
            for x in st.session_state.chat_messages
        ]

        answer = call_chatbot(
            chat_input,
            history_for_api[:-1],
        )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()

    if st.button(
        "🗑️ Xóa hội thoại",
        use_container_width=True,
    ):
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown("---")

    st.caption(
        "Chatbot được thiết kế để trả lời dựa trên "
        "thông tin/menu được cấu hình trong app.py."
    )


# ============================================================
# 15. TAB
# ============================================================

tab_order, tab_menu, tab_invoice, tab_info = st.tabs(
    [
        "🧾 Tạo hóa đơn",
        "🍣 Menu",
        "📄 Hóa đơn gần nhất",
        "ℹ️ Thông tin N7 Sushi",
    ]
)


# ============================================================
# 16. TAB TẠO HÓA ĐƠN
# ============================================================

with tab_order:

    st.markdown(
        '<div class="section-title">Thông tin khách hàng</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        table_number = st.text_input(
            "🪑 Số bàn",
            placeholder="Ví dụ: B12",
        )

    with col2:
        customer_name = st.text_input(
            "👤 Tên khách hàng",
            placeholder="Nguyễn Văn A",
        )

    with col3:
        phone = st.text_input(
            "📱 Số điện thoại tích điểm",
            placeholder="0901234567",
        )

    st.markdown(
        '<div class="section-title">Chọn món</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Một khách có thể chọn nhiều món khác nhau. "
        "Nhập số lượng và ghi chú riêng cho từng món."
    )

    # --------------------------------------------------------
    # Tạo 15 dòng order
    # --------------------------------------------------------

    item_options = ["-- Chọn món --"] + [
        x["name"] for x in MENU
    ]

    default_rows = pd.DataFrame(
        [
            {
                "Món": "-- Chọn món --",
                "Số lượng": 0,
                "Ghi chú": "",
            }
            for _ in range(15)
        ]
    )

    edited_order = st.data_editor(
        default_rows,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        key="order_editor",
        column_config={
            "Món": st.column_config.SelectboxColumn(
                "🍣 Món",
                options=item_options,
                required=False,
                width="large",
            ),
            "Số lượng": st.column_config.NumberColumn(
                "🔢 Số lượng",
                min_value=0,
                max_value=100,
                step=1,
                format="%d",
                width="small",
            ),
            "Ghi chú": st.column_config.TextColumn(
                "📝 Ghi chú",
                width="large",
            ),
        },
    )

    # --------------------------------------------------------
    # Voucher
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Voucher & Thanh toán</div>',
        unsafe_allow_html=True,
    )

    voucher_col1, voucher_col2 = st.columns(
        [2, 3]
    )

    with voucher_col1:
        voucher_code = st.text_input(
            "🎟️ Mã voucher",
            placeholder="Ví dụ: N7WELCOME",
        )

    with voucher_col2:
        st.info(
            "Voucher mẫu: "
            + ", ".join(VOUCHERS.keys())
        )

    # --------------------------------------------------------
    # Xử lý order
    # --------------------------------------------------------

    order_items = []

    for _, row in edited_order.iterrows():

        item_name = row["Món"]
        quantity = row["Số lượng"]

        if (
            pd.isna(item_name)
            or item_name == "-- Chọn món --"
        ):
            continue

        try:
            quantity = int(quantity)
        except Exception:
            quantity = 0

        if quantity <= 0:
            continue

        item = MENU_LOOKUP.get(item_name)

        if not item:
            continue

        note = row["Ghi chú"]

        if pd.isna(note):
            note = ""

        line_total = item["price"] * quantity

        order_items.append(
            {
                "code": item["code"],
                "name": item["name"],
                "category": item["category"],
                "price": item["price"],
                "quantity": quantity,
                "note": str(note),
                "line_total": line_total,
            }
        )

    subtotal = sum(
        x["line_total"]
        for x in order_items
    )

    discount, voucher_message = calculate_voucher(
        subtotal,
        voucher_code,
    )

    total = max(
        0,
        subtotal - discount,
    )

    points = calculate_points(total)

    # --------------------------------------------------------
    # Hiển thị kết quả
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Kiểm tra đơn hàng</div>',
        unsafe_allow_html=True,
    )

    if order_items:

        result_df = pd.DataFrame(
            [
                {
                    "Món": x["name"],
                    "Loại": x["category"],
                    "Số lượng": x["quantity"],
                    "Đơn giá": format_currency(x["price"]),
                    "Ghi chú": x["note"],
                    "Thành tiền": format_currency(
                        x["line_total"]
                    ),
                }
                for x in order_items
            ]
        )

        st.dataframe(
            result_df,
            width="stretch",
            hide_index=True,
        )

    else:
        st.warning(
            "Chưa có món nào trong đơn hàng."
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.metric(
            "Tạm tính",
            format_currency(subtotal),
        )

    with col_b:
        st.metric(
            "Giảm voucher",
            format_currency(discount),
        )

    with col_c:
        st.metric(
            "Điểm tích lũy",
            f"+{points}",
        )

    with col_d:
        st.markdown(
            f"""
            <div class="total-box">
                <div>TỔNG THANH TOÁN</div>
                <div class="total-number">
                    {format_currency(total)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if voucher_message:
        if discount > 0:
            st.success(voucher_message)
        elif voucher_code:
            st.warning(voucher_message)

    st.markdown("---")

    # --------------------------------------------------------
    # Thanh toán
    # --------------------------------------------------------

    payment_col1, payment_col2 = st.columns(
        [2, 1]
    )

    with payment_col1:
        st.markdown(
            f"""
            **Bàn:** {table_number or "---"}  
            **Khách hàng:** {customer_name or "---"}  
            **SĐT:** {phone or "---"}  
            **Số món:** {len(order_items)} loại  
            **Tổng số lượng:** {sum(x["quantity"] for x in order_items)}
            """
        )

    with payment_col2:

        pay_clicked = st.button(
            "💳 THANH TOÁN & XUẤT HÓA ĐƠN",
            type="primary",
            use_container_width=True,
        )

        if pay_clicked:

            errors = []

            if not table_number.strip():
                errors.append(
                    "Vui lòng nhập số bàn."
                )

            if not customer_name.strip():
                errors.append(
                    "Vui lòng nhập tên khách hàng."
                )

            if not order_items:
                errors.append(
                    "Vui lòng chọn ít nhất một món."
                )

            if errors:

                for error in errors:
                    st.error(error)

            else:

                clean_phone = parse_phone(phone)

                invoice_number = generate_invoice_number()

                invoice_data = {
                    "invoice_number": invoice_number,
                    "created_at": datetime.now(),
                    "table_number": table_number,
                    "customer_name": customer_name,
                    "phone": clean_phone,
                    "items": order_items,
                    "subtotal": subtotal,
                    "discount": discount,
                    "total": total,
                    "voucher_code": voucher_code.upper().strip(),
                    "points": points,
                }

                st.session_state.invoice_data = invoice_data
                st.session_state.last_invoice_number = (
                    invoice_number
                )

                if REPORTLAB_AVAILABLE:

                    pdf_bytes = create_pdf_invoice(
                        invoice_number=invoice_number,
                        table_number=table_number,
                        customer_name=customer_name,
                        phone=clean_phone,
                        order_items=order_items,
                        subtotal=subtotal,
                        discount=discount,
                        total=total,
                        voucher_code=voucher_code,
                        points=points,
                    )

                    st.session_state.last_invoice_pdf = pdf_bytes

                else:
                    st.session_state.last_invoice_pdf = None

                st.success(
                    f"✅ Thanh toán thành công! "
                    f"Mã hóa đơn: {invoice_number}"
                )

                st.balloons()


# ============================================================
# 17. TAB MENU
# ============================================================

with tab_menu:

    st.markdown(
        '<div class="section-title">🍣 Menu N7 Sushi</div>',
        unsafe_allow_html=True,
    )

    category_filter = st.selectbox(
        "Lọc theo danh mục",
        [
            "Tất cả",
            "Món ăn",
            "Combo",
            "Nước uống",
        ],
    )

    search_menu = st.text_input(
        "🔎 Tìm món",
        placeholder="Nhập tên món...",
    )

    menu_display = MENU_DF.copy()

    if category_filter != "Tất cả":
        menu_display = menu_display[
            menu_display["category"]
            == category_filter
        ]

    if search_menu.strip():
        keyword = search_menu.lower().strip()

        menu_display = menu_display[
            menu_display["name"]
            .str.lower()
            .str.contains(keyword, na=False)
        ]

    display_rows = []

    for _, row in menu_display.iterrows():

        display_rows.append(
            {
                "Mã": row["code"],
                "Món": row["name"],
                "Loại": row["category"],
                "Giá": format_currency(row["price"]),
                "⭐": "Best seller"
                if row["bestseller"]
                else "",
                "Mô tả": row["description"],
            }
        )

    st.dataframe(
        pd.DataFrame(display_rows),
        width="stretch",
        hide_index=True,
    )


# ============================================================
# 18. TAB HÓA ĐƠN GẦN NHẤT
# ============================================================

with tab_invoice:

    st.markdown(
        '<div class="section-title">📄 Hóa đơn gần nhất</div>',
        unsafe_allow_html=True,
    )

    invoice = st.session_state.invoice_data

    if not invoice:

        st.info(
            "Chưa có hóa đơn nào. "
            "Hãy tạo đơn hàng và bấm Thanh toán."
        )

    else:

        st.success(
            f"Hóa đơn {invoice['invoice_number']}"
        )

        st.markdown(
            f"""
            <div class="info-card">
            <b>Mã hóa đơn:</b> {invoice['invoice_number']}<br/>
            <b>Thời gian:</b> {invoice['created_at'].strftime('%d/%m/%Y %H:%M:%S')}<br/>
            <b>Bàn:</b> {invoice['table_number']}<br/>
            <b>Khách hàng:</b> {invoice['customer_name']}<br/>
            <b>SĐT:</b> {invoice['phone'] or '---'}
            </div>
            """,
            unsafe_allow_html=True,
        )

        invoice_display = pd.DataFrame(
            [
                {
                    "Món": x["name"],
                    "Số lượng": x["quantity"],
                    "Đơn giá": format_currency(
                        x["price"]
                    ),
                    "Ghi chú": x["note"],
                    "Thành tiền": format_currency(
                        x["line_total"]
                    ),
                }
                for x in invoice["items"]
            ]
        )

        st.dataframe(
            invoice_display,
            width="stretch",
            hide_index=True,
        )

        st.markdown(
            f"""
            ### Tổng kết

            **Tạm tính:** {format_currency(invoice['subtotal'])}

            **Voucher:** {invoice['voucher_code'] or 'Không có'}

            **Giảm:** {format_currency(invoice['discount'])}

            **TỔNG THANH TOÁN:** **{format_currency(invoice['total'])}**

            **Điểm tích lũy:** +{invoice['points']} điểm
            """
        )

        if st.session_state.last_invoice_pdf:

            st.download_button(
                label="📥 TẢI HÓA ĐƠN PDF",
                data=st.session_state.last_invoice_pdf,
                file_name=(
                    f"{invoice['invoice_number']}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )

        else:

            st.warning(
                "Chưa cài thư viện ReportLab nên chưa thể "
                "xuất PDF. Hãy chạy: pip install reportlab"
            )


# ============================================================
# 19. TAB THÔNG TIN
# ============================================================

with tab_info:

    st.markdown(
        '<div class="section-title">ℹ️ N7 Sushi</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            f"""
            <div class="info-card">
                <h3>🍣 {RESTAURANT['name']}</h3>
                <b>📍 Địa chỉ</b><br/>
                {RESTAURANT['address']}<br/><br/>

                <b>☎️ Điện thoại</b><br/>
                {RESTAURANT['phone']}<br/><br/>

                <b>🕐 Giờ mở cửa</b><br/>
                {RESTAURANT['opening_hours']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            """
            <div class="info-card">
                <h3>⭐ Best Seller</h3>
            """,
            unsafe_allow_html=True,
        )

        for item in MENU:

            if item["bestseller"]:

                st.write(
                    f"🍣 **{item['name']}** — "
                    f"{format_currency(item['price'])}"
                )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🎁 Các voucher hiện có")

    for code, voucher in VOUCHERS.items():

        st.markdown(
            f"""
            <div class="info-card">
                <b>🎟️ {code}</b><br/>
                {voucher['description']}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 20. FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "N7 Sushi POS • Order • Voucher • Loyalty • Invoice • AI Assistant"
)
