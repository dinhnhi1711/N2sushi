import os
import io
import uuid
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ============================================================
# PDF
# ============================================================

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


# ============================================================
# CẤU HÌNH STREAMLIT
# ============================================================

st.set_page_config(
    page_title="N2 Sushi",
    page_icon="🍣",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #fffaf7;
    }

    .main-title {
        color: #a31313;
        font-size: 44px;
        font-weight: 800;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #666;
        text-align: center;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .section-title {
        color: #a31313;
        font-size: 25px;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    .total-box {
        background: linear-gradient(
            135deg,
            #a31313,
            #d32f2f
        );
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }

    .total-label {
        font-size: 16px;
    }

    .total-number {
        font-size: 32px;
        font-weight: 800;
    }

    .info-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #eeeeee;
        margin-bottom: 10px;
    }

    .chat-user {
        background: #e9f5ff;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
    }

    .chat-bot {
        background: white;
        border: 1px solid #eeeeee;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
    }

    .restaurant-image {
        border-radius: 18px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# THÔNG TIN N2 SUSHI
# ============================================================

RESTAURANT = {
    "name": "N2 Sushi",
    "phone": "0900 000 000",
    "address": "Địa chỉ N2 Sushi - cập nhật địa chỉ thật tại đây",
    "opening_hours": "10:00 - 22:00 hàng ngày",
}


# ============================================================
# MENU
# ============================================================

MENU = [

    # ----------------------------
    # MÓN ĂN
    # ----------------------------

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
        "description": "Sashimi tổng hợp",
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


    # ----------------------------
    # COMBO
    # ----------------------------

    {
        "code": "C02",
        "name": "Combo N2 Couple - 2 người",
        "category": "Combo",
        "price": 299000,
        "bestseller": True,
        "description": "Combo dành cho 2 người",
    },

    {
        "code": "C03",
        "name": "Combo N2 Family - 3 người",
        "category": "Combo",
        "price": 429000,
        "bestseller": True,
        "description": "Combo dành cho 3 người",
    },

    {
        "code": "C45",
        "name": "Combo N2 Party - 4-5 người",
        "category": "Combo",
        "price": 649000,
        "bestseller": True,
        "description": "Combo dành cho 4-5 người",
    },


    # ----------------------------
    # NƯỚC
    # ----------------------------

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
# VOUCHER
# ============================================================

VOUCHERS = {

    "N2WELCOME": {
        "type": "percent",
        "value": 10,
        "max_discount": 100000,
        "min_order": 200000,
        "description": "Giảm 10%, tối đa 100.000đ cho đơn từ 200.000đ",
    },

    "N2SAVE50": {
        "type": "fixed",
        "value": 50000,
        "max_discount": 50000,
        "min_order": 300000,
        "description": "Giảm 50.000đ cho đơn từ 300.000đ",
    },

    "N2VIP": {
        "type": "percent",
        "value": 15,
        "max_discount": 150000,
        "min_order": 500000,
        "description": "Giảm 15%, tối đa 150.000đ cho đơn từ 500.000đ",
    },
}


# ============================================================
# KHUYẾN MÃI
# ============================================================

PROMOTIONS = [
    "Combo N2 Couple dành cho 2 người.",
    "Combo N2 Family dành cho 3 người.",
    "Combo N2 Party dành cho 4-5 người.",
    "Khách có thể nhập voucher trực tiếp tại màn hình thanh toán.",
]


# ============================================================
# HÀM TIỆN ÍCH
# ============================================================

def format_currency(value):

    return (
        f"{float(value):,.0f} ₫"
        .replace(",", ".")
    )


def calculate_voucher(
    subtotal,
    voucher_code,
):

    voucher_code = (
        str(voucher_code or "")
        .strip()
        .upper()
    )

    if not voucher_code:
        return 0, "Không sử dụng voucher"

    if voucher_code not in VOUCHERS:
        return (
            0,
            f"Voucher {voucher_code} không tồn tại.",
        )

    voucher = VOUCHERS[voucher_code]

    if subtotal < voucher["min_order"]:

        return (
            0,
            f"Đơn hàng phải từ "
            f"{format_currency(voucher['min_order'])}.",
        )

    if voucher["type"] == "percent":

        discount = (
            subtotal
            * voucher["value"]
            / 100
        )

    else:

        discount = voucher["value"]

    discount = min(
        discount,
        voucher["max_discount"],
    )

    discount = min(
        discount,
        subtotal,
    )

    return (
        discount,
        f"Đã áp dụng voucher {voucher_code}: "
        f"-{format_currency(discount)}",
    )


def calculate_points(total):

    # 10.000đ = 1 điểm
    return int(total // 10000)


def generate_invoice_number():

    return (
        "N2-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + "-"
        + str(uuid.uuid4())[:4].upper()
    )


# ============================================================
# TẠO PDF
# ============================================================

def find_font():

    paths = [

        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",

        "C:/Windows/Fonts/arial.ttf",

        "C:/Windows/Fonts/Arial.ttf",

        "/Library/Fonts/Arial.ttf",
    ]

    for path in paths:

        if os.path.exists(path):
            return path

    return None


def create_invoice_pdf(invoice):

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

    font_path = find_font()

    if font_path:

        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:

            pdfmetrics.registerFont(
                TTFont(
                    "N2Font",
                    font_path,
                )
            )

            font = "N2Font"

        except Exception:

            font = "Helvetica"

    else:

        font = "Helvetica"

    title_style = ParagraphStyle(
        "N2Title",
        parent=styles["Title"],
        fontName=font,
        fontSize=21,
        leading=25,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#a31313"),
    )

    normal_style = ParagraphStyle(
        "N2Normal",
        parent=styles["Normal"],
        fontName=font,
        fontSize=9,
        leading=13,
    )

    right_style = ParagraphStyle(
        "N2Right",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    elements = []

    elements.append(
        Paragraph(
            "N2 SUSHI",
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

    elements.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    elements.append(
        Paragraph(
            f"<b>HÓA ĐƠN THANH TOÁN</b><br/>"
            f"Mã hóa đơn: {invoice['invoice_number']}<br/>"
            f"Thời gian: "
            f"{invoice['created_at'].strftime('%d/%m/%Y %H:%M:%S')}<br/>"
            f"Bàn: {invoice['table_number']}<br/>"
            f"Khách hàng: {invoice['customer_name']}<br/>"
            f"SĐT: {invoice['phone'] or '---'}",
            normal_style,
        )
    )

    elements.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    data = [
        [
            Paragraph("<b>Món</b>", normal_style),
            Paragraph("<b>SL</b>", normal_style),
            Paragraph("<b>Đơn giá</b>", normal_style),
            Paragraph("<b>Thành tiền</b>", normal_style),
        ]
    ]

    for item in invoice["items"]:

        note = item["note"]

        item_name = item["name"]

        if note:

            item_name += (
                f"<br/><font size='7'>"
                f"Note: {note}"
                f"</font>"
            )

        data.append(
            [
                Paragraph(
                    item_name,
                    normal_style,
                ),
                str(item["quantity"]),
                format_currency(
                    item["price"]
                ),
                format_currency(
                    item["line_total"]
                ),
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
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#a31313"),
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
                    font,
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

    elements.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    summary = [

        [
            Paragraph(
                "Tạm tính",
                normal_style,
            ),

            Paragraph(
                format_currency(
                    invoice["subtotal"]
                ),
                right_style,
            ),
        ],

        [
            Paragraph(
                "Giảm voucher",
                normal_style,
            ),

            Paragraph(
                "-"
                + format_currency(
                    invoice["discount"]
                ),
                right_style,
            ),
        ],

        [
            Paragraph(
                "<b>TỔNG THANH TOÁN</b>",
                normal_style,
            ),

            Paragraph(
                "<b>"
                + format_currency(
                    invoice["total"]
                )
                + "</b>",
                right_style,
            ),
        ],

        [
            Paragraph(
                "Điểm tích lũy",
                normal_style,
            ),

            Paragraph(
                str(invoice["points"]),
                right_style,
            ),
        ],
    ]

    summary_table = Table(
        summary,
        colWidths=[
            120 * mm,
            55 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    font,
                ),

                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    1,
                    colors.HexColor("#a31313"),
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

    elements.append(
        Spacer(
            1,
            10 * mm,
        )
    )

    elements.append(
        Paragraph(
            "Cảm ơn quý khách đã đến N2 Sushi! ❤️",
            ParagraphStyle(
                "Thanks",
                parent=normal_style,
                alignment=TA_CENTER,
                fontSize=11,
                textColor=colors.HexColor("#a31313"),
            ),
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# CHATBOT
# ============================================================

def get_api_key():

    try:

        key = st.secrets.get(
            "OPENROUTER_API_KEY",
            "",
        )

        if key:
            return key

    except Exception:
        pass

    return os.getenv(
        "OPENROUTER_API_KEY",
        "",
    )


def get_model():

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


def build_knowledge():

    bestsellers = [
        x
        for x in MENU
        if x["bestseller"]
    ]

    best_text = "\n".join(
        [
            f"- {x['name']}: "
            f"{format_currency(x['price'])}"
            for x in bestsellers
        ]
    )

    combos = [
        x
        for x in MENU
        if x["category"] == "Combo"
    ]

    combo_text = "\n".join(
        [
            f"- {x['name']}: "
            f"{format_currency(x['price'])}"
            for x in combos
        ]
    )

    menu_text = "\n".join(
        [
            f"- {x['name']} "
            f"({x['category']}): "
            f"{format_currency(x['price'])}"
            for x in MENU
        ]
    )

    promo_text = "\n".join(
        [
            f"- {x}"
            for x in PROMOTIONS
        ]
    )

    return f"""
N2 SUSHI

Tên quán:
{RESTAURANT['name']}

Địa chỉ:
{RESTAURANT['address']}

Điện thoại:
{RESTAURANT['phone']}

Giờ mở cửa:
{RESTAURANT['opening_hours']}

BEST SELLER:
{best_text}

COMBO:
{combo_text}

KHUYẾN MÃI:
{promo_text}

MENU:
{menu_text}

VOUCHER:
{list(VOUCHERS.keys())}
"""


def local_chatbot(message):

    text = message.lower()

    # ----------------------------
    # BEST SELLER
    # ----------------------------

    if (
        "best seller" in text
        or "bán chạy" in text
        or "bán chạy nhất" in text
    ):

        best = [
            x
            for x in MENU
            if x["bestseller"]
        ]

        result = "🍣 **Best seller của N2 Sushi:**\n\n"

        for x in best:

            result += (
                f"- **{x['name']}** — "
                f"{format_currency(x['price'])}\n"
            )

        return result


    # ----------------------------
    # COMBO 2 NGƯỜI
    # ----------------------------

    if (
        "2 người" in text
        or "2 nguoi" in text
    ):

        return (
            "👫 **Combo dành cho 2 người:**\n\n"
            "- Combo N2 Couple - 2 người\n"
            "  Giá: 299.000đ"
        )


    # ----------------------------
    # COMBO 3 NGƯỜI
    # ----------------------------

    if (
        "3 người" in text
        or "3 nguoi" in text
    ):

        return (
            "👨‍👩‍👧 **Combo dành cho 3 người:**\n\n"
            "- Combo N2 Family - 3 người\n"
            "  Giá: 429.000đ"
        )


    # ----------------------------
    # COMBO 4-5 NGƯỜI
    # ----------------------------

    if (
        "4-5" in text
        or "4 5" in text
        or "4 người" in text
        or "5 người" in text
    ):

        return (
            "👨‍👩‍👧‍👦 **Combo dành cho 4-5 người:**\n\n"
            "- Combo N2 Party - 4-5 người\n"
            "  Giá: 649.000đ"
        )


    # ----------------------------
    # KHUYẾN MÃI
    # ----------------------------

    if (
        "khuyến mãi" in text
        or "khuyen mai" in text
        or "ưu đãi" in text
        or "voucher" in text
    ):

        result = (
            "🎁 **Khuyến mãi của N2 Sushi:**\n\n"
        )

        for x in PROMOTIONS:

            result += f"- {x}\n"

        return result


    # ----------------------------
    # ĐỊA CHỈ
    # ----------------------------

    if (
        "địa chỉ" in text
        or "dia chi" in text
        or "ở đâu" in text
        or "o dau" in text
    ):

        return (
            "📍 **Địa chỉ N2 Sushi:**\n\n"
            + RESTAURANT["address"]
        )


    # ----------------------------
    # GIỜ MỞ CỬA
    # ----------------------------

    if (
        "giờ mở cửa" in text
        or "gio mo cua" in text
        or "mấy giờ mở" in text
    ):

        return (
            "🕐 **Giờ mở cửa N2 Sushi:**\n\n"
            + RESTAURANT["opening_hours"]
        )


    # ----------------------------
    # MENU
    # ----------------------------

    if (
        "menu" in text
        or "thực đơn" in text
        or "thuc don" in text
    ):

        result = (
            "🍣 **Một số món của N2 Sushi:**\n\n"
        )

        for x in MENU:

            result += (
                f"- {x['name']} — "
                f"{format_currency(x['price'])}\n"
            )

        return result


    # ----------------------------
    # MẶC ĐỊNH
    # ----------------------------

    return (
        "Xin chào! 👋 Mình là trợ lý N2 Sushi.\n\n"
        "Bạn có thể hỏi mình:\n"
        "- 🍣 Best seller là gì?\n"
        "- 👫 Combo cho 2 người?\n"
        "- 👨‍👩‍👧 Combo cho 3 người?\n"
        "- 👨‍👩‍👧‍👦 Combo cho 4-5 người?\n"
        "- 🎁 N2 Sushi đang có khuyến mãi gì?\n"
        "- 📍 Địa chỉ quán?\n"
        "- 🕐 Giờ mở cửa?\n"
        "- 🍱 Menu có món gì?"
    )


def ask_ai(
    user_message,
    chat_history,
):

    api_key = get_api_key()

    if not api_key:

        return local_chatbot(
            user_message
        )

    system_prompt = f"""
Bạn là chatbot chính thức của N2 Sushi.

Trả lời bằng tiếng Việt.
Thân thiện, ngắn gọn và chính xác.

Chỉ sử dụng thông tin dưới đây:

{build_knowledge()}

QUY TẮC:

1. Không được tự bịa thông tin.
2. Không tự bịa giá.
3. Không tự bịa địa chỉ.
4. Không tự bịa chương trình khuyến mãi.
5. Nếu không có thông tin, nói rằng thông tin chưa được cập nhật.
6. Nếu khách hỏi best seller, sử dụng danh sách BEST SELLER.
7. Nếu khách hỏi combo 2 người, 3 người hoặc 4-5 người,
   giới thiệu đúng combo tương ứng.
8. Không tiết lộ API key.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    messages.extend(
        chat_history[-10:]
    )

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
                "Authorization":
                    f"Bearer {api_key}",

                "Content-Type":
                    "application/json",

                "HTTP-Referer":
                    "http://localhost:8501",

                "X-Title":
                    "N2 Sushi POS",
            },

            json={
                "model": get_model(),

                "messages": messages,

                "temperature": 0.2,

                "max_tokens": 700,
            },

            timeout=45,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data["choices"][0]
            ["message"]
            ["content"]
        )

    except Exception:

        return local_chatbot(
            user_message
        )


# ============================================================
# SESSION STATE
# ============================================================

if "chat_messages" not in st.session_state:

    st.session_state.chat_messages = []


if "invoice_data" not in st.session_state:

    st.session_state.invoice_data = None


if "invoice_pdf" not in st.session_state:

    st.session_state.invoice_pdf = None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🍣 N2 SUSHI</div>',
    unsafe_allow_html=True,
)


# ============================================================
# ẢNH QUÁN
# ============================================================

image_col1, image_col2, image_col3 = st.columns(
    [1, 2, 1]
)

with image_col2:

    try:

        st.image(
            "sushi.jpg",
            width="stretch",
        )

    except Exception:

        st.warning(
            "Không tìm thấy file sushi.jpg. "
            "Hãy đặt sushi.jpg cùng thư mục với app.py."
        )


st.markdown(
    '<div class="sub-title">'
    "POS Order • Thanh toán • Tích điểm • Chatbot"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR CHATBOT
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🤖 N2 Sushi Assistant"
    )

    if get_api_key():

        st.success(
            "AI Chatbot: Đã kết nối"
        )

    else:

        st.info(
            "AI Chatbot đang ở chế độ offline."
        )

    st.markdown("---")


    for message in st.session_state.chat_messages:

        if message["role"] == "user":

            st.markdown(
                f"""
                <div class="chat-user">
                    <b>👤 Bạn</b><br>
                    {message["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                f"""
                <div class="chat-bot">
                    <b>🤖 N2 Sushi</b><br>
                    {message["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )


    user_message = st.chat_input(
        "Hỏi N2 Sushi..."
    )


    if user_message:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        history = [
            {
                "role": x["role"],
                "content": x["content"],
            }

            for x in st.session_state.chat_messages
        ]

        answer = ask_ai(
            user_message,
            history[:-1],
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


# ============================================================
# TABS
# ============================================================

tab_order, tab_menu, tab_invoice, tab_info = st.tabs(
    [
        "🧾 Tạo hóa đơn",
        "🍣 Menu",
        "📄 Hóa đơn",
        "ℹ️ Thông tin",
    ]
)


# ============================================================
# TAB TẠO HÓA ĐƠN
# ============================================================

with tab_order:

    st.markdown(
        '<div class="section-title">'
        "Thông tin khách hàng"
        "</div>",
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
        '<div class="section-title">'
        "Chọn món"
        "</div>",
        unsafe_allow_html=True,
    )


    st.caption(
        "Một khách có thể chọn nhiều món khác nhau."
    )


    # --------------------------------------------------------
    # BẢNG ORDER
    # --------------------------------------------------------

    item_options = [
        "-- Chọn món --"
    ] + [
        x["name"]
        for x in MENU
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
            ),

            "Số lượng":
                st.column_config.NumberColumn(
                    "🔢 Số lượng",
                    min_value=0,
                    max_value=100,
                    step=1,
                ),

            "Ghi chú":
                st.column_config.TextColumn(
                    "📝 Ghi chú",
                ),
        },
    )


    # --------------------------------------------------------
    # VOUCHER
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        "Voucher"
        "</div>",
        unsafe_allow_html=True,
    )


    voucher_code = st.text_input(
        "🎟️ Nhập mã voucher",
        placeholder="Ví dụ: N2WELCOME",
    )


    # --------------------------------------------------------
    # TÍNH ORDER
    # --------------------------------------------------------

    order_items = []


    for _, row in edited_order.iterrows():

        item_name = row["Món"]

        if (
            pd.isna(item_name)
            or item_name == "-- Chọn món --"
        ):
            continue


        try:

            quantity = int(
                row["Số lượng"]
            )

        except Exception:

            quantity = 0


        if quantity <= 0:
            continue


        item = MENU_LOOKUP.get(
            item_name
        )


        if not item:
            continue


        note = row["Ghi chú"]

        if pd.isna(note):
            note = ""


        line_total = (
            item["price"]
            * quantity
        )


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


    discount, voucher_message = (
        calculate_voucher(
            subtotal,
            voucher_code,
        )
    )


    total = max(
        0,
        subtotal - discount,
    )


    points = calculate_points(
        total
    )


    # --------------------------------------------------------
    # HIỂN THỊ ORDER
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        "Kiểm tra đơn hàng"
        "</div>",
        unsafe_allow_html=True,
    )


    if order_items:

        result_df = pd.DataFrame(
            [
                {
                    "Món": x["name"],
                    "Loại": x["category"],
                    "Số lượng": x["quantity"],
                    "Đơn giá":
                        format_currency(
                            x["price"]
                        ),
                    "Ghi chú": x["note"],
                    "Thành tiền":
                        format_currency(
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
            "Chưa có món nào."
        )


    # --------------------------------------------------------
    # TỔNG TIỀN
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.metric(
            "Tạm tính",
            format_currency(
                subtotal
            ),
        )


    with c2:

        st.metric(
            "Giảm voucher",
            format_currency(
                discount
            ),
        )


    with c3:

        st.metric(
            "Điểm tích lũy",
            f"+{points}",
        )


    with c4:

        st.markdown(
            f"""
            <div class="total-box">
                <div class="total-label">
                    TỔNG THANH TOÁN
                </div>

                <div class="total-number">
                    {format_currency(total)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    if voucher_code:

        if discount > 0:

            st.success(
                voucher_message
            )

        else:

            st.warning(
                voucher_message
            )


    st.markdown("---")


    # --------------------------------------------------------
    # THANH TOÁN
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

            **Số loại món:** {len(order_items)}

            **Tổng số lượng:** {
                sum(
                    x["quantity"]
                    for x in order_items
                )
            }
            """
        )


    with payment_col2:

        pay = st.button(
            "💳 THANH TOÁN",
            type="primary",
            use_container_width=True,
        )


        if pay:

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

                invoice = {

                    "invoice_number":
                        generate_invoice_number(),

                    "created_at":
                        datetime.now(),

                    "table_number":
                        table_number,

                    "customer_name":
                        customer_name,

                    "phone":
                        phone,

                    "items":
                        order_items,

                    "subtotal":
                        subtotal,

                    "discount":
                        discount,

                    "total":
                        total,

                    "voucher_code":
                        voucher_code.upper(),

                    "points":
                        points,
                }


                st.session_state.invoice_data = invoice


                if REPORTLAB_AVAILABLE:

                    st.session_state.invoice_pdf = (
                        create_invoice_pdf(
                            invoice
                        )
                    )

                else:

                    st.session_state.invoice_pdf = None


                st.success(
                    "✅ Thanh toán thành công! "
                    f"Mã hóa đơn: "
                    f"{invoice['invoice_number']}"
                )

                st.balloons()


# ============================================================
# TAB MENU
# ============================================================

with tab_menu:

    st.markdown(
        '<div class="section-title">'
        "🍣 Menu N2 Sushi"
        "</div>",
        unsafe_allow_html=True,
    )


    category = st.selectbox(
        "Danh mục",
        [
            "Tất cả",
            "Món ăn",
            "Combo",
            "Nước uống",
        ],
    )


    search = st.text_input(
        "🔎 Tìm món",
        placeholder="Nhập tên món...",
    )


    menu_display = MENU_DF.copy()


    if category != "Tất cả":

        menu_display = menu_display[
            menu_display["category"]
            == category
        ]


    if search.strip():

        menu_display = menu_display[
            menu_display["name"]
            .str.lower()
            .str.contains(
                search.lower(),
                na=False,
            )
        ]


    display = []


    for _, row in menu_display.iterrows():

        display.append(
            {
                "Mã":
                    row["code"],

                "Món":
                    row["name"],

                "Loại":
                    row["category"],

                "Giá":
                    format_currency(
                        row["price"]
                    ),

                "⭐":
                    "Best seller"
                    if row["bestseller"]
                    else "",

                "Mô tả":
                    row["description"],
            }
        )


    st.dataframe(
        pd.DataFrame(display),
        width="stretch",
        hide_index=True,
    )


# ============================================================
# TAB HÓA ĐƠN
# ============================================================

with tab_invoice:

    st.markdown(
        '<div class="section-title">'
        "📄 Hóa đơn gần nhất"
        "</div>",
        unsafe_allow_html=True,
    )


    invoice = (
        st.session_state.invoice_data
    )


    if not invoice:

        st.info(
            "Chưa có hóa đơn."
        )

    else:

        st.success(
            f"Hóa đơn: "
            f"{invoice['invoice_number']}"
        )


        st.markdown(
            f"""
            <div class="info-card">

            <b>Mã hóa đơn:</b>
            {invoice['invoice_number']}
            <br><br>

            <b>Thời gian:</b>
            {invoice['created_at'].strftime(
                '%d/%m/%Y %H:%M:%S'
            )}
            <br><br>

            <b>Bàn:</b>
            {invoice['table_number']}
            <br><br>

            <b>Khách hàng:</b>
            {invoice['customer_name']}
            <br><br>

            <b>SĐT:</b>
            {invoice['phone'] or '---'}

            </div>
            """,
            unsafe_allow_html=True,
        )


        invoice_df = pd.DataFrame(
            [
                {
                    "Món": x["name"],
                    "Số lượng":
                        x["quantity"],
                    "Đơn giá":
                        format_currency(
                            x["price"]
                        ),
                    "Ghi chú":
                        x["note"],
                    "Thành tiền":
                        format_currency(
                            x["line_total"]
                        ),
                }

                for x in invoice["items"]
            ]
        )


        st.dataframe(
            invoice_df,
            width="stretch",
            hide_index=True,
        )


        st.markdown(
            f"""
            ### Tổng kết

            **Tạm tính:** {
                format_currency(
                    invoice["subtotal"]
                )
            }

            **Giảm voucher:** {
                format_currency(
                    invoice["discount"]
                )
            }

            # **TỔNG THANH TOÁN: {
                format_currency(
                    invoice["total"]
                )
            }**

            **Điểm tích lũy:** +
            {invoice["points"]} điểm
            """
        )


        if st.session_state.invoice_pdf:

            st.download_button(

                "📥 TẢI HÓA ĐƠN PDF",

                data=st.session_state.invoice_pdf,

                file_name=(
                    f"{invoice['invoice_number']}.pdf"
                ),

                mime="application/pdf",

                use_container_width=True,

                type="primary",
            )


# ============================================================
# TAB THÔNG TIN
# ============================================================

with tab_info:

    st.markdown(
        '<div class="section-title">'
        "ℹ️ Thông tin N2 Sushi"
        "</div>",
        unsafe_allow_html=True,
    )


    c1, c2 = st.columns(2)


    with c1:

        st.markdown(
            f"""
            <div class="info-card">

            <h3>🍣 N2 Sushi</h3>

            <b>📍 Địa chỉ</b><br>
            {RESTAURANT['address']}

            <br><br>

            <b>☎️ Điện thoại</b><br>
            {RESTAURANT['phone']}

            <br><br>

            <b>🕐 Giờ mở cửa</b><br>
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


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    st.markdown("---")

    st.markdown(
        "### 🎁 Voucher hiện có"
    )


    for code, voucher in VOUCHERS.items():

        st.markdown(
            f"""
            <div class="info-card">

            <b>🎟️ {code}</b><br>

            {voucher['description']}

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🍣 N2 Sushi POS • Order • Thanh toán • "
    "Voucher • Tích điểm • Hóa đơn • AI Assistant"
)
