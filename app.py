import os
import io
import uuid
from datetime import datetime

import streamlit as st
import requests


# =========================================================
# CẤU HÌNH
# =========================================================

st.set_page_config(
    page_title="N2 Sushi",
    page_icon="🍣",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# THÔNG TIN QUÁN
# =========================================================

RESTAURANT = {
    "name": "N2 Sushi",
    "address": "Địa chỉ N2 Sushi - cập nhật tại đây",
    "phone": "0900 000 000",
    "hours": "10:00 - 22:00 hàng ngày",
}


# =========================================================
# MENU
# =========================================================

MENU = [
    {
        "id": "S01",
        "name": "Sushi cá hồi",
        "category": "Sushi",
        "price": 69000,
        "desc": "Cá hồi tươi, cơm sushi Nhật",
        "best": True,
    },
    {
        "id": "S02",
        "name": "Sushi cá ngừ",
        "category": "Sushi",
        "price": 65000,
        "desc": "Cá ngừ tươi cùng cơm sushi",
        "best": True,
    },
    {
        "id": "S03",
        "name": "Sashimi cá hồi",
        "category": "Sashimi",
        "price": 129000,
        "desc": "Cá hồi tươi cắt lát",
        "best": True,
    },
    {
        "id": "S04",
        "name": "Sashimi tổng hợp",
        "category": "Sashimi",
        "price": 229000,
        "desc": "Tổng hợp nhiều loại sashimi",
        "best": True,
    },
    {
        "id": "S05",
        "name": "Maki cá hồi bơ",
        "category": "Maki",
        "price": 89000,
        "desc": "Cá hồi, bơ và rong biển",
        "best": True,
    },
    {
        "id": "S06",
        "name": "Maki tempura tôm",
        "category": "Maki",
        "price": 99000,
        "desc": "Tôm tempura cuộn maki",
        "best": False,
    },
    {
        "id": "S07",
        "name": "Salmon Aburi",
        "category": "Sushi",
        "price": 109000,
        "desc": "Cá hồi áp lửa kiểu Nhật",
        "best": True,
    },
    {
        "id": "S08",
        "name": "Unagi Sushi",
        "category": "Sushi",
        "price": 119000,
        "desc": "Sushi lươn Nhật",
        "best": False,
    },
    {
        "id": "S09",
        "name": "Gyoza",
        "category": "Món ăn",
        "price": 79000,
        "desc": "Bánh xếp Nhật",
        "best": False,
    },
    {
        "id": "S10",
        "name": "Edamame",
        "category": "Món ăn",
        "price": 49000,
        "desc": "Đậu nành Nhật",
        "best": False,
    },
    {
        "id": "C02",
        "name": "Combo N2 Couple",
        "category": "Combo",
        "price": 299000,
        "desc": "Combo dành cho 2 người",
        "best": True,
    },
    {
        "id": "C03",
        "name": "Combo N2 Family",
        "category": "Combo",
        "price": 429000,
        "desc": "Combo dành cho 3 người",
        "best": True,
    },
    {
        "id": "C45",
        "name": "Combo N2 Party",
        "category": "Combo",
        "price": 649000,
        "desc": "Combo dành cho 4-5 người",
        "best": True,
    },
    {
        "id": "D01",
        "name": "Coca-Cola",
        "category": "Nước uống",
        "price": 25000,
        "desc": "Nước ngọt",
        "best": False,
    },
    {
        "id": "D02",
        "name": "Sprite",
        "category": "Nước uống",
        "price": 25000,
        "desc": "Nước ngọt",
        "best": False,
    },
    {
        "id": "D03",
        "name": "Trà đào",
        "category": "Nước uống",
        "price": 45000,
        "desc": "Trà đào mát lạnh",
        "best": True,
    },
    {
        "id": "D04",
        "name": "Trà xanh Nhật",
        "category": "Nước uống",
        "price": 35000,
        "desc": "Trà xanh Nhật",
        "best": False,
    },
]


MENU_BY_ID = {
    item["id"]: item
    for item in MENU
}


# =========================================================
# VOUCHER
# =========================================================

VOUCHERS = {
    "N2WELCOME": {
        "type": "percent",
        "value": 10,
        "max": 100000,
        "minimum": 200000,
    },
    "N2SAVE50": {
        "type": "fixed",
        "value": 50000,
        "max": 50000,
        "minimum": 300000,
    },
    "N2VIP": {
        "type": "percent",
        "value": 15,
        "max": 150000,
        "minimum": 500000,
    },
}


# =========================================================
# SESSION STATE
# =========================================================

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "notes" not in st.session_state:
    st.session_state.notes = {}

if "chat" not in st.session_state:
    st.session_state.chat = []

if "invoice" not in st.session_state:
    st.session_state.invoice = None


# =========================================================
# HELPER
# =========================================================

def money(number):
    return f"{int(number):,}".replace(",", ".") + " ₫"


def add_item(item_id):
    if item_id not in st.session_state.cart:
        st.session_state.cart[item_id] = 1
    else:
        st.session_state.cart[item_id] += 1


def remove_item(item_id):
    if item_id in st.session_state.cart:

        st.session_state.cart[item_id] -= 1

        if st.session_state.cart[item_id] <= 0:
            del st.session_state.cart[item_id]

            if item_id in st.session_state.notes:
                del st.session_state.notes[item_id]


def clear_cart():
    st.session_state.cart = {}
    st.session_state.notes = {}


def get_subtotal():
    total = 0

    for item_id, quantity in st.session_state.cart.items():

        item = MENU_BY_ID[item_id]

        total += item["price"] * quantity

    return total


def calculate_discount(subtotal, voucher):

    code = voucher.strip().upper()

    if not code:
        return 0, ""

    if code not in VOUCHERS:
        return 0, "❌ Voucher không tồn tại."

    data = VOUCHERS[code]

    if subtotal < data["minimum"]:
        return (
            0,
            f"❌ Đơn tối thiểu {money(data['minimum'])}.",
        )

    if data["type"] == "percent":

        discount = (
            subtotal
            * data["value"]
            / 100
        )

    else:

        discount = data["value"]

    discount = min(
        discount,
        data["max"],
        subtotal,
    )

    return (
        discount,
        f"✓ Đã áp dụng {code}: giảm {money(discount)}",
    )


def get_points(total):
    return int(total // 10000)


# =========================================================
# CHATBOT
# =========================================================

def local_answer(question):

    q = question.lower()

    if "best seller" in q or "bán chạy" in q:

        names = [
            item["name"]
            for item in MENU
            if item["best"]
        ]

        return (
            "⭐ **Best seller của N2 Sushi:**\n\n"
            + "\n".join(
                f"- {name}"
                for name in names
            )
        )

    if "2 người" in q:

        return (
            "👫 **Combo dành cho 2 người**\n\n"
            "Combo N2 Couple — **299.000đ**"
        )

    if "3 người" in q:

        return (
            "👨‍👩‍👧 **Combo dành cho 3 người**\n\n"
            "Combo N2 Family — **429.000đ**"
        )

    if (
        "4-5" in q
        or "4 5" in q
        or "4 người" in q
        or "5 người" in q
    ):

        return (
            "👨‍👩‍👧‍👦 **Combo dành cho 4-5 người**\n\n"
            "Combo N2 Party — **649.000đ**"
        )

    if (
        "khuyến mãi" in q
        or "khuyen mai" in q
        or "voucher" in q
        or "ưu đãi" in q
    ):

        return (
            "🎁 **Các ưu đãi hiện có:**\n\n"
            "- N2WELCOME: giảm 10%, tối đa 100.000đ\n"
            "- N2SAVE50: giảm 50.000đ\n"
            "- N2VIP: giảm 15%, tối đa 150.000đ"
        )

    if (
        "địa chỉ" in q
        or "dia chi" in q
        or "ở đâu" in q
    ):

        return (
            f"📍 **Địa chỉ N2 Sushi:**\n\n"
            f"{RESTAURANT['address']}"
        )

    if (
        "giờ" in q
        or "gio" in q
        or "mở cửa" in q
    ):

        return (
            f"🕐 **Giờ mở cửa:**\n\n"
            f"{RESTAURANT['hours']}"
        )

    return (
        "Xin chào 👋 Mình là trợ lý N2 Sushi.\n\n"
        "Bạn có thể hỏi mình về:\n"
        "- Best seller\n"
        "- Combo 2 / 3 / 4-5 người\n"
        "- Khuyến mãi\n"
        "- Voucher\n"
        "- Địa chỉ\n"
        "- Giờ mở cửa"
    )


def ask_ai(question):

    api_key = os.getenv(
        "OPENROUTER_API_KEY",
        ""
    )

    if not api_key:
        return local_answer(question)

    menu_text = "\n".join(
        f"- {item['name']}: {money(item['price'])}"
        for item in MENU
    )

    prompt = f"""
Bạn là chatbot chính thức của N2 Sushi.

Tên quán: N2 Sushi
Địa chỉ: {RESTAURANT['address']}
Giờ mở cửa: {RESTAURANT['hours']}

MENU:
{menu_text}

Combo:
- Combo N2 Couple: 299.000đ - 2 người
- Combo N2 Family: 429.000đ - 3 người
- Combo N2 Party: 649.000đ - 4-5 người

Voucher:
- N2WELCOME: giảm 10%, tối đa 100.000đ
- N2SAVE50: giảm 50.000đ
- N2VIP: giảm 15%, tối đa 150.000đ

Hãy trả lời tiếng Việt.
Không được tự bịa thông tin.
Trả lời ngắn gọn, thân thiện.

Câu hỏi:
{question}
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
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0.2,
            },
            timeout=30,
        )

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception:

        return local_answer(question)


# =========================================================
# CSS
# =========================================================

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
        linear-gradient(
            135deg,
            #fffaf7 0%,
            #ffffff 50%,
            #fff6f1 100%
        );
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #21120f,
            #120b09
        );
}

section[data-testid="stSidebar"] * {
    color: #fff !important;
}

.hero {
    background:
        linear-gradient(
            135deg,
            #270b08,
            #8f1717,
            #c72d2d
        );
    border-radius: 28px;
    padding: 38px 42px;
    color: white;
    box-shadow:
        0 18px 45px rgba(90,20,10,.20);
    margin-bottom: 22px;
}

.hero-small {
    font-size: 11px;
    letter-spacing: 4px;
    opacity: .7;
}

.hero-title {
    font-size: 48px;
    font-weight: 800;
    margin: 5px 0;
}

.hero-subtitle {
    font-size: 14px;
    opacity: .82;
}

.info-box {
    background: white;
    border: 1px solid #f0e0da;
    border-radius: 18px;
    padding: 18px;
    box-shadow:
        0 7px 25px rgba(70,20,10,.05);
}

.info-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #9c8982;
}

.info-value {
    color: #32130f;
    font-size: 18px;
    font-weight: 800;
    margin-top: 5px;
}

.section-title {
    color: #35130f;
    font-size: 25px;
    font-weight: 800;
    margin: 25px 0 15px;
}

.food-card {
    background: white;
    border: 1px solid #eee0da;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 15px;
    min-height: 225px;
    box-shadow:
        0 8px 25px rgba(80,20,10,.055);
}

.food-card:hover {
    border-color: #d99a8d;
    box-shadow:
        0 12px 30px rgba(120,30,15,.10);
}

.food-name {
    font-size: 17px;
    font-weight: 800;
    color: #30120e;
}

.food-description {
    color: #95817a;
    font-size: 12px;
    min-height: 37px;
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

.cart-card {
    background: white;
    border: 1px solid #eee0da;
    border-radius: 22px;
    padding: 22px;
    box-shadow:
        0 10px 35px rgba(80,20,10,.07);
}

.cart-item {
    padding: 14px 0;
    border-bottom: 1px solid #eee5e1;
}

.cart-name {
    color: #35130f;
    font-weight: 800;
}

.cart-price {
    color: #b21c1c;
    font-weight: 800;
}

.qty-box {
    background: #fff5f1;
    border-radius: 12px;
    padding: 3px;
}

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
        0 15px 35px rgba(140,20,20,.23);
}

.total-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    opacity: .7;
}

.total-number {
    font-size: 36px;
    font-weight: 800;
    margin-top: 4px;
}

.stButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    border: 1px solid #eadbd5 !important;
}

.stButton > button:hover {
    border-color: #bd3830 !important;
}

button[kind="primary"] {
    background:
        linear-gradient(
            135deg,
            #991414,
            #cf2e2e
        ) !important;
    border: none !important;
    color: white !important;
}

div[data-testid="stTextInput"] input {
    border-radius: 12px;
}

.footer {
    text-align: center;
    color: #a18d86;
    font-size: 11px;
    padding: 35px 0 15px;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
<div class="hero">

    <div class="hero-small">
        JAPANESE CUISINE
    </div>

    <div class="hero-title">
        N2 Sushi
    </div>

    <div class="hero-subtitle">
        Premium Sushi • Sashimi • Japanese Dining
    </div>

</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# ẢNH QUÁN
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
        "Chưa tìm thấy sushi.jpg. "
        "Hãy đặt file sushi.jpg cùng thư mục với app.py."
    )


# =========================================================
# THÔNG TIN NHANH
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

i1, i2, i3, i4 = st.columns(4)

with i1:

    st.markdown(
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
{RESTAURANT['address']}
</div>

</div>
""",
        unsafe_allow_html=True,
    )

with i2:

    st.markdown(
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

with i3:

    st.markdown(
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

with i4:

    st.markdown(
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
# SIDEBAR CHATBOT
# =========================================================

with st.sidebar:

    st.markdown(
        """
<div style="
text-align:center;
padding:10px 0 20px;
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
Trợ lý N2 Sushi
</div>

</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    for message in st.session_state.chat:

        if message["role"] == "user":

            st.markdown(
                f"""
<div style="
background:#a31c1c;
padding:10px 12px;
border-radius:14px;
margin:8px 0;
font-size:13px;
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
background:#3a2521;
padding:10px 12px;
border-radius:14px;
margin:8px 0;
font-size:13px;
">
<b>🍣 N2</b><br>
{message["content"]}
</div>
""",
                unsafe_allow_html=True,
            )

    chat = st.chat_input(
        "Hỏi N2 Sushi..."
    )

    if chat:

        st.session_state.chat.append(
            {
                "role": "user",
                "content": chat,
            }
        )

        answer = ask_ai(chat)

        st.session_state.chat.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()

    if st.button(
        "🗑️ Xóa chat",
        use_container_width=True,
    ):

        st.session_state.chat = []

        st.rerun()


# =========================================================
# THÔNG TIN KHÁCH
# =========================================================

st.markdown(
    '<div class="section-title">'
    "🧾 Thông tin đơn hàng"
    "</div>",
    unsafe_allow_html=True,
)

customer_col1, customer_col2, customer_col3 = st.columns(
    [1, 1.5, 1.5]
)

with customer_col1:

    table_number = st.text_input(
        "🪑 Số bàn",
        placeholder="VD: B12",
    )

with customer_col2:

    customer_name = st.text_input(
        "👤 Tên khách hàng",
        placeholder="Nguyễn Văn A",
    )

with customer_col3:

    phone = st.text_input(
        "📱 Số điện thoại tích điểm",
        placeholder="0901234567",
    )


# =========================================================
# MENU + CART
# =========================================================

menu_col, cart_col = st.columns(
    [1.7, 1],
    gap="large",
)


# =========================================================
# MENU
# =========================================================

with menu_col:

    st.markdown(
        '<div class="section-title">'
        "🍣 Chọn món"
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
                "Sushi",
                "Sashimi",
                "Maki",
                "Món ăn",
                "Combo",
                "Nước uống",
            ],
        )

    with search_col:

        search = st.text_input(
            "🔎 Tìm món",
            placeholder="Tìm sushi, sashimi, combo...",
        )


    filtered_menu = MENU.copy()

    if category != "Tất cả":

        filtered_menu = [
            item
            for item in filtered_menu
            if item["category"] == category
        ]

    if search:

        filtered_menu = [
            item
            for item in filtered_menu
            if search.lower()
            in item["name"].lower()
        ]


    # 2 CỘT MÓN

    food_columns = st.columns(2)

    for index, item in enumerate(filtered_menu):

        with food_columns[index % 2]:

            best_html = ""

            if item["best"]:

                best_html = (
                    '<span class="best">'
                    "⭐ BEST SELLER"
                    "</span>"
                )

            st.markdown(
                f"""
<div class="food-card">

{best_html}

<div style="height:8px;"></div>

<div class="food-name">
{item['name']}
</div>

<div class="food-description">
{item['desc']}
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


            # NÚT THÊM

            current_qty = st.session_state.cart.get(
                item["id"],
                0,
            )

            if current_qty == 0:

                if st.button(
                    "＋  Thêm món",
                    key=f"add_{item['id']}",
                    use_container_width=True,
                ):

                    add_item(item["id"])

                    st.rerun()

            else:

                minus, quantity, plus = st.columns(
                    [1, 1.2, 1]
                )

                with minus:

                    if st.button(
                        "−",
                        key=f"minus_{item['id']}",
                        use_container_width=True,
                    ):

                        remove_item(item["id"])

                        st.rerun()

                with quantity:

                    st.markdown(
                        f"""
<div style="
background:#fff3ef;
border:1px solid #efd7d0;
border-radius:11px;
height:43px;
display:flex;
align-items:center;
justify-content:center;
font-size:16px;
font-weight:800;
color:#8f1717;
">
{current_qty}
</div>
""",
                        unsafe_allow_html=True,
                    )

                with plus:

                    if st.button(
                        "＋",
                        key=f"plus_{item['id']}",
                        use_container_width=True,
                    ):

                        add_item(item["id"])

                        st.rerun()


            # GHI CHÚ

            if current_qty > 0:

                note_value = st.session_state.notes.get(
                    item["id"],
                    "",
                )

                note = st.text_input(
                    "📝 Ghi chú",
                    value=note_value,
                    placeholder="Ít wasabi, không hành...",
                    key=f"note_{item['id']}",
                    label_visibility="collapsed",
                )

                st.session_state.notes[item["id"]] = note


# =========================================================
# CART
# =========================================================

with cart_col:

    st.markdown(
        '<div class="section-title">'
        "🛒 Đơn hàng"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="cart-card">',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:

        st.markdown(
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

            st.markdown(
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


        st.markdown("<br>", unsafe_allow_html=True)


        # VOUCHER

        voucher = st.text_input(
            "🎟️ Voucher",
            placeholder="VD: N2WELCOME",
        )

        subtotal = get_subtotal()

        discount, voucher_message = calculate_discount(
            subtotal,
            voucher,
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
            subtotal - discount,
        )

        points = get_points(total)


        # SUMMARY

        st.markdown(
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
{money(subtotal)}
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


        st.markdown(
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
opacity:.7;
margin-top:5px;
">
Đã bao gồm ưu đãi nếu có
</div>

</div>
""",
            unsafe_allow_html=True,
        )


        st.markdown("<br>", unsafe_allow_html=True)


        if st.button(
            "🗑️ Xóa toàn bộ món",
            use_container_width=True,
        ):

            clear_cart()

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


                st.session_state.invoice = {
                    "number": (
                        "N2-"
                        + datetime.now().strftime(
                            "%Y%m%d-%H%M%S"
                        )
                        + "-"
                        + str(uuid.uuid4())[:4].upper()
                    ),
                    "time": datetime.now(),
                    "table": table_number,
                    "customer": customer_name,
                    "phone": phone,
                    "items": invoice_items,
                    "subtotal": subtotal,
                    "discount": discount,
                    "total": total,
                    "voucher": voucher.upper(),
                    "points": points,
                }

                st.success(
                    "🎉 Thanh toán thành công!"
                )

                st.balloons()


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# =========================================================
# HÓA ĐƠN
# =========================================================

invoice = st.session_state.invoice

if invoice:

    st.markdown(
        '<div class="section-title">'
        "📄 Hóa đơn vừa thanh toán"
        "</div>",
        unsafe_allow_html=True,
    )

    invoice_left, invoice_right = st.columns(
        [1.5, 1]
    )

    with invoice_left:

        st.markdown(
            f"""
<div class="info-box">

<h3 style="
color:#a51616;
margin-top:0;
">
N2 SUSHI
</h3>

<div style="
font-size:12px;
color:#75615a;
line-height:1.8;
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

            st.markdown(
                f"""
<div style="
display:flex;
justify-content:space-between;
padding:10px 0;
border-bottom:1px solid #eee;
">

<div>
<b>{item['name']}</b>

<div style="
font-size:11px;
color:#8f7c75;
">
SL: {item['quantity']}
</div>

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

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    with invoice_right:

        st.markdown(
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
opacity:.85;
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

        st.markdown("<br>", unsafe_allow_html=True)

        # Xuất CSV thay vì bảng code/PDF bắt buộc

        csv_text = (
            "N2 Sushi\n"
            f"Hóa đơn: {invoice['number']}\n"
            f"Khách hàng: {invoice['customer']}\n"
            f"Bàn: {invoice['table']}\n"
            f"Thời gian: "
            f"{invoice['time'].strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        )

        csv_text += (
            "Món,Số lượng,Đơn giá,Thành tiền,Ghi chú\n"
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
            "📥 Tải hóa đơn",
            data=csv_text.encode("utf-8-sig"),
            file_name=f"{invoice['number']}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
<div class="footer">
🍣 N2 Sushi • Japanese Premium Dining
<br>
Order & Payment System
</div>
""",
    unsafe_allow_html=True,
)
