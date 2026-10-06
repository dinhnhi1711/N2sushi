import os
import io
import uuid
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ============================================================
# OPTIONAL PDF
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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="N2 Sushi",
    page_icon="🍣",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DATA
# ============================================================

RESTAURANT = {
    "name": "N2 Sushi",
    "tagline": "Japanese Cuisine • Premium Sushi",
    "phone": "0900 000 000",
    "address": "Địa chỉ N2 Sushi - cập nhật địa chỉ thật tại đây",
    "opening_hours": "10:00 - 22:00 hàng ngày",
}


MENU = [
    {
        "code": "S01",
        "name": "Sushi cá hồi",
        "category": "Món ăn",
        "price": 69000,
        "bestseller": True,
        "description": "Cá hồi tươi, cơm sushi Nhật",
    },
    {
        "code": "S02",
        "name": "Sushi cá ngừ",
        "category": "Món ăn",
        "price": 65000,
        "bestseller": True,
        "description": "Cá ngừ tươi cùng cơm sushi",
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
        "description": "Tổng hợp nhiều loại sashimi",
    },
    {
        "code": "S05",
        "name": "Maki cá hồi bơ",
        "category": "Món ăn",
        "price": 89000,
        "bestseller": True,
        "description": "Cá hồi, bơ và rong biển",
    },
    {
        "code": "S06",
        "name": "Maki tempura tôm",
        "category": "Món ăn",
        "price": 99000,
        "bestseller": False,
        "description": "Tôm tempura cuộn maki",
    },
    {
        "code": "S07",
        "name": "Salmon Aburi",
        "category": "Món ăn",
        "price": 109000,
        "bestseller": True,
        "description": "Cá hồi áp lửa kiểu Nhật",
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

    {
        "code": "C02",
        "name": "Combo N2 Couple",
        "category": "Combo",
        "price": 299000,
        "bestseller": True,
        "description": "Combo dành cho 2 người",
    },
    {
        "code": "C03",
        "name": "Combo N2 Family",
        "category": "Combo",
        "price": 429000,
        "bestseller": True,
        "description": "Combo dành cho 3 người",
    },
    {
        "code": "C45",
        "name": "Combo N2 Party",
        "category": "Combo",
        "price": 649000,
        "bestseller": True,
        "description": "Combo dành cho 4-5 người",
    },

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
        "description": "Trà đào mát lạnh",
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


PROMOTIONS = [
    "Combo N2 Couple dành cho 2 người.",
    "Combo N2 Family dành cho 3 người.",
    "Combo N2 Party dành cho 4-5 người.",
    "Nhập voucher để nhận ưu đãi khi thanh toán.",
]


MENU_LOOKUP = {
    item["name"]: item
    for item in MENU
}


# ============================================================
# HELPER
# ============================================================

def money(value):
    return f"{float(value):,.0f} ₫".replace(",", ".")


def calculate_voucher(subtotal, code):

    code = str(code or "").strip().upper()

    if not code:
        return 0, ""

    if code not in VOUCHERS:
        return 0, f"Voucher {code} không tồn tại."

    voucher = VOUCHERS[code]

    if subtotal < voucher["min_order"]:
        return (
            0,
            f"Đơn tối thiểu {money(voucher['min_order'])} "
            f"để sử dụng voucher này.",
        )

    if voucher["type"] == "percent":
        discount = subtotal * voucher["value"] / 100
    else:
        discount = voucher["value"]

    discount = min(discount, voucher["max_discount"])
    discount = min(discount, subtotal)

    return (
        discount,
        f"Đã áp dụng {code}: giảm {money(discount)}",
    )


def loyalty_points(total):
    return int(total // 10000)


def invoice_number():
    return (
        "N2-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + "-"
        + str(uuid.uuid4())[:4].upper()
    )


# ============================================================
# AI CHATBOT
# ============================================================

def get_api_key():

    try:
        key = st.secrets.get("OPENROUTER_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    return os.getenv("OPENROUTER_API_KEY", "")


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


def local_bot(question):

    q = question.lower()

    if "best seller" in q or "bán chạy" in q:

        items = [
            x for x in MENU
            if x["bestseller"]
        ]

        text = "🍣 **Best seller của N2 Sushi:**\n\n"

        for item in items:
            text += (
                f"- {item['name']} — "
                f"{money(item['price'])}\n"
            )

        return text

    if "2 người" in q:

        return (
            "👫 **Combo cho 2 người**\n\n"
            "**Combo N2 Couple** — 299.000đ"
        )

    if "3 người" in q:

        return (
            "👨‍👩‍👧 **Combo cho 3 người**\n\n"
            "**Combo N2 Family** — 429.000đ"
        )

    if (
        "4-5" in q
        or "4 5" in q
        or "4 người" in q
        or "5 người" in q
    ):

        return (
            "👨‍👩‍👧‍👦 **Combo cho 4-5 người**\n\n"
            "**Combo N2 Party** — 649.000đ"
        )

    if (
        "khuyến mãi" in q
        or "khuyen mai" in q
        or "ưu đãi" in q
        or "voucher" in q
    ):

        result = "🎁 **Khuyến mãi tại N2 Sushi:**\n\n"

        for promo in PROMOTIONS:
            result += f"- {promo}\n"

        return result

    if (
        "địa chỉ" in q
        or "dia chi" in q
        or "ở đâu" in q
        or "o dau" in q
    ):

        return (
            "📍 **Địa chỉ N2 Sushi:**\n\n"
            + RESTAURANT["address"]
        )

    if (
        "giờ mở cửa" in q
        or "gio mo cua" in q
        or "mấy giờ mở" in q
    ):

        return (
            "🕐 **N2 Sushi mở cửa:**\n\n"
            + RESTAURANT["opening_hours"]
        )

    if (
        "menu" in q
        or "thực đơn" in q
        or "thuc don" in q
    ):

        result = "🍣 **Menu N2 Sushi:**\n\n"

        for item in MENU:
            result += (
                f"- {item['name']} — "
                f"{money(item['price'])}\n"
            )

        return result

    return (
        "Xin chào 👋 Mình là trợ lý của N2 Sushi.\n\n"
        "Bạn có thể hỏi:\n"
        "- Best seller của quán là gì?\n"
        "- Combo cho 2 người?\n"
        "- Combo cho 3 người?\n"
        "- Combo cho 4-5 người?\n"
        "- Quán đang có khuyến mãi gì?\n"
        "- Địa chỉ quán ở đâu?\n"
        "- Giờ mở cửa?\n"
        "- Menu có món gì?"
    )


def ai_bot(question, history):

    api_key = get_api_key()

    if not api_key:
        return local_bot(question)

    knowledge = f"""
Bạn là trợ lý chính thức của N2 Sushi.

Tên quán: {RESTAURANT['name']}
Địa chỉ: {RESTAURANT['address']}
Điện thoại: {RESTAURANT['phone']}
Giờ mở cửa: {RESTAURANT['opening_hours']}

MENU:
{chr(10).join(
    f"- {x['name']}: {money(x['price'])}"
    for x in MENU
)}

BEST SELLER:
{chr(10).join(
    f"- {x['name']}"
    for x in MENU
    if x['bestseller']
)}

COMBO:
- Combo N2 Couple: 299.000đ - 2 người
- Combo N2 Family: 429.000đ - 3 người
- Combo N2 Party: 649.000đ - 4-5 người

KHUYẾN MÃI:
{chr(10).join(PROMOTIONS)}

VOUCHER:
{chr(10).join(VOUCHERS.keys())}

Chỉ dùng dữ liệu trên.
Không tự bịa thông tin.
Nếu không biết, nói rằng thông tin chưa được cập nhật.
Trả lời bằng tiếng Việt, thân thiện và ngắn gọn.
"""

    messages = [
        {
            "role": "system",
            "content": knowledge,
        }
    ]

    messages.extend(history[-8:])

    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-Title": "N2 Sushi POS",
            },
            json={
                "model": get_model(),
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 600,
            },
            timeout=40,
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception:

        return local_bot(question)


# ============================================================
# PDF
# ============================================================

def create_pdf(invoice):

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

    title = ParagraphStyle(
        "TitleN2",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        textColor=colors.HexColor("#a31313"),
    )

    normal = ParagraphStyle(
        "NormalN2",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
    )

    right = ParagraphStyle(
        "RightN2",
        parent=normal,
        alignment=TA_RIGHT,
    )

    story = []

    story.append(
        Paragraph(
            "N2 SUSHI",
            title,
        )
    )

    story.append(
        Paragraph(
            f"{RESTAURANT['address']}<br/>"
            f"Điện thoại: {RESTAURANT['phone']}<br/>"
            f"{RESTAURANT['opening_hours']}",
            normal,
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            f"<b>HÓA ĐƠN THANH TOÁN</b><br/>"
            f"Mã hóa đơn: {invoice['number']}<br/>"
            f"Thời gian: "
            f"{invoice['time'].strftime('%d/%m/%Y %H:%M:%S')}<br/>"
            f"Bàn: {invoice['table']}<br/>"
            f"Khách hàng: {invoice['customer']}<br/>"
            f"SĐT: {invoice['phone'] or '---'}",
            normal,
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    data = [
        [
            Paragraph("<b>Món</b>", normal),
            Paragraph("<b>SL</b>", normal),
            Paragraph("<b>Đơn giá</b>", normal),
            Paragraph("<b>Thành tiền</b>", normal),
        ]
    ]

    for item in invoice["items"]:

        name = item["name"]

        if item["note"]:
            name += (
                f"<br/><font size='7'>"
                f"Ghi chú: {item['note']}"
                f"</font>"
            )

        data.append(
            [
                Paragraph(name, normal),
                str(item["quantity"]),
                money(item["price"]),
                money(item["line_total"]),
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
                        colors.HexColor("#fff6f2"),
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

    story.append(table)

    story.append(
        Spacer(1, 5 * mm)
    )

    summary = [
        [
            "Tạm tính",
            money(invoice["subtotal"]),
        ],
        [
            "Giảm voucher",
            "-" + money(invoice["discount"]),
        ],
        [
            "TỔNG THANH TOÁN",
            money(invoice["total"]),
        ],
        [
            "Điểm tích lũy",
            f"+{invoice['points']} điểm",
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
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    1,
                    colors.HexColor("#a31313"),
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

    story.append(summary_table)

    story.append(
        Spacer(1, 10 * mm)
    )

    story.append(
        Paragraph(
            "Cảm ơn quý khách đã đến N2 Sushi ❤️",
            ParagraphStyle(
                "Thanks",
                parent=normal,
                alignment=TA_CENTER,
                fontSize=11,
                textColor=colors.HexColor("#a31313"),
            ),
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# SESSION
# ============================================================

if "chat" not in st.session_state:
    st.session_state.chat = []

if "invoice" not in st.session_state:
    st.session_state.invoice = None

if "pdf" not in st.session_state:
    st.session_state.pdf = None


# ============================================================
# PREMIUM CSS
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap'
    );

    * {
        font-family: 'Be Vietnam Pro', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(
                circle at top left,
                #fff5ef 0%,
                #fffaf7 35%,
                #ffffff 100%
            );
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #241512 0%,
                #160e0c 100%
            );
    }

    section[data-testid="stSidebar"] * {
        color: #fffaf7 !important;
    }

    .hero {
        position: relative;
        overflow: hidden;
        border-radius: 28px;
        margin-bottom: 25px;
        background:
            linear-gradient(
                135deg,
                #250b08,
                #8e1515 55%,
                #c83232
            );
        box-shadow:
            0 20px 45px rgba(90, 20, 10, 0.20);
    }

    .hero-content {
        padding: 36px 40px;
        color: white;
    }

    .hero-kicker {
        letter-spacing: 4px;
        font-size: 12px;
        text-transform: uppercase;
        opacity: 0.75;
    }

    .hero-title {
        font-size: 46px;
        font-weight: 800;
        line-height: 1.1;
        margin: 7px 0;
    }

    .hero-subtitle {
        font-size: 15px;
        opacity: 0.85;
    }

    .hero-badge {
        display: inline-block;
        margin-top: 18px;
        padding: 8px 15px;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.2);
        font-size: 12px;
    }

    .section-heading {
        font-size: 25px;
        font-weight: 800;
        color: #33120e;
        margin: 12px 0 15px;
    }

    .glass-card {
        background: rgba(255,255,255,0.86);
        border: 1px solid #f0e2dc;
        border-radius: 18px;
        padding: 20px;
        box-shadow:
            0 10px 30px rgba(70,20,10,0.06);
    }

    .metric-card {
        background: white;
        border-radius: 18px;
        padding: 18px;
        border: 1px solid #f0e4df;
        box-shadow:
            0 8px 25px rgba(70,20,10,0.06);
    }

    .metric-label {
        color: #8b7770;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-value {
        color: #31120e;
        font-size: 23px;
        font-weight: 800;
        margin-top: 5px;
    }

    .total-card {
        background:
            linear-gradient(
                135deg,
                #8f1111,
                #c92727
            );
        color: white;
        border-radius: 22px;
        padding: 25px;
        box-shadow:
            0 14px 35px rgba(143,17,17,0.24);
    }

    .total-small {
        opacity: 0.75;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    .total-price {
        font-size: 38px;
        font-weight: 800;
        margin-top: 5px;
    }

    .food-card {
        background: white;
        border: 1px solid #f0e3dd;
        border-radius: 18px;
        padding: 18px;
        min-height: 155px;
        box-shadow:
            0 8px 25px rgba(70,20,10,0.05);
    }

    .food-name {
        color: #35130f;
        font-weight: 800;
        font-size: 17px;
    }

    .food-desc {
        color: #8c7770;
        font-size: 12px;
        margin: 7px 0;
    }

    .food-price {
        color: #b51b1b;
        font-size: 17px;
        font-weight: 800;
    }

    .best-badge {
        background: #fff0d4;
        color: #9a6100;
        border-radius: 999px;
        padding: 4px 9px;
        font-size: 10px;
        font-weight: 700;
    }

    .info-chip {
        background: #fff4ef;
        color: #8e2920;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 11px;
        display: inline-block;
        margin: 2px;
    }

    .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        min-height: 44px;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
    }

    div[data-testid="stDataEditor"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #eadbd4;
    }

    div[data-testid="stTabs"] button {
        font-weight: 700;
    }

    .footer {
        text-align: center;
        color: #9c8881;
        font-size: 12px;
        padding: 25px 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-content">
            <div class="hero-kicker">
                JAPANESE CUISINE
            </div>

            <div class="hero-title">
                N2 Sushi
            </div>

            <div class="hero-subtitle">
                Premium Sushi • Sashimi • Japanese Dining
            </div>

            <div class="hero-badge">
                🍣 Fresh • Elegant • Japanese
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# IMAGE
# ============================================================

img1, img2, img3 = st.columns([1, 2, 1])

with img2:

    if os.path.exists("sushi.jpg"):

        st.image(
            "sushi.jpg",
            width="stretch",
        )

    else:

        st.warning(
            "Không tìm thấy sushi.jpg. "
            "Hãy đặt ảnh sushi.jpg cùng thư mục với app.py."
        )


# ============================================================
# QUICK INFO
# ============================================================

q1, q2, q3, q4 = st.columns(4)

with q1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Địa chỉ</div>
            <div class="metric-value">📍</div>
            <div style="font-size:12px;color:#777">
                {RESTAURANT['address']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with q2:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Giờ mở cửa</div>
            <div class="metric-value">🕐</div>
            <div style="font-size:12px;color:#777">
                {RESTAURANT['opening_hours']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with q3:

    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Best Seller</div>
            <div class="metric-value">⭐</div>
            <div style="font-size:12px;color:#777">
                Sushi & Sashimi
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with q4:

    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Tích điểm</div>
            <div class="metric-value">🎁</div>
            <div style="font-size:12px;color:#777">
                1 điểm / 10.000đ
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# SIDEBAR CHATBOT
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:8px 0 18px;
        ">
            <div style="
                font-size:42px;
            ">
                🍣
            </div>

            <div style="
                font-size:23px;
                font-weight:800;
            ">
                N2 Assistant
            </div>

            <div style="
                font-size:11px;
                opacity:.65;
            ">
                Your Japanese dining assistant
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if get_api_key():

        st.success(
            "AI đang hoạt động"
        )

    else:

        st.info(
            "Chế độ trợ lý offline"
        )

    for message in st.session_state.chat:

        if message["role"] == "user":

            st.markdown(
                f"""
                <div style="
                    background:#9d2020;
                    padding:11px 13px;
                    border-radius:14px;
                    margin:8px 0;
                ">
                    <b>Bạn</b><br>
                    {message["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                f"""
                <div style="
                    background:#3b2521;
                    padding:11px 13px;
                    border-radius:14px;
                    margin:8px 0;
                ">
                    <b>🍣 N2 Sushi</b><br>
                    {message["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

    chat_input = st.chat_input(
        "Hỏi N2 Sushi..."
    )

    if chat_input:

        st.session_state.chat.append(
            {
                "role": "user",
                "content": chat_input,
            }
        )

        history = [
            {
                "role": x["role"],
                "content": x["content"],
            }
            for x in st.session_state.chat
        ]

        answer = ai_bot(
            chat_input,
            history[:-1],
        )

        st.session_state.chat.append(
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

        st.session_state.chat = []

        st.rerun()


# ============================================================
# TABS
# ============================================================

order_tab, menu_tab, invoice_tab, info_tab = st.tabs(
    [
        "🧾  TẠO HÓA ĐƠN",
        "🍣  MENU",
        "📄  HÓA ĐƠN",
        "ℹ️  N2 SUSHI",
    ]
)


# ============================================================
# ORDER TAB
# ============================================================

with order_tab:

    st.markdown(
        '<div class="section-heading">'
        "Thông tin khách hàng"
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        table_number = st.text_input(
            "🪑 Số bàn",
            placeholder="VD: B12",
        )

    with c2:

        customer_name = st.text_input(
            "👤 Tên khách hàng",
            placeholder="Nguyễn Văn A",
        )

    with c3:

        phone = st.text_input(
            "📱 Số điện thoại tích điểm",
            placeholder="0901234567",
        )


    st.markdown(
        '<div class="section-heading">'
        "Chọn món"
        "</div>",
        unsafe_allow_html=True,
    )

    item_options = [
        "-- Chọn món --"
    ] + [
        x["name"]
        for x in MENU
    ]

    initial_rows = pd.DataFrame(
        [
            {
                "Món": "-- Chọn món --",
                "Số lượng": 0,
                "Ghi chú": "",
            }
            for _ in range(12)
        ]
    )

    order_editor = st.data_editor(
        initial_rows,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        key="premium_order_editor",
        column_config={
            "Món": st.column_config.SelectboxColumn(
                "🍣 Món",
                options=item_options,
                width="large",
            ),
            "Số lượng": st.column_config.NumberColumn(
                "SL",
                min_value=0,
                max_value=100,
                step=1,
                width="small",
            ),
            "Ghi chú": st.column_config.TextColumn(
                "📝 Ghi chú",
                width="large",
            ),
        },
    )


    st.markdown(
        '<div class="section-heading">'
        "Voucher & thanh toán"
        "</div>",
        unsafe_allow_html=True,
    )

    voucher_code = st.text_input(
        "🎟️ Mã voucher",
        placeholder="N2WELCOME",
    )


    # BUILD ORDER

    order_items = []

    for _, row in order_editor.iterrows():

        name = row["Món"]

        if (
            pd.isna(name)
            or name == "-- Chọn món --"
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

        item = MENU_LOOKUP.get(name)

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

    discount, voucher_message = calculate_voucher(
        subtotal,
        voucher_code,
    )

    total = max(
        0,
        subtotal - discount,
    )

    points = loyalty_points(total)


    # SUMMARY

    if order_items:

        st.markdown(
            '<div class="section-heading">'
            "Đơn hàng"
            "</div>",
            unsafe_allow_html=True,
        )

        order_df = pd.DataFrame(
            [
                {
                    "Món": x["name"],
                    "SL": x["quantity"],
                    "Đơn giá": money(x["price"]),
                    "Ghi chú": x["note"],
                    "Thành tiền": money(x["line_total"]),
                }
                for x in order_items
            ]
        )

        st.dataframe(
            order_df,
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "Chưa có món nào. Hãy chọn món ở bảng phía trên."
        )


    # TOTAL CARDS

    m1, m2, m3 = st.columns(3)

    with m1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    Tạm tính
                </div>
                <div class="metric-value">
                    {money(subtotal)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    Voucher
                </div>
                <div class="metric-value"
                     style="color:#198754">
                    - {money(discount)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    Điểm tích lũy
                </div>
                <div class="metric-value">
                    +{points}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.markdown("<br>", unsafe_allow_html=True)


    total_col, button_col = st.columns(
        [2, 1]
    )

    with total_col:

        st.markdown(
            f"""
            <div class="total-card">

                <div class="total-small">
                    Tổng thanh toán
                </div>

                <div class="total-price">
                    {money(total)}
                </div>

                <div style="
                    margin-top:8px;
                    opacity:.78;
                    font-size:12px;
                ">
                    N2 Sushi • Premium Japanese Dining
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with button_col:

        st.markdown(
            "<br>",
            unsafe_allow_html=True,
        )

        payment_button = st.button(
            "💳  THANH TOÁN",
            type="primary",
            use_container_width=True,
        )

        if payment_button:

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
                    "number": invoice_number(),
                    "time": datetime.now(),
                    "table": table_number,
                    "customer": customer_name,
                    "phone": phone,
                    "items": order_items,
                    "subtotal": subtotal,
                    "discount": discount,
                    "total": total,
                    "voucher": voucher_code.upper(),
                    "points": points,
                }

                st.session_state.invoice = invoice

                if REPORTLAB_AVAILABLE:

                    st.session_state.pdf = create_pdf(
                        invoice
                    )

                else:

                    st.session_state.pdf = None

                st.success(
                    "Thanh toán thành công!"
                )

                st.balloons()


# ============================================================
# MENU TAB
# ============================================================

with menu_tab:

    st.markdown(
        '<div class="section-heading">'
        "Menu N2 Sushi"
        "</div>",
        unsafe_allow_html=True,
    )

    filter_col, search_col = st.columns(
        [1, 2]
    )

    with filter_col:

        category = st.selectbox(
            "Danh mục",
            [
                "Tất cả",
                "Món ăn",
                "Combo",
                "Nước uống",
            ],
        )

    with search_col:

        search = st.text_input(
            "🔎 Tìm món",
            placeholder="Nhập tên món...",
        )


    filtered = MENU.copy()

    if category != "Tất cả":

        filtered = [
            x
            for x in filtered
            if x["category"] == category
        ]

    if search.strip():

        filtered = [
            x
            for x in filtered
            if search.lower()
            in x["name"].lower()
        ]


    cols = st.columns(3)

    for index, item in enumerate(filtered):

        with cols[index % 3]:

            badge = (
                '<span class="best-badge">'
                "⭐ BEST SELLER"
                "</span>"
                if item["bestseller"]
                else ""
            )

            st.markdown(
                f"""
                <div class="food-card">

                    {badge}

                    <div style="height:8px;"></div>

                    <div class="food-name">
                        {item['name']}
                    </div>

                    <div class="food-desc">
                        {item['description']}
                    </div>

                    <div class="food-price">
                        {money(item['price'])}
                    </div>

                    <div style="
                        margin-top:8px;
                    ">
                        <span class="info-chip">
                            {item['category']}
                        </span>

                        <span class="info-chip">
                            {item['code']}
                        </span>
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                "<div style='height:12px'></div>",
                unsafe_allow_html=True,
            )


# ============================================================
# INVOICE TAB
# ============================================================

with invoice_tab:

    st.markdown(
        '<div class="section-heading">'
        "Hóa đơn gần nhất"
        "</div>",
        unsafe_allow_html=True,
    )

    invoice = st.session_state.invoice

    if not invoice:

        st.info(
            "Chưa có hóa đơn. "
            "Hãy tạo đơn và bấm Thanh toán."
        )

    else:

        st.markdown(
            f"""
            <div class="glass-card">

            <h3 style="color:#a31313;">
                N2 SUSHI
            </h3>

            <b>Mã hóa đơn:</b>
            {invoice['number']}

            <br><br>

            <b>Thời gian:</b>
            {invoice['time'].strftime(
                '%d/%m/%Y %H:%M:%S'
            )}

            <br><br>

            <b>Bàn:</b>
            {invoice['table']}

            <br><br>

            <b>Khách hàng:</b>
            {invoice['customer']}

            <br><br>

            <b>Số điện thoại:</b>
            {invoice['phone'] or '---'}

            </div>
            """,
            unsafe_allow_html=True,
        )


        st.markdown(
            "<br>",
            unsafe_allow_html=True,
        )


        invoice_df = pd.DataFrame(
            [
                {
                    "Món": x["name"],
                    "SL": x["quantity"],
                    "Đơn giá": money(x["price"]),
                    "Ghi chú": x["note"],
                    "Thành tiền": money(x["line_total"]),
                }
                for x in invoice["items"]
            ]
        )

        st.dataframe(
            invoice_df,
            width="stretch",
            hide_index=True,
        )


        total_col1, total_col2 = st.columns(2)

        with total_col1:

            st.markdown(
                f"""
                <div class="glass-card">

                <b>Tạm tính</b>
                <br>
                {money(invoice['subtotal'])}

                <br><br>

                <b>Voucher</b>
                <br>
                - {money(invoice['discount'])}

                <br><br>

                <b>Điểm tích lũy</b>
                <br>
                +{invoice['points']} điểm

                </div>
                """,
                unsafe_allow_html=True,
            )

        with total_col2:

            st.markdown(
                f"""
                <div class="total-card">

                    <div class="total-small">
                        Tổng thanh toán
                    </div>

                    <div class="total-price">
                        {money(invoice['total'])}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        st.markdown("<br>", unsafe_allow_html=True)


        if st.session_state.pdf:

            st.download_button(
                "📥  TẢI HÓA ĐƠN PDF",
                data=st.session_state.pdf,
                file_name=f"{invoice['number']}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

        elif not REPORTLAB_AVAILABLE:

            st.warning(
                "Muốn tải PDF, hãy cài reportlab:"
            )

            st.code(
                "pip install reportlab"
            )


# ============================================================
# INFO TAB
# ============================================================

with info_tab:

    st.markdown(
        '<div class="section-heading">'
        "N2 Sushi"
        "</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:

        st.markdown(
            f"""
            <div class="glass-card">

                <h3 style="color:#a31313;">
                    🍣 N2 Sushi
                </h3>

                <p>
                    <b>📍 Địa chỉ</b><br>
                    {RESTAURANT['address']}
                </p>

                <p>
                    <b>☎️ Điện thoại</b><br>
                    {RESTAURANT['phone']}
                </p>

                <p>
                    <b>🕐 Giờ mở cửa</b><br>
                    {RESTAURANT['opening_hours']}
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with right:

        bestsellers = [
            x for x in MENU
            if x["bestseller"]
        ]

        best_text = ""

        for item in bestsellers:

            best_text += (
                f"""
                <div style="
                    padding:9px 0;
                    border-bottom:1px solid #eee;
                ">
                    ⭐ <b>{item['name']}</b>
                    <span style="
                        float:right;
                        color:#b51b1b;
                        font-weight:700;
                    ">
                        {money(item['price'])}
                    </span>
                </div>
                """
            )

        st.markdown(
            f"""
            <div class="glass-card">

                <h3 style="color:#a31313;">
                    ⭐ Best Seller
                </h3>

                {best_text}

            </div>
            """,
            unsafe_allow_html=True,
        )


    st.markdown("<br>", unsafe_allow_html=True)


    st.markdown(
        '<div class="section-heading">'
        "🎁 Voucher"
        "</div>",
        unsafe_allow_html=True,
    )


    voucher_cols = st.columns(3)

    for index, (code, data) in enumerate(
        VOUCHERS.items()
    ):

        with voucher_cols[index % 3]:

            st.markdown(
                f"""
                <div class="glass-card">

                    <div style="
                        color:#a31313;
                        font-weight:800;
                        font-size:18px;
                    ">
                        🎟️ {code}
                    </div>

                    <div style="
                        color:#777;
                        font-size:12px;
                        margin-top:8px;
                    ">
                        {data['description']}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🍣 N2 Sushi &nbsp;•&nbsp;
        Japanese Cuisine &nbsp;•&nbsp;
        Order & Payment System
    </div>
    """,
    unsafe_allow_html=True,
)
