import os
import textwrap
import uuid
import sqlite3
import unicodedata
import html
from datetime import datetime

import requests
import streamlit as st


# =========================================================
# HÀM RENDER HTML AN TOÀN
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
RESTAURANT_ADDRESS = "Số 8 đường Nguyễn Huệ Thành Phố Hồ Chí Minh"
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
# 4. DATABASE SQLITE
# =========================================================

DB_PATH = os.getenv("N2_DATABASE_PATH", "n2_sushi.db")


def get_db_connection():
    """Mở kết nối SQLite."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Tạo bảng database và đồng bộ menu."""
    with get_db_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS menu_items (
                item_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                best_seller INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,
                loyalty_points INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                table_number TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                subtotal INTEGER NOT NULL,
                discount INTEGER NOT NULL,
                total INTEGER NOT NULL,
                voucher TEXT,
                points_earned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL,
                item_id TEXT,
                item_name TEXT NOT NULL,
                unit_price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                note TEXT,
                line_total INTEGER NOT NULL,
                FOREIGN KEY(invoice_number)
                    REFERENCES orders(invoice_number)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_logs (
                chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_orders_phone
            ON orders(customer_phone);

            CREATE INDEX IF NOT EXISTS idx_chat_session
            ON chat_logs(session_id, chat_id);
        """)

        now = datetime.now().isoformat(timespec="seconds")

        for item in MENU:
            conn.execute("""
                INSERT INTO menu_items (
                    item_id, name, category, price,
                    description, best_seller, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    name = excluded.name,
                    category = excluded.category,
                    price = excluded.price,
                    description = excluded.description,
                    best_seller = excluded.best_seller,
                    updated_at = excluded.updated_at
            """, (
                item["id"],
                item["name"],
                item["category"],
                item["price"],
                item["description"],
                int(item["best"]),
                now,
            ))


def save_chat_message(session_id, role, content):
    """Lưu tin nhắn chatbot vào database."""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO chat_logs (
                    session_id, role, content, created_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                role,
                str(content),
                datetime.now().isoformat(timespec="seconds"),
            ))
    except sqlite3.Error as exc:
        print(f"Không thể lưu lịch sử chatbot: {exc}")


def save_order_to_database(invoice):
    """Lưu hóa đơn, chi tiết món và điểm khách hàng."""
    now = invoice["time"].isoformat(timespec="seconds")
    phone = (invoice.get("phone") or "").strip() or None

    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO orders (
                invoice_number, table_number, customer_name,
                customer_phone, subtotal, discount, total,
                voucher, points_earned, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice["number"],
            invoice["table"],
            invoice["customer"],
            phone,
            invoice["subtotal"],
            invoice["discount"],
            invoice["total"],
            invoice.get("voucher", ""),
            invoice["points"],
            now,
        ))

        for item in invoice["items"]:
            item_id = next(
                (
                    menu_item["id"]
                    for menu_item in MENU
                    if menu_item["name"] == item["name"]
                ),
                None,
            )

            conn.execute("""
                INSERT INTO order_items (
                    invoice_number, item_id, item_name,
                    unit_price, quantity, note, line_total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice["number"],
                item_id,
                item["name"],
                item["price"],
                item["quantity"],
                item.get("note", ""),
                item["total"],
            ))

        if phone:
            existing_customer = conn.execute(
                "SELECT customer_id FROM customers WHERE phone = ?",
                (phone,),
            ).fetchone()

            if existing_customer:
                conn.execute("""
                    UPDATE customers
                    SET name = ?,
                        loyalty_points = loyalty_points + ?,
                        updated_at = ?
                    WHERE phone = ?
                """, (
                    invoice["customer"],
                    invoice["points"],
                    now,
                    phone,
                ))
            else:
                conn.execute("""
                    INSERT INTO customers (
                        name, phone, loyalty_points,
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    invoice["customer"],
                    phone,
                    invoice["points"],
                    now,
                    now,
                ))


# Khởi tạo database
init_database()
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

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())


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
        st.session_state.notes.pop(item_id, None)


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
        return 0, f"Đơn hàng tối thiểu {money(voucher['minimum'])}."

    if voucher["type"] == "percent":
        discount = amount * voucher["value"] / 100
    else:
        discount = voucher["value"]

    discount = min(
        discount,
        voucher["max_discount"],
        amount,
    )

    return discount, f"Đã áp dụng {code}: giảm {money(discount)}."


def loyalty_points(amount):
    return int(amount // 10000)


# =========================================================
# 7. CHATBOT LOCAL
# =========================================================

def normalize_text(value):
    """Chuẩn hóa chữ thường và bỏ dấu tiếng Việt."""
    value = str(value or "").lower().strip()
    value = unicodedata.normalize("NFD", value)

    return "".join(
        ch for ch in value
        if unicodedata.category(ch) != "Mn"
    ).replace("đ", "d")


def find_menu_matches(question):
    q = normalize_text(question)
    matches = []

    for item in MENU:
        name = normalize_text(item["name"])
        words = [w for w in name.split() if len(w) > 2]

        if name in q or (
            words
            and sum(w in q for w in words) >= max(1, len(words) - 1)
        ):
            matches.append(item)

    return matches


def local_chatbot(question):
    """Chatbot dự phòng khi chưa cấu hình API AI."""
    q = normalize_text(question)

    if any(k in q for k in [
        "xin chao", "hello", "hi ", "chao ban", "hey"
    ]):
        return (
            "Xin chào 👋 Mình là N2 Assistant. "
            "Bạn muốn xem menu, tìm món, hỏi combo, voucher "
            "hay thông tin quán nè?"
        )

    if any(k in q for k in [
        "best seller", "best-seller", "ban chay",
        "mon hot", "mon duoc yeu thich"
    ]):
        names = [
            f"- {x['name']} — {money(x['price'])}"
            for x in MENU if x["best"]
        ]
        return "⭐ **Best seller của N2 Sushi:**\n\n" + "\n".join(names)

    if any(k in q for k in [
        "voucher", "khuyen mai", "uu dai", "giam gia", "ma giam"
    ]):
        return (
            "🎁 **Voucher hiện có:**\n\n"
            "- **N2WELCOME:** giảm 10%, tối đa 100.000đ, "
            "đơn tối thiểu 200.000đ.\n"
            "- **N2SAVE50:** giảm 50.000đ, "
            "đơn tối thiểu 300.000đ.\n"
            "- **N2VIP:** giảm 15%, tối đa 150.000đ, "
            "đơn tối thiểu 500.000đ."
        )

    if any(k in q for k in [
        "dia chi", "o dau", "dia diem", "duong nao"
    ]):
        return f"📍 **Địa chỉ N2 Sushi:**\n\n{RESTAURANT_ADDRESS}"

    if any(k in q for k in [
        "gio mo cua", "mo cua", "dong cua",
        "may gio", "thoi gian hoat dong"
    ]):
        return f"🕐 **Giờ mở cửa:**\n\n{RESTAURANT_HOURS}"

    if any(k in q for k in [
        "so dien thoai", "hotline", "lien he", "sdt"
    ]):
        return f"📞 **Hotline N2 Sushi:**\n\n{RESTAURANT_PHONE}"

    if any(k in q for k in [
        "2 nguoi", "hai nguoi", "cap doi"
    ]):
        return (
            "👫 **Combo N2 Couple — 299.000đ**, dành cho 2 người. "
            "Bạn có thể gọi thêm nước uống tùy sở thích nha."
        )

    if any(k in q for k in ["3 nguoi", "ba nguoi"]):
        return "👨‍👩‍👧 **Combo N2 Family — 429.000đ**, dành cho 3 người."

    if any(k in q for k in [
        "4-5 nguoi", "4 5 nguoi", "4 nguoi",
        "5 nguoi", "nhom dong"
    ]):
        return (
            "👨‍👩‍👧‍👦 **Combo N2 Party — 649.000đ**, "
            "dành cho 4–5 người."
        )

    matches = find_menu_matches(question)

    if matches:
        lines = [
            f"- **{m['name']}** ({m['category']}): "
            f"{money(m['price'])} — {m['description']}."
            for m in matches[:5]
        ]

        return (
            "🍣 Mình tìm thấy món này trong menu N2 Sushi nè:\n\n"
            + "\n".join(lines)
        )

    if any(k in q for k in [
        "menu", "co mon gi", "mon an", "thuc don", "gia mon"
    ]):
        categories = {}

        for item in MENU:
            categories.setdefault(item["category"], []).append(item)

        lines = []

        for category, items in categories.items():
            lines.append(
                f"**{category}:** "
                + ", ".join(
                    f"{x['name']} ({money(x['price'])})"
                    for x in items
                )
            )

        return "📋 **Menu N2 Sushi theo danh mục:**\n\n" + "\n\n".join(lines)

    return (
        "Mình có thể giúp bạn xem menu/giá món, gợi ý combo theo số người, "
        "kiểm tra voucher, hoặc cung cấp địa chỉ và giờ mở cửa. "
        "Bạn thử hỏi cụ thể hơn nha 😊"
    )


def ask_chatbot(question):
    """Gọi AI qua OpenRouter; nếu lỗi thì dùng chatbot local."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if not api_key:
        return local_chatbot(question)

    menu_text = "\n".join(
        f"{item['name']} | danh mục: {item['category']} | "
        f"giá: {money(item['price'])} | "
        f"mô tả: {item['description']} | "
        f"best seller: {'có' if item['best'] else 'không'}"
        for item in MENU
    )

    voucher_text = "\n".join(
        f"{code}: giảm {v['value']}"
        f"{'%' if v['type'] == 'percent' else 'đ'}, "
        f"tối đa {money(v['max_discount'])}, "
        f"đơn tối thiểu {money(v['minimum'])}"
        for code, v in VOUCHERS.items()
    )

    system_prompt = f"""
Bạn là trợ lý AI chính thức của N2 Sushi.
Trả lời bằng tiếng Việt tự nhiên, thân thiện và ngắn gọn.

THÔNG TIN QUÁN:
Tên: {RESTAURANT_NAME}
Địa chỉ: {RESTAURANT_ADDRESS}
Điện thoại: {RESTAURANT_PHONE}
Giờ mở cửa: {RESTAURANT_HOURS}

MENU:
{menu_text}

VOUCHER:
{voucher_text}

QUY TẮC:
- Chỉ khẳng định giá, thành phần, ưu đãi và thông tin có trong dữ liệu.
- Combo N2 Couple 299.000đ cho 2 người.
- Combo N2 Family 429.000đ cho 3 người.
- Combo N2 Party 649.000đ cho 4–5 người.
- Khi gợi ý món, cân nhắc số người, ngân sách và sở thích.
- Hiểu câu hỏi tiếp nối dựa trên lịch sử hội thoại.
- Không bịa thông tin về đơn hàng hoặc dữ liệu khách hàng.
- Nếu chưa có thông tin, hãy nói rõ và hướng khách liên hệ nhân viên.
"""

    history = []

    for message in st.session_state.get("chat_messages", [])[-8:]:
        role = (
            "assistant"
            if message.get("role") == "assistant"
            else "user"
        )

        history.append({
            "role": role,
            "content": str(message.get("content", ""))[:2000],
        })

    if not history or history[-1].get("content") != question:
        history.append({"role": "user", "content": question})

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv(
                    "OPENROUTER_MODEL",
                    "openai/gpt-4o-mini",
                ),
                "messages": [
                    {"role": "system", "content": system_prompt}
                ] + history,
                "temperature": 0.35,
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        if isinstance(answer, str) and answer.strip():
            return answer.strip()

        return local_chatbot(question)

    except Exception as exc:
        print(f"Chatbot AI lỗi, chuyển sang chế độ local: {exc}")
        return local_chatbot(question)


# =========================================================
# 8. CSS
# =========================================================
# =========================================================
# 8. CSS
# =========================================================

html_markdown(
    """
<style>
    .stApp {
        background: linear-gradient(135deg, #fff8f3 0%, #f5f1f7 100%);
        color: #39313a;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #40353c 0%, #29252c 100%);
    }

    [data-testid="stSidebar"] * {
        color: #f9f2f3;
    }

    .main-title {
        font-size: 42px;
        font-weight: 900;
        color: #6c3540;
        letter-spacing: -1px;
        margin-bottom: 5px;
    }

    .main-subtitle {
        color: #87717a;
        font-size: 15px;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 27px;
        font-weight: 850;
        color: #593d43;
        margin: 20px 0 16px 0;
    }

    .info-card {
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid #eadde0;
        border-radius: 20px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 5px 18px rgba(70, 40, 50, 0.05);
    }

    .info-label {
        font-size: 12px;
        font-weight: 800;
        color: #a0878d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .info-value {
        font-size: 25px;
        font-weight: 900;
        color: #593d43;
        margin-top: 8px;
    }

    .menu-card {
        background: #ffffff;
        border: 1px solid #eadde0;
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(70, 40, 50, 0.04);
    }

    .menu-name {
        font-size: 17px;
        font-weight: 800;
        color: #53363e;
    }

    .menu-description {
        font-size: 13px;
        color: #8c777d;
        margin-top: 5px;
    }

    .menu-price {
        font-size: 19px;
        font-weight: 900;
        color: #b04c58;
        margin-top: 10px;
    }

    .menu-category {
        display: inline-block;
        background: #f9e8eb;
        color: #a64a58;
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .chat-user {
        background: #a8434d;
        color: #ffffff;
        border-radius: 18px 18px 4px 18px;
        padding: 13px 15px;
        margin: 12px 0 12px 24px;
        font-size: 14px;
        overflow-wrap: anywhere;
    }

    .chat-bot {
        background: #51454c;
        color: #ffffff;
        border: 1px solid #66565e;
        border-radius: 18px 18px 18px 4px;
        padding: 13px 15px;
        margin: 12px 16px 12px 0;
        font-size: 14px;
        overflow-wrap: anywhere;
    }

    .chat-user b,
    .chat-bot b {
        display: inline-block;
        margin-bottom: 7px;
    }

    .cart-card {
        background: #ffffff;
        border: 1px solid #eadde0;
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .cart-total {
        background: linear-gradient(135deg, #773c49, #a94c59);
        color: white;
        border-radius: 18px;
        padding: 22px;
        margin-top: 16px;
    }

    .cart-total-label {
        font-size: 13px;
        opacity: 0.85;
    }

    .cart-total-value {
        font-size: 30px;
        font-weight: 900;
        margin-top: 8px;
    }

    .invoice-box {
        background: #ffffff;
        border: 1px solid #eadde0;
        border-radius: 20px;
        padding:
        # =========================================================
# 10. HEADER
# =========================================================

html_markdown(
    """
<div class="hero">
    <div class="hero-small">JAPANESE CUISINE</div>
    <div class="hero-title">🍣 N2 Sushi</div>
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
    image_left, image_center, image_right = st.columns([1, 2, 1])

    with image_center:
        st.image("sushi.jpg", width="stretch")
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
    <div class="info-label">ĐỊA CHỈ</div>
    <div class="info-value">📍 N2 Sushi</div>
    <div style="font-size:11px;color:#8f7b74;margin-top:5px;">
        {html.escape(RESTAURANT_ADDRESS)}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

with info2:
    html_markdown(
        """
<div class="info-box">
    <div class="info-label">GIỜ MỞ CỬA</div>
    <div class="info-value">🕐 10:00 - 22:00</div>
    <div style="font-size:11px;color:#8f7b74;margin-top:5px;">
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
    <div class="info-label">BEST SELLER</div>
    <div class="info-value">⭐ Sushi & Sashimi</div>
    <div style="font-size:11px;color:#8f7b74;margin-top:5px;">
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
    <div class="info-label">TÍCH ĐIỂM</div>
    <div class="info-value">🎁 1 điểm / 10.000đ</div>
    <div style="font-size:11px;color:#8f7b74;margin-top:5px;">
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
<div style="text-align:center;padding:10px 0 18px;">
    <div style="font-size:42px;">🍣</div>
    <div style="font-size:23px;font-weight:800;color:#ffffff;">
        N2 Assistant
    </div>
    <div style="font-size:11px;color:#c9aaa1;margin-top:4px;">
        Trợ lý N2 Sushi
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    for message in st.session_state.chat_messages:
        safe_chat_content = html.escape(
            str(message.get("content", ""))
        ).replace("\n", "<br>")

        if message.get("role") == "user":
            html_markdown(
                f"""
<div class="chat-user">
    <b>Bạn</b><br>
    {safe_chat_content}
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            html_markdown(
                f"""
<div class="chat-bot">
    <b>🍣 N2 Sushi</b><br>
    {safe_chat_content}
</div>
""",
                unsafe_allow_html=True,
            )

    user_question = st.chat_input("Hỏi N2 Sushi...")

    if user_question:
        st.session_state.chat_messages.append(
            {"role": "user", "content": user_question}
        )

        save_chat_message(
            st.session_state.chat_session_id,
            "user",
            user_question,
        )

        answer = ask_chatbot(user_question)

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": answer}
        )

        save_chat_message(
            st.session_state.chat_session_id,
            "assistant",
            answer,
        )

        st.rerun()

    if st.button("🗑️ Xóa cuộc trò chuyện", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()


# =========================================================
# 14. THÔNG TIN KHÁCH HÀNG
# =========================================================

html_markdown(
    '<div class="section-title">🧾 Thông tin đơn hàng</div>',
    unsafe_allow_html=True,
)

customer1, customer2, customer3 = st.columns([1, 1.5, 1.5])

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

menu_column, cart_column = st.columns([1.7, 1], gap="large")
# =========================================================
# 15. MENU + GIỎ HÀNG
# =========================================================

with menu_column:
    html_markdown(
        '<div class="section-title">🍱 Thực đơn</div>',
        unsafe_allow_html=True,
    )

    categories = ["Tất cả"] + list(dict.fromkeys(
        item["category"] for item in MENU
    ))

    selected_category = st.selectbox(
        "Chọn danh mục",
        categories,
        key="menu_category_filter",
    )

    search_menu = st.text_input(
        "🔎 Tìm món ăn",
        placeholder="Nhập tên món bạn muốn tìm...",
        key="menu_search",
    )

    filtered_menu = MENU

    if selected_category != "Tất cả":
        filtered_menu = [
            item for item in filtered_menu
            if item["category"] == selected_category
        ]

    if search_menu.strip():
        keyword = normalize_text(search_menu)
        filtered_menu = [
            item for item in filtered_menu
            if keyword in normalize_text(item["name"])
            or keyword in normalize_text(item["description"])
        ]

    if not filtered_menu:
        st.info("Không tìm thấy món phù hợp.")

    for item in filtered_menu:
        with st.container(border=True):
            if item["best"]:
                st.caption("⭐ BEST SELLER")

            st.subheader(item["name"])
            st.caption(item["category"])
            st.write(item["description"])
            st.markdown(f"### {money(item['price'])}")

            if st.button(
                "➕ Thêm vào giỏ",
                key=f"add_{item['id']}",
                use_container_width=True,
                type="primary",
            ):
                add_item(item["id"])
                st.rerun()


# =========================================================
# 16. GIỎ HÀNG
# =========================================================

with cart_column:
    html_markdown(
        '<div class="section-title">🛒 Giỏ hàng</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:
        st.info("Giỏ hàng đang trống. Hãy chọn món ở bên trái.")
    else:
        for item_id in list(st.session_state.cart.keys()):
            item = MENU_BY_ID[item_id]
            quantity = st.session_state.cart[item_id]

            with st.container(border=True):
                st.markdown(f"**{item['name']}**")
                st.caption(
                    f"{money(item['price'])} × {quantity} "
                    f"= {money(item['price'] * quantity)}"
                )

                minus_col, qty_col, plus_col = st.columns([1, 1, 1])

                with minus_col:
                    if st.button(
                        "➖",
                        key=f"minus_{item_id}",
                        use_container_width=True,
                    ):
                        remove_item(item_id)
                        st.rerun()

                with qty_col:
                    st.markdown(
                        f"<div style='text-align:center;padding-top:8px'>"
                        f"{quantity}</div>",
                        unsafe_allow_html=True,
                    )

                with plus_col:
                    if st.button(
                        "➕",
                        key=f"plus_{item_id}",
                        use_container_width=True,
                    ):
                        add_item(item_id)
                        st.rerun()

                note_value = st.text_input(
                    "Ghi chú món",
                    value=st.session_state.notes.get(item_id, ""),
                    placeholder="VD: ít cay, không hành...",
                    key=f"note_{item_id}",
                )

                st.session_state.notes[item_id] = note_value

    st.divider()

    voucher_code = st.text_input(
        "🎟️ Mã voucher",
        placeholder="VD: N2WELCOME",
        key="voucher_code",
    ).strip().upper()

    current_subtotal = subtotal()

    discount_amount, voucher_message = calculate_voucher(
        voucher_code,
        current_subtotal,
    )

    discount_amount = int(discount_amount)
    total_amount = max(0, current_subtotal - discount_amount)

    if voucher_code:
        if discount_amount > 0:
            st.success(voucher_message)
        else:
            st.warning(voucher_message)

    st.markdown(f"**Tạm tính:** {money(current_subtotal)}")
    st.markdown(f"**Giảm giá:** {money(discount_amount)}")

    html_markdown(
        f"""
<div class="cart-total">
    <div class="cart-total-label">TỔNG THANH TOÁN</div>
    <div class="cart-total-value">{money(total_amount)}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.caption("Điểm tích lũy dự kiến: "
               f"{loyalty_points(total_amount)} điểm")

    checkout_clicked = st.button(
        "✅ Xác nhận đơn hàng",
        type="primary",
        use_container_width=True,
        disabled=(
            not st.session_state.cart
            or not table_number.strip()
            or not customer_name.strip()
        ),
        key="checkout_button",
    )

    if checkout_clicked:
        now = datetime.now()
        invoice_number = (
            "N2-" + now.strftime("%Y%m%d-%H%M%S")
            + "-" + uuid.uuid4().hex[:4].upper()
        )

        invoice_items = []

        for item_id, quantity in st.session_state.cart.items():
            item = MENU_BY_ID[item_id]

            invoice_items.append({
                "name": item["name"],
                "price": int(item["price"]),
                "quantity": int(quantity),
                "note": st.session_state.notes.get(item_id, ""),
                "total": int(item["price"] * quantity),
            })

        invoice_data = {
            "number": invoice_number,
            "time": now,
            "table": table_number.strip(),
            "customer": customer_name.strip(),
            "phone": customer_phone.strip(),
            "items": invoice_items,
            "subtotal": int(current_subtotal),
            "discount": int(discount_amount),
            "total": int(total_amount),
            "voucher": voucher_code if discount_amount > 0 else "",
            "points": loyalty_points(total_amount),
        }

        try:
            save_order_to_database(invoice_data)
            st.session_state.invoice = invoice_data
            st.session_state.cart = {}
            st.session_state.notes = {}

            st.success("Đơn hàng đã được lưu thành công!")
            st.rerun()

        except sqlite3.Error as exc:
            st.error(f"Không lưu được đơn hàng vào database: {exc}")


# =========================================================
# 17. HÓA ĐƠN
# =========================================================

st.divider()

html_markdown(
    '<div class="section-title">🧾 Hóa đơn</div>',
    unsafe_allow_html=True,
)

invoice = st.session_state.invoice

if invoice:
    html_markdown(
        f"""
<div class="invoice-box">
    <div class="invoice-title">🍣 N2 Sushi</div>
    <div class="invoice-number">
        HÓA ĐƠN: {html.escape(invoice['number'])}
    </div>
    <div class="invoice-row">
        <span>Thời gian</span>
        <span>{invoice['time'].strftime('%d/%m/%Y %H:%M:%S')}</span>
    </div>
    <div class="invoice-row">
        <span>Số bàn</span>
        <span>{html.escape(invoice['table'])}</span>
    </div>
    <div class="invoice-row">
        <span>Khách hàng</span>
        <span>{html.escape(invoice['customer'])}</span>
    </div>
    <div class="invoice-row">
        <span>Số điện thoại</span>
        <span>{html.escape(invoice['phone'] or 'Không cung cấp')}</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("#### Chi tiết món")

    for item in invoice["items"]:
        st.write(
            f"**{item['name']}** × {item['quantity']} — "
            f"{money(item['total'])}"
        )

        if item["note"]:
            st.caption(f"Ghi chú: {item['note']}")

    st.markdown("---")
    st.write(f"**Tạm tính:** {money(invoice['subtotal'])}")
    st.write(f"**Giảm giá:** {money(invoice['discount'])}")
    st.markdown(f"## Tổng cộng: {money(invoice['total'])}")
    st.success(f"🎁 Điểm tích lũy: +{invoice['points']} điểm")

    invoice_text = [
        "N2 SUSHI",
        f"Hóa đơn: {invoice['number']}",
        f"Thời gian: {invoice['time'].strftime('%d/%m/%Y %H:%M:%S')}",
        f"Số bàn: {invoice['table']}",
        f"Khách hàng: {invoice['customer']}",
        f"Số điện thoại: {invoice['phone'] or 'Không cung cấp'}",
        "-" * 35,
    ]

    for item in invoice["items"]:
        invoice_text.append(
            f"{item['name']} x {item['quantity']} = "
            f"{money(item['total'])}"
        )

        if item["note"]:
            invoice_text.append(f"  Ghi chú: {item['note']}")

    invoice_text.extend([
        "-" * 35,
        f"Tạm tính: {money(invoice['subtotal'])}",
        f"Giảm giá: {money(invoice['discount'])}",
        f"Tổng thanh toán: {money(invoice['total'])}",
        f"Điểm tích lũy: {invoice['points']}",
        "",
        "Cảm ơn quý khách đã dùng bữa tại N2 Sushi!",
    ])

    st.download_button(
        "⬇️ Tải hóa đơn dạng TXT",
        data="\n".join(invoice_text),
        file_name=f"{invoice['number']}.txt",
        mime="text/plain",
        use_container_width=True,
    )

else:
    st.info("Chưa có hóa đơn. Hãy chọn món và xác nhận đơn hàng.")


# =========================================================
# 18. FOOTER
# =========================================================

html_markdown(
    f"""
<div class="footer">
    <div style="font-size:22px;font-weight:900;color:#793d49;">
        🍣 N2 Sushi
    </div>
    <div style="margin-top:8px;">
        {html.escape(RESTAURANT_ADDRESS)}
    </div>
    <div style="margin-top:5px;">
        Hotline: {html.escape(RESTAURANT_PHONE)}
    </div>
    <div style="margin-top:12px;">
        Cảm ơn bạn đã lựa chọn N2 Sushi ❤️
    </div>
</div>
""",
    unsafe_allow_html=True,
)
