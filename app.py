
import os
import textwrap
import uuid
from datetime import datetime

import requests
import streamlit as st



# =========================================================
# HÀM RENDER HTML AN TOÀN
# Xóa khoảng trắng đầu dòng để Streamlit không hiểu HTML
# là một khối code Markdown.
# =========================================================

def clean_html(content):
    return "\n".join(line.lstrip() for line in content.splitlines())


def html_markdown(content, *args, **kwargs):
    return st.markdown(clean_html(content), *args, **kwargs)


# =========================================================
# 1. CẤU HÌNH TRANG
# =========================================================

st.set_page_config(
    page_title="N2 Sushi",
    page_icon="🍣",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. THÔNG TIN QUÁN
# =========================================================

RESTAURANT_NAME = "N2 Sushi"
RESTAURANT_ADDRESS = "Địa chỉ N2 Sushi - cập nhật địa chỉ tại đây"
RESTAURANT_PHONE = "0900 000 000"
RESTAURANT_HOURS = "10:00 - 22:00 hàng ngày"


# =========================================================
# 3. MENU
# =========================================================

MENU = [
    {
        "id": "S01",
        "name": "Sushi cá hồi",
        "category": "Sushi",
        "price": 69000,
        "description": "Cá hồi tươi cùng cơm sushi Nhật",
        "best": True,
    },
    {
        "id": "S02",
        "name": "Sushi cá ngừ",
        "category": "Sushi",
        "price": 65000,
        "description": "Cá ngừ tươi cùng cơm sushi",
        "best": True,
    },
    {
        "id": "S03",
        "name": "Sashimi cá hồi",
        "category": "Sashimi",
        "price": 129000,
        "description": "Cá hồi tươi cắt lát kiểu Nhật",
        "best": True,
    },
    {
        "id": "S04",
        "name": "Sashimi tổng hợp",
        "category": "Sashimi",
        "price": 229000,
        "description": "Tổng hợp nhiều loại sashimi",
        "best": True,
    },
    {
        "id": "S05",
        "name": "Maki cá hồi bơ",
        "category": "Maki",
        "price": 89000,
        "description": "Cá hồi, bơ và rong biển",
        "best": True,
    },
    {
        "id": "S06",
        "name": "Maki tempura tôm",
        "category": "Maki",
        "price": 99000,
        "description": "Tôm tempura cuộn maki",
        "best": False,
    },
    {
        "id": "S07",
        "name": "Salmon Aburi",
        "category": "Sushi",
        "price": 109000,
        "description": "Cá hồi áp lửa kiểu Nhật",
        "best": True,
    },
    {
        "id": "S08",
        "name": "Unagi Sushi",
        "category": "Sushi",
        "price": 119000,
        "description": "Sushi lươn Nhật",
        "best": False,
    },
    {
        "id": "S09",
        "name": "Gyoza",
        "category": "Món ăn",
        "price": 79000,
        "description": "Bánh xếp Nhật",
        "best": False,
    },
    {
        "id": "S10",
        "name": "Edamame",
        "category": "Món ăn",
        "price": 49000,
        "description": "Đậu nành Nhật",
        "best": False,
    },
    {
        "id": "C02",
        "name": "Combo N2 Couple",
        "category": "Combo",
        "price": 299000,
        "description": "Combo dành cho 2 người",
        "best": True,
    },
    {
        "id": "C03",
        "name": "Combo N2 Family",
        "category": "Combo",
        "price": 429000,
        "description": "Combo dành cho 3 người",
        "best": True,
    },
    {
        "id": "C45",
        "name": "Combo N2 Party",
        "category": "Combo",
        "price": 649000,
        "description": "Combo dành cho 4-5 người",
        "best": True,
    },
    {
        "id": "D01",
        "name": "Coca-Cola",
        "category": "Nước uống",
        "price": 25000,
        "description": "Nước ngọt Coca-Cola",
        "best": False,
    },
    {
        "id": "D02",
        "name": "Sprite",
        "category": "Nước uống",
        "price": 25000,
        "description": "Nước ngọt Sprite",
        "best": False,
    },
    {
        "id": "D03",
        "name": "Trà đào",
        "category": "Nước uống",
        "price": 45000,
        "description": "Trà đào mát lạnh",
        "best": True,
    },
    {
        "id": "D04",
        "name": "Trà xanh Nhật",
        "category": "Nước uống",
        "price": 35000,
        "description": "Trà xanh Nhật",
        "best": False,
    },
]

MENU_BY_ID = {
    item["id"]: item
    for item in MENU
}


# =========================================================
# 4. VOUCHER
# =========================================================

VOUCHERS = {
    "N2WELCOME": {
        "type": "percent",
        "value": 10,
        "max_discount": 100000,
        "minimum": 200000,
    },
    "N2SAVE50": {
        "type": "fixed",
        "value": 50000,
        "max_discount": 50000,
        "minimum": 300000,
    },
    "N2VIP": {
        "type": "percent",
        "value": 15,
        "max_discount": 150000,
        "minimum": 500000,
    },
}


# =========================================================
# 5. SESSION STATE
# =========================================================

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "notes" not in st.session_state:
    st.session_state.notes = {}

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "invoice" not in st.session_state:
    st.session_state.invoice = None


# =========================================================
# 6. HÀM TIỆN ÍCH
# =========================================================

def money(value):
    return f"{int(value):,}".replace(",", ".") + " ₫"


def add_item(item_id):
    if item_id not in st.session_state.cart:
        st.session_state.cart[item_id] = 1
    else:
        st.session_state.cart[item_id] += 1


def remove_item(item_id):
    if item_id not in st.session_state.cart:
        return

    st.session_state.cart[item_id] -= 1

    if st.session_state.cart[item_id] <= 0:
        del st.session_state.cart[item_id]

        if item_id in st.session_state.notes:
            del st.session_state.notes[item_id]


def subtotal():
    total = 0

    for item_id, quantity in st.session_state.cart.items():
        item = MENU_BY_ID[item_id]
        total += item["price"] * quantity

    return total


def calculate_voucher(code, amount):
    code = code.strip().upper()

    if not code:
        return 0, ""

    if code not in VOUCHERS:
        return 0, "Voucher không tồn tại."

    voucher = VOUCHERS[code]

    if amount < voucher["minimum"]:
        return (
            0,
            f"Đơn hàng tối thiểu {money(voucher['minimum'])}.",
        )

    if voucher["type"] == "percent":
        discount = amount * voucher["value"] / 100
    else:
        discount = voucher["value"]

    discount = min(
        discount,
        voucher["max_discount"],
        amount,
    )

    return (
        discount,
        f"Đã áp dụng {code}: giảm {money(discount)}.",
    )


def loyalty_points(amount):
    return int(amount // 10000)


# =========================================================
# 7. CHATBOT LOCAL
# =========================================================

def local_chatbot(question):

    q = question.lower().strip()

    if (
        "best seller" in q
        or "best-seller" in q
        or "bán chạy" in q
        or "bán chạy nhất" in q
    ):
        best_items = [
            item["name"]
            for item in MENU
            if item["best"]
        ]

        return (
            "⭐ **Best seller của N2 Sushi:**\n\n"
            + "\n".join(
                f"- {name}"
                for name in best_items
            )
        )

    if "2 người" in q:
        return (
            "👫 **Combo cho 2 người**\n\n"
            "**Combo N2 Couple — 299.000đ**."
        )

    if "3 người" in q:
        return (
            "👨‍👩‍👧 **Combo cho 3 người**\n\n"
            "**Combo N2 Family — 429.000đ**."
        )

    if (
        "4-5 người" in q
        or "4 5 người" in q
        or "4 người" in q
        or "5 người" in q
    ):
        return (
            "👨‍👩‍👧‍👦 **Combo cho 4-5 người**\n\n"
            "**Combo N2 Party — 649.000đ**."
        )

    if (
        "khuyến mãi" in q
        or "khuyen mai" in q
        or "ưu đãi" in q
        or "voucher" in q
    ):
        return (
            "🎁 **Khuyến mãi / Voucher hiện có:**\n\n"
            "- **N2WELCOME:** giảm 10%, tối đa 100.000đ.\n"
            "- **N2SAVE50:** giảm 50.000đ.\n"
            "- **N2VIP:** giảm 15%, tối đa 150.000đ."
        )

    if (
        "địa chỉ" in q
        or "dia chi" in q
        or "ở đâu" in q
        or "địa điểm" in q
    ):
        return (
            "📍 **Địa chỉ N2 Sushi:**\n\n"
            f"{RESTAURANT_ADDRESS}"
        )

    if (
        "giờ mở cửa" in q
        or "mở cửa" in q
        or "gio mo cua" in q
        or "mấy giờ" in q
    ):
        return (
            "🕐 **Giờ mở cửa N2 Sushi:**\n\n"
            f"{RESTAURANT_HOURS}"
        )

    if "số điện thoại" in q or "hotline" in q:
        return (
            "📞 **Hotline N2 Sushi:**\n\n"
            f"{RESTAURANT_PHONE}"
        )

    return (
        "Xin chào 👋 Mình là trợ lý của N2 Sushi.\n\n"
        "Bạn có thể hỏi mình:\n\n"
        "- ⭐ Best seller là gì?\n"
        "- 👫 Combo cho 2 người?\n"
        "- 👨‍👩‍👧 Combo cho 3 người?\n"
        "- 👨‍👩‍👧‍👦 Combo cho 4-5 người?\n"
        "- 🎁 Đang có khuyến mãi gì?\n"
        "- 📍 Địa chỉ quán?\n"
        "- 🕐 Giờ mở cửa?"
    )


# =========================================================
# 8. CHATBOT AI
# =========================================================

def ask_chatbot(question):

    api_key = os.getenv("OPENROUTER_API_KEY", "")

    if not api_key:
        return local_chatbot(question)

    menu_text = "\n".join(
        f"{item['name']}: {money(item['price'])}"
        for item in MENU
    )

    system_prompt = f"""
Bạn là trợ lý AI chính thức của N2 Sushi.

Thông tin quán:
Tên: N2 Sushi
Địa chỉ: {RESTAURANT_ADDRESS}
Điện thoại: {RESTAURANT_PHONE}
Giờ mở cửa: {RESTAURANT_HOURS}

MENU:
{menu_text}

COMBO:
- Combo N2 Couple: 299.000đ - 2 người
- Combo N2 Family: 429.000đ - 3 người
- Combo N2 Party: 649.000đ - 4-5 người

VOUCHER:
- N2WELCOME: giảm 10%, tối đa 100.000đ
- N2SAVE50: giảm 50.000đ
- N2VIP: giảm 15%, tối đa 150.000đ

Hãy trả lời bằng tiếng Việt.
Trả lời ngắn gọn, thân thiện.
Không tự bịa thông tin.
Nếu không biết thông tin thì nói khách liên hệ nhân viên N2 Sushi.
"""

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": question,
                    },
                ],
                "temperature": 0.2,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception:
        return local_chatbot(question)


# =========================================================
# 9. CSS
# =========================================================

html_markdown(
    """
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap'
);

/* ===== TOÀN APP ===== */

html,
body,
[class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif;
}

.stApp {
    background:
        linear-gradient(
            135deg,
            #fffaf7 0%,
            #ffffff 50%,
            #fff6f2 100%
        );
}

/* ===== ẨN MENU STREAMLIT KHÔNG CẦN THIẾT ===== */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* ===== HEADER ===== */

.hero {
    background:
        linear-gradient(
            135deg,
            #260806,
            #8e1717,
            #c82d2d
        );

    border-radius: 28px;

    padding: 38px 42px;

    color: white;

    box-shadow:
        0 18px 45px rgba(100, 20, 10, 0.20);

    margin-bottom: 20px;
}

.hero-small {
    font-size: 11px;
    letter-spacing: 4px;
    opacity: 0.70;
}

.hero-title {
    font-size: 48px;
    font-weight: 800;
    line-height: 1.15;
    margin-top: 5px;
}

.hero-subtitle {
    font-size: 14px;
    opacity: 0.82;
    margin-top: 8px;
}

/* ===== INFO CARD ===== */

.info-box {
    background: #ffffff;
    border: 1px solid #eee0da;
    border-radius: 18px;
    padding: 18px;

    box-shadow:
        0 7px 25px rgba(70, 20, 10, 0.05);

    min-height: 105px;
}

.info-label {
    font-size: 10px;
    letter-spacing: 1.2px;
    color: #a08d86;
    font-weight: 700;
}

.info-value {
    color: #32130f;
    font-size: 17px;
    font-weight: 800;
    margin-top: 5px;
}

/* ===== SECTION ===== */

.section-title {
    color: #35130f;
    font-size: 25px;
    font-weight: 800;
    margin: 25px 0 15px;
}

/* ===== FOOD CARD ===== */

.food-card {
    background: #ffffff;

    border: 1px solid #eee0da;

    border-radius: 20px;

    padding: 20px;

    margin-bottom: 12px;

    min-height: 215px;

    box-shadow:
        0 8px 25px rgba(80, 20, 10, 0.055);

    transition:
        transform 0.15s ease,
        box-shadow 0.15s ease,
        border-color 0.15s ease;
}

.food-card:hover {
    transform: translateY(-2px);

    border-color: #d49a8d;

    box-shadow:
        0 12px 30px rgba(120, 30, 15, 0.12);
}

.food-name {
    font-size: 17px;
    font-weight: 800;
    color: #30120e;
}

.food-description {
    color: #95817a;
    font-size: 12px;
    min-height: 38px;
    margin-top: 7px;
}

.food-price {
    color: #b31d1d;
    font-size: 18px;
    font-weight: 800;
    margin: 12px 0;
}

.best {
    display: inline-block;

    background: #fff1d5;
    color: #956000;

    padding: 5px 9px;

    border-radius: 50px;

    font-size: 10px;
    font-weight: 800;
}

.category {
    display: inline-block;

    background: #fff4ef;
    color: #9a3329;

    padding: 5px 9px;

    border-radius: 50px;

    font-size: 10px;
}

/* ===== BUTTON ===== */

.stButton > button {
    border-radius: 12px !important;

    min-height: 42px;

    font-weight: 700 !important;

    border: 1px solid #eadbd5 !important;

    background: #ffffff !important;

    color: #5c2920 !important;

    transition: all 0.15s ease;
}

.stButton > button:hover {
    border-color: #bd3830 !important;

    color: #9b1717 !important;

    background: #fff8f5 !important;
}

/* PRIMARY */

.stButton > button[kind="primary"] {
    background:
        linear-gradient(
            135deg,
            #951414,
            #ce2e2e
        ) !important;

    border: none !important;

    color: #ffffff !important;
}

.stButton > button[kind="primary"]:hover {
    color: #ffffff !important;

    transform: translateY(-1px);
}

/* ===== INPUT ===== */

div[data-testid="stTextInput"] input {
    border-radius: 12px !important;

    border: 1px solid #eadbd5 !important;

    color: #32130f !important;

    background: #ffffff !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #a18d86 !important;
}

/* ===== CART ===== */

.cart-card {
    background: #ffffff;

    border: 1px solid #eee0da;

    border-radius: 22px;

    padding: 22px;

    box-shadow:
        0 10px 35px rgba(80, 20, 10, 0.07);
}

.cart-item {
    padding: 14px 0;

    border-bottom:
        1px solid #eee5e1;
}

.cart-name {
    color: #35130f;

    font-weight: 800;
}

.cart-price {
    color: #b21c1c;

    font-weight: 800;
}

/* ===== TOTAL ===== */

.total-card {
    background:
        linear-gradient(
            135deg,
            #8d1111,
            #c62929
        );

    color: white;

    border-radius: 22px;

    padding: 25px;

    margin-top: 18px;

    box-shadow:
        0 15px 35px rgba(140, 20, 20, 0.23);
}

.total-label {
    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: 1.5px;

    opacity: 0.72;
}

.total-number {
    font-size: 34px;

    font-weight: 800;

    margin-top: 4px;
}

/* =================================================
   SIDEBAR CHATBOT
   ================================================= */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #21120f 0%,
            #130a08 100%
        );
}

/* Không ép input thành chữ trắng */

section[data-testid="stSidebar"] label {
    color: #ffffff !important;
}

/* Text bên ngoài */

section[data-testid="stSidebar"] {
    color: #ffffff;
}

/* Ô nhập chatbot */

section[data-testid="stSidebar"] input {
    background: #ffffff !important;

    color: #21120f !important;

    caret-color: #a71919 !important;

    border:
        2px solid #d9b9ae !important;

    border-radius: 14px !important;

    padding: 10px 13px !important;

    font-size: 13px !important;
}

section[data-testid="stSidebar"] input:focus {
    border-color: #d13a32 !important;

    box-shadow:
        0 0 0 2px rgba(209, 58, 50, 0.18) !important;
}

section[data-testid="stSidebar"] input::placeholder {
    color: #9b8580 !important;

    opacity: 1 !important;
}

/* Chatbot message */

.chat-user {
    background:
        linear-gradient(
            135deg,
            #a51c1c,
            #c52a2a
        );

    color: #ffffff;

    padding: 11px 13px;

    border-radius:
        15px 15px 4px 15px;

    margin:
        8px 0 8px 20px;

    font-size: 12px;

    line-height: 1.55;
}

.chat-bot {
    background: #3a2723;

    color: #ffffff;

    padding: 11px 13px;

    border-radius:
        15px 15px 15px 4px;

    margin:
        8px 20px 8px 0;

    font-size: 12px;

    line-height: 1.55;

    border: 1px solid #513832;
}

/* Sidebar button */

section[data-testid="stSidebar"] .stButton > button {
    background: #3a2723 !important;

    color: #ffffff !important;

    border:
        1px solid #5a3d36 !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #51342e !important;

    color: #ffffff !important;
}

/* ===== FOOTER ===== */

.footer {
    text-align: center;

    color: #a18d86;

    font-size: 11px;

    padding:
        35px 0 15px;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# 10. HEADER
# =========================================================

html_markdown(
    """
<div class="hero">

    <div class="hero-small">
        JAPANESE CUISINE
    </div>

    <div class="hero-title">
        🍣 N2 Sushi
    </div>

    <div class="hero-subtitle">
        Premium Sushi • Sashimi • Japanese Dining
    </div>

</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# 11. ẢNH QUÁN
# =========================================================

if os.path.exists("sushi.jpg"):

    image_left, image_center, image_right = st.columns(
        [1, 2, 1]
    )

    with image_center:

        st.image(
            "sushi.jpg",
            width="stretch",
        )

else:

    st.warning(
        "Không tìm thấy sushi.jpg. "
        "Hãy đặt sushi.jpg cùng thư mục với app.py."
    )


# =========================================================
# 12. THÔNG TIN NHANH
# =========================================================

html_markdown("<br>", unsafe_allow_html=True)

info1, info2, info3, info4 = st.columns(4)


with info1:

    html_markdown(
        f"""
<div class="info-box">

<div class="info-label">
ĐỊA CHỈ
</div>

<div class="info-value">
📍 N2 Sushi
</div>

<div style="
font-size:11px;
color:#8f7b74;
margin-top:5px;
">
{RESTAURANT_ADDRESS}
</div>

</div>
""",
        unsafe_allow_html=True,
    )


with info2:

    html_markdown(
        f"""
<div class="info-box">

<div class="info-label">
GIỜ MỞ CỬA
</div>

<div class="info-value">
🕐 10:00 - 22:00
</div>

<div style="
font-size:11px;
color:#8f7b74;
margin-top:5px;
">
Hàng ngày
</div>

</div>
""",
        unsafe_allow_html=True,
    )


with info3:

    html_markdown(
        """
<div class="info-box">

<div class="info-label">
BEST SELLER
</div>

<div class="info-value">
⭐ Sushi & Sashimi
</div>

<div style="
font-size:11px;
color:#8f7b74;
margin-top:5px;
">
Món được yêu thích
</div>

</div>
""",
        unsafe_allow_html=True,
    )


with info4:

    html_markdown(
        """
<div class="info-box">

<div class="info-label">
TÍCH ĐIỂM
</div>

<div class="info-value">
🎁 1 điểm / 10.000đ
</div>

<div style="
font-size:11px;
color:#8f7b74;
margin-top:5px;
">
Dành cho khách hàng
</div>

</div>
""",
        unsafe_allow_html=True,
    )


# =========================================================
# 13. CHATBOT SIDEBAR
# =========================================================

with st.sidebar:

    html_markdown(
        """
<div style="
text-align:center;
padding:10px 0 18px;
">

<div style="
font-size:42px;
">
🍣
</div>

<div style="
font-size:23px;
font-weight:800;
color:#ffffff;
">
N2 Assistant
</div>

<div style="
font-size:11px;
color:#c9aaa1;
margin-top:4px;
">
Trợ lý N2 Sushi
</div>

</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # Tin nhắn cũ

    for message in st.session_state.chat_messages:

        if message["role"] == "user":

            html_markdown(
                f"""
<div class="chat-user">

<b>Bạn</b>

<br>

{message["content"]}

</div>
""",
                unsafe_allow_html=True,
            )

        else:

            content = message["content"]

            content = content.replace(
                "\n",
                "<br>",
            )

            html_markdown(
                f"""
<div class="chat-bot">

<b>🍣 N2 Sushi</b>

<br>

{content}

</div>
""",
                unsafe_allow_html=True,
            )


    # Input chatbot

    user_question = st.chat_input(
        "Hỏi N2 Sushi..."
    )


    if user_question:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": user_question,
            }
        )

        answer = ask_chatbot(
            user_question
        )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()


    if st.button(
        "🗑️ Xóa cuộc trò chuyện",
        use_container_width=True,
    ):

        st.session_state.chat_messages = []

        st.rerun()


# =========================================================
# 14. THÔNG TIN KHÁCH HÀNG
# =========================================================

html_markdown(
    '<div class="section-title">'
    "🧾 Thông tin đơn hàng"
    "</div>",
    unsafe_allow_html=True,
)

customer1, customer2, customer3 = st.columns(
    [1, 1.5, 1.5]
)


with customer1:

    table_number = st.text_input(
        "🪑 Số bàn",
        placeholder="VD: B12",
    )


with customer2:

    customer_name = st.text_input(
        "👤 Tên khách hàng",
        placeholder="Nguyễn Văn A",
    )


with customer3:

    customer_phone = st.text_input(
        "📱 Số điện thoại tích điểm",
        placeholder="0901234567",
    )


# =========================================================
# 15. MENU + GIỎ HÀNG
# =========================================================

menu_column, cart_column = st.columns(
    [1.7, 1],
    gap="large",
)


# =========================================================
# 16. MENU
# =========================================================

with menu_column:

    html_markdown(
        '<div class="section-title">'
        "🍣 Chọn món"
        "</div>",
        unsafe_allow_html=True,
    )

    filter1, filter2 = st.columns(
        [1, 2]
    )


    with filter1:

        category = st.selectbox(
            "Danh mục",
            [
                "Tất cả",
                "Sushi",
                "Sashimi",
                "Maki",
                "Món ăn",
                "Combo",
                "Nước uống",
            ],
        )


    with filter2:

        search = st.text_input(
            "🔎 Tìm món",
            placeholder="Nhập tên món...",
        )


    filtered_menu = MENU.copy()


    if category != "Tất cả":

        filtered_menu = [
            item
            for item in filtered_menu
            if item["category"] == category
        ]


    if search.strip():

        filtered_menu = [
            item
            for item in filtered_menu
            if search.lower()
            in item["name"].lower()
        ]


    food_columns = st.columns(2)


    for index, item in enumerate(filtered_menu):

        with food_columns[index % 2]:

            best_badge = ""

            if item["best"]:

                best_badge = (
                    '<span class="best">'
                    "⭐ BEST SELLER"
                    "</span>"
                )


            html_markdown(
                f"""
<div class="food-card">

{best_badge}

<div style="height:8px;"></div>

<div class="food-name">
{item['name']}
</div>

<div class="food-description">
{item['description']}
</div>

<span class="category">
{item['category']}
</span>

<div class="food-price">
{money(item['price'])}
</div>

</div>
""",
                unsafe_allow_html=True,
            )


            current_quantity = (
                st.session_state.cart.get(
                    item["id"],
                    0,
                )
            )


            # Chưa chọn món

            if current_quantity == 0:

                if st.button(
                    "＋  Thêm món",
                    key=f"add_{item['id']}",
                    use_container_width=True,
                ):

                    add_item(
                        item["id"]
                    )

                    st.rerun()


            # Đã chọn món

            else:

                minus_col, qty_col, plus_col = st.columns(
                    [1, 1.2, 1]
                )


                with minus_col:

                    if st.button(
                        "−",
                        key=f"minus_{item['id']}",
                        use_container_width=True,
                    ):

                        remove_item(
                            item["id"]
                        )

                        st.rerun()


                with qty_col:

                    html_markdown(
                        f"""
<div style="
background:#fff3ef;
border:1px solid #efd7d0;
border-radius:11px;
height:42px;
display:flex;
align-items:center;
justify-content:center;
font-size:16px;
font-weight:800;
color:#8f1717;
">
{current_quantity}
</div>
""",
                        unsafe_allow_html=True,
                    )


                with plus_col:

                    if st.button(
                        "＋",
                        key=f"plus_{item['id']}",
                        use_container_width=True,
                    ):

                        add_item(
                            item["id"]
                        )

                        st.rerun()


                # Ghi chú

                note_key = f"note_{item['id']}"

                current_note = (
                    st.session_state.notes.get(
                        item["id"],
                        "",
                    )
                )

                note = st.text_input(
                    "Ghi chú",
                    value=current_note,
                    placeholder="Ít wasabi, không hành...",
                    key=note_key,
                    label_visibility="collapsed",
                )

                st.session_state.notes[
                    item["id"]
                ] = note


# =========================================================
# 17. GIỎ HÀNG
# =========================================================

with cart_column:

    html_markdown(
        '<div class="section-title">'
        "🛒 Đơn hàng"
        "</div>",
        unsafe_allow_html=True,
    )

    html_markdown(
        '<div class="cart-card">',
        unsafe_allow_html=True,
    )


    if not st.session_state.cart:

        html_markdown(
            """
<div style="
text-align:center;
padding:35px 10px;
color:#9b8881;
">

<div style="
font-size:45px;
">
🍣
</div>

<div style="
font-weight:700;
color:#5d4640;
margin-top:8px;
">
Chưa có món
</div>

<div style="
font-size:12px;
margin-top:5px;
">
Chọn món bên trái để bắt đầu order
</div>

</div>
""",
            unsafe_allow_html=True,
        )


    else:

        for item_id, quantity in list(
            st.session_state.cart.items()
        ):

            item = MENU_BY_ID[item_id]

            line_total = (
                item["price"]
                * quantity
            )

            html_markdown(
                f"""
<div class="cart-item">

<div style="
display:flex;
justify-content:space-between;
gap:10px;
">

<div>

<div class="cart-name">
{item['name']}
</div>

<div style="
font-size:11px;
color:#9a8780;
margin-top:3px;
">
{money(item['price'])} × {quantity}
</div>

</div>

<div class="cart-price">
{money(line_total)}
</div>

</div>

</div>
""",
                unsafe_allow_html=True,
            )


        html_markdown("<br>", unsafe_allow_html=True)


        # Voucher

        voucher_code = st.text_input(
            "🎟️ Voucher",
            placeholder="VD: N2WELCOME",
        )


        current_subtotal = subtotal()


        discount, voucher_message = calculate_voucher(
            voucher_code,
            current_subtotal,
        )


        if voucher_message:

            if discount > 0:

                st.success(
                    voucher_message
                )

            else:

                st.warning(
                    voucher_message
                )


        total = max(
            0,
            current_subtotal - discount,
        )


        points = loyalty_points(total)


        # Tổng tiền

        html_markdown(
            f"""
<div style="
display:flex;
justify-content:space-between;
margin-top:15px;
color:#75615a;
font-size:13px;
">

<span>Tạm tính</span>

<b>
{money(current_subtotal)}
</b>

</div>

<div style="
display:flex;
justify-content:space-between;
margin-top:10px;
color:#198754;
font-size:13px;
">

<span>Voucher</span>

<b>
- {money(discount)}
</b>

</div>

<div style="
display:flex;
justify-content:space-between;
margin-top:10px;
color:#75615a;
font-size:13px;
">

<span>Điểm tích lũy</span>

<b>
+{points} điểm
</b>

</div>
""",
            unsafe_allow_html=True,
        )


        html_markdown(
            f"""
<div class="total-card">

<div class="total-label">
TỔNG THANH TOÁN
</div>

<div class="total-number">
{money(total)}
</div>

<div style="
font-size:11px;
opacity:.72;
margin-top:5px;
">
Đã áp dụng ưu đãi nếu có
</div>

</div>
""",
            unsafe_allow_html=True,
        )


        html_markdown("<br>", unsafe_allow_html=True)


        if st.button(
            "🗑️ Xóa toàn bộ món",
            use_container_width=True,
        ):

            st.session_state.cart = {}

            st.session_state.notes = {}

            st.rerun()


        if st.button(
            "💳  THANH TOÁN",
            type="primary",
            use_container_width=True,
        ):

            errors = []


            if not table_number.strip():

                errors.append(
                    "Vui lòng nhập số bàn."
                )


            if not customer_name.strip():

                errors.append(
                    "Vui lòng nhập tên khách hàng."
                )


            if not st.session_state.cart:

                errors.append(
                    "Chưa có món trong đơn hàng."
                )


            if errors:

                for error in errors:

                    st.error(error)


            else:

                invoice_items = []


                for item_id, quantity in (
                    st.session_state.cart.items()
                ):

                    item = MENU_BY_ID[item_id]

                    invoice_items.append(
                        {
                            "name": item["name"],
                            "price": item["price"],
                            "quantity": quantity,
                            "note": st.session_state.notes.get(
                                item_id,
                                "",
                            ),
                            "total": (
                                item["price"]
                                * quantity
                            ),
                        }
                    )


                invoice_number = (
                    "N2-"
                    + datetime.now().strftime(
                        "%Y%m%d-%H%M%S"
                    )
                    + "-"
                    + str(uuid.uuid4())[:4].upper()
                )


                st.session_state.invoice = {
                    "number": invoice_number,
                    "time": datetime.now(),
                    "table": table_number,
                    "customer": customer_name,
                    "phone": customer_phone,
                    "items": invoice_items,
                    "subtotal": current_subtotal,
                    "discount": discount,
                    "total": total,
                    "voucher": voucher_code.upper(),
                    "points": points,
                }


                st.success(
                    "🎉 Thanh toán thành công!"
                )

                st.balloons()


    html_markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# =========================================================
# 18. HÓA ĐƠN
# =========================================================

invoice = st.session_state.invoice


if invoice:

    html_markdown(
        '<div class="section-title">'
        "📄 Hóa đơn vừa thanh toán"
        "</div>",
        unsafe_allow_html=True,
    )


    invoice_left, invoice_right = st.columns(
        [1.5, 1]
    )


    with invoice_left:

        html_markdown(
            f"""
<div class="info-box">

<h3 style="
color:#a51616;
margin-top:0;
">
🍣 N2 SUSHI
</h3>

<div style="
font-size:12px;
color:#75615a;
line-height:1.9;
">

<b>Mã hóa đơn:</b>
{invoice['number']}

<br>

<b>Thời gian:</b>
{invoice['time'].strftime('%d/%m/%Y %H:%M:%S')}

<br>

<b>Số bàn:</b>
{invoice['table']}

<br>

<b>Khách hàng:</b>
{invoice['customer']}

<br>

<b>Số điện thoại:</b>
{invoice['phone'] or '---'}

</div>

<hr>
""",
            unsafe_allow_html=True,
        )


        for item in invoice["items"]:

            note_html = ""

            if item["note"]:

                note_html = (
                    f"""
                    <div style="
                    font-size:10px;
                    color:#9a8780;
                    margin-top:3px;
                    ">
                    📝 {item['note']}
                    </div>
                    """
                )


            html_markdown(
                f"""
<div style="
display:flex;
justify-content:space-between;
padding:10px 0;
border-bottom:1px solid #eee;
">

<div>

<b>
{item['name']}
</b>

<div style="
font-size:11px;
color:#8f7c75;
">
SL: {item['quantity']}
</div>

{note_html}

</div>

<div style="
font-weight:700;
color:#a71919;
">
{money(item['total'])}
</div>

</div>
""",
                unsafe_allow_html=True,
            )


        html_markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    with invoice_right:

        html_markdown(
            f"""
<div class="total-card">

<div class="total-label">
TỔNG THANH TOÁN
</div>

<div class="total-number">
{money(invoice['total'])}
</div>

<div style="
margin-top:15px;
font-size:13px;
line-height:1.8;
opacity:.88;
">

Tạm tính:
{money(invoice['subtotal'])}

<br>

Voucher:
- {money(invoice['discount'])}

<br>

Điểm tích lũy:
+{invoice['points']} điểm

</div>

</div>
""",
            unsafe_allow_html=True,
        )


        html_markdown("<br>", unsafe_allow_html=True)


        # Tạo file hóa đơn CSV

        csv_text = (
            "N2 Sushi\n"
            f"Hóa đơn: {invoice['number']}\n"
            f"Khách hàng: {invoice['customer']}\n"
            f"Số bàn: {invoice['table']}\n"
            f"Số điện thoại: {invoice['phone']}\n"
            f"Thời gian: "
            f"{invoice['time'].strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        )


        csv_text += (
            "Món,Số lượng,Đơn giá,"
            "Thành tiền,Ghi chú\n"
        )


        for item in invoice["items"]:

            csv_text += (
                f"\"{item['name']}\","
                f"{item['quantity']},"
                f"{item['price']},"
                f"{item['total']},"
                f"\"{item['note']}\"\n"
            )


        csv_text += (
            f"\nTạm tính,{invoice['subtotal']}\n"
            f"Giảm voucher,{invoice['discount']}\n"
            f"Tổng thanh toán,{invoice['total']}\n"
            f"Điểm tích lũy,{invoice['points']}\n"
        )


        st.download_button(
            "📥 TẢI HÓA ĐƠN",
            data=csv_text.encode("utf-8-sig"),
            file_name=f"{invoice['number']}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# =========================================================
# 19. FOOTER
# =========================================================

html_markdown(
    """
<div class="footer">

🍣 N2 Sushi

<br>

Premium Japanese Dining • Order & Payment System

</div>
""",
    unsafe_allow_html=True,
)
