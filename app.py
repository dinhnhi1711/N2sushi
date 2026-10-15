

import streamlit as st
import sqlite3
import pandas as pd
import html
import io
import os
import uuid
import random
import string
from datetime import datetime
from pathlib import Path

# =========================================================
# 1. CẤU HÌNH APP
# =========================================================

st.set_page_config(
    page_title="N2 Sushi | POS",
    page_icon="🍣",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "n2_sushi.db"

# Sửa thông tin này thành thông tin thật của quán
SHOP_NAME = "N2 Sushi"
SHOP_ADDRESS = "123 Đường ABC, TP. Thủ Dầu Một, Bình Dương"
SHOP_PHONE = "0900 123 456"
SHOP_HOURS = "09:00 - 22:00 hằng ngày"

# Ảnh banner sushi. Có thể thay bằng đường dẫn ảnh của quán.
BANNER_URL = (
    "https://images.unsplash.com/"
    "photo-1579871494447-9811cf80d66c"
    "?auto=format&fit=crop&w=1800&q=85"
)

# =========================================================
# 2. GIAO DIỆN
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif;
}

.stApp {
    background: #f7f5f0;
    color: #222222;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: #171717;
}

section[data-testid="stSidebar"] * {
    color: #f5f0e8;
}

.hero {
    padding: 28px;
    border-radius: 18px;
    background: linear-gradient(
        110deg,
        rgba(15,15,15,0.96),
        rgba(80,20,30,0.86)
    );
    color: #fff8ed;
    margin-bottom: 20px;
}

.hero h1 {
    font-size: 38px;
    font-weight: 800;
    margin: 0;
    letter-spacing: 2px;
}

.hero p {
    color: #e7d7c4;
    font-size: 14px;
    line-height: 1.9;
}

.section-title {
    color: #7d1f2a;
    font-size: 22px;
    font-weight: 800;
    margin: 18px 0 12px 0;
}

.info-card {
    background: #ffffff;
    padding: 17px;
    border-radius: 14px;
    border: 1px solid #e9e1d5;
    margin-bottom: 12px;
}

.total-card {
    background: #191919;
    color: #ffffff;
    border-radius: 16px;
    padding: 24px;
}

.total-number {
    font-size: 32px;
    font-weight: 800;
    color: #f1c77a;
}

.small-muted {
    color: #8b8175;
    font-size: 12px;
}

div.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
}

div.stButton > button[kind="primary"] {
    background: #7d1f2a;
    border: 1px solid #7d1f2a;
    color: white;
}

div.stButton > button[kind="primary"]:hover {
    background: #58141c;
    border-color: #58141c;
}

div[data-testid="stMetric"] {
    background: white;
    padding: 14px;
    border-radius: 12px;
    border: 1px solid #ece4d8;
}

.chat-panel {
    background: #171717;
    padding: 18px;
    border-radius: 15px;
    color: white;
}

.chat-bubble {
    background: #ffffff;
    color: #171717;
    border-radius: 12px;
    padding: 12px 15px;
    margin: 9px 0;
    line-height: 1.7;
    overflow-wrap: anywhere;
}

.chat-user {
    background: #7d1f2a;
    color: white;
    border-radius: 12px;
    padding: 12px 15px;
    margin: 9px 0;
    line-height: 1.7;
    overflow-wrap: anywhere;
}

div[data-testid="stExpander"] {
    background: white;
    border-radius: 12px;
}

hr {
    border-color: #e5ddd2;
}

@media (max-width: 768px) {
    .hero h1 { font-size: 28px; }
    .total-number { font-size: 25px; }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. DATABASE SQLITE
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            bestseller INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS customers (
            phone TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            visits INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            table_number TEXT,
            created_at TEXT NOT NULL,
            subtotal INTEGER NOT NULL,
            discount INTEGER NOT NULL,
            total INTEGER NOT NULL,
            points_earned INTEGER DEFAULT 0,
            voucher TEXT,
            payment_method TEXT,
            status TEXT DEFAULT 'Đã thanh toán'
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            line_total INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM menu"
        ).fetchone()[0]

        if count == 0:
            menu_items = [
                # Sushi
                ("🍣 Sushi cá hồi", "Sushi", 45000, 1),
                ("🍣 Sushi cá ngừ", "Sushi", 40000, 0),
                ("🍣 Sushi lươn Nhật", "Sushi", 55000, 1),
                ("🍣 Sushi tôm", "Sushi", 35000, 0),
                ("🍣 Sushi thanh cua", "Sushi", 30000, 0),
                ("🍣 Sushi trứng Nhật", "Sushi", 25000, 0),
                ("🍣 Sushi tổng hợp 8 miếng", "Sushi", 99000, 1),

                # Sashimi
                ("🐟 Sashimi cá hồi", "Sashimi", 129000, 1),
                ("🐟 Sashimi cá ngừ", "Sashimi", 119000, 0),
                ("🐟 Sashimi tổng hợp", "Sashimi", 189000, 1),

                # Món nóng
                ("🍜 Ramen bò", "Món nóng", 89000, 1),
                ("🍜 Ramen hải sản", "Món nóng", 95000, 0),
                ("🍤 Tempura tôm", "Món nóng", 79000, 1),
                ("🍗 Gà chiên sốt teriyaki", "Món nóng", 69000, 0),
                ("🍚 Cơm bò Nhật", "Món nóng", 75000, 0),
                ("🥟 Há cảo Nhật", "Món nóng", 49000, 0),
                ("🥗 Salad rong biển", "Món nóng", 39000, 0),

                # Combo
                ("🎎 Combo N2 Couple", "Combo", 199000, 1),
                ("🍱 Combo Sakura", "Combo", 299000, 1),
                ("👨‍👩‍👧 Combo Family 3-4 người", "Combo", 499000, 1),
                ("👑 Combo Premium", "Combo", 699000, 1),

                # Thức uống
                ("🍵 Trà xanh Nhật", "Thức uống", 25000, 0),
                ("🧋 Trà đào", "Thức uống", 30000, 1),
                ("🥤 Coca-Cola", "Thức uống", 20000, 0),
                ("🍋 Nước chanh", "Thức uống", 25000, 0),
                ("🍓 Soda dâu", "Thức uống", 35000, 0),
                ("💧 Nước suối", "Thức uống", 15000, 0),
            ]

            conn.executemany("""
                INSERT INTO menu(name, category, price, bestseller)
                VALUES (?, ?, ?, ?)
            """, menu_items)

        conn.commit()


init_database()

# =========================================================
# 4. HÀM HỖ TRỢ
# =========================================================

def money(value):
    return f"{int(value):,}".replace(",", ".") + " đ"


def get_menu(active_only=True):
    with get_connection() as conn:
        query = """
            SELECT id, name, category, price, bestseller, active
            FROM menu
        """
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY category, name"

        return pd.read_sql_query(query, conn)


def get_customer(phone):
    if not phone:
        return None

    with get_connection() as conn:
        row = conn.execute("""
            SELECT phone, name, points, total_spent, visits
            FROM customers
            WHERE phone = ?
        """, (phone.strip(),)).fetchone()

    if row:
        return {
            "phone": row[0],
            "name": row[1],
            "points": row[2],
            "total_spent": row[3],
            "visits": row[4],
        }

    return None


def get_sales_summary():
    with get_connection() as conn:
        today = datetime.now().strftime("%Y-%m-%d")

        today_data = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(total), 0)
            FROM orders
            WHERE substr(created_at, 1, 10) = ?
              AND status = 'Đã thanh toán'
        """, (today,)).fetchone()

        all_data = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(total), 0)
            FROM orders
            WHERE status = 'Đã thanh toán'
        """).fetchone()

    return today_data, all_data


def generate_order_code():
    return "N2" + datetime.now().strftime("%y%m%d%H%M%S") + \
        uuid.uuid4().hex[:4].upper()


def calculate_voucher(code, subtotal):
    code = (code or "").strip().upper()

    if not code:
        return 0, ""

    if code == "N2WELCOME":
        discount = min(int(subtotal * 0.10), 50000)
        return discount, "N2WELCOME - Giảm 10%, tối đa 50.000đ"

    if code == "SUSHI20":
        if subtotal >= 200000:
            return 20000, "SUSHI20 - Giảm 20.000đ"
        return 0, "Đơn hàng chưa đạt 200.000đ để dùng SUSHI20"

    if code == "N2VIP":
        if subtotal >= 500000:
            discount = min(int(subtotal * 0.15), 100000)
            return discount, "N2VIP - Giảm 15%, tối đa 100.000đ"
        return 0, "Đơn hàng chưa đạt 500.000đ để dùng N2VIP"

    return 0, "Mã voucher không hợp lệ"


def build_invoice_html(order, items):
    safe = lambda x: html.escape(str(x if x is not None else ""))

    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td>{safe(item['name'])}</td>
            <td style="text-align:center">{item['quantity']}</td>
            <td style="text-align:right">{money(item['price'])}</td>
            <td style="text-align:right">{money(item['line_total'])}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hóa đơn {safe(order['order_code'])}</title>
<style>
body {{
    font-family: Arial, sans-serif;
    max-width: 760px;
    margin: 30px auto;
    padding: 25px;
    color: #222;
}}
h1 {{ color: #7d1f2a; text-align: center; }}
p {{ line-height: 1.7; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ border-bottom: 1px solid #ddd; padding: 11px 6px; }}
th {{ background: #f5f0e8; text-align: left; }}
.total {{ text-align: right; font-size: 21px; color: #7d1f2a; font-weight: bold; }}
@media print {{
    button {{ display: none; }}
    body {{ margin: 0 auto; }}
}}
</style>
</head>
<body>
<h1>🍣 N2 SUSHI</h1>
<p style="text-align:center">
    {safe(SHOP_ADDRESS)}<br>
    Điện thoại: {safe(SHOP_PHONE)}<br>
    Giờ mở cửa: {safe(SHOP_HOURS)}
</p>
<hr>
<h2>HÓA ĐƠN THANH TOÁN</h2>
<p>
    Mã hóa đơn: <b>{safe(order['order_code'])}</b><br>
    Thời gian: {safe(order['created_at'])}<br>
    Khách hàng: {safe(order['customer_name'])}<br>
    Điện thoại: {safe(order['customer_phone'])}<br>
    Số bàn: {safe(order['table_number'])}<br>
    Hình thức thanh toán: {safe(order['payment_method'])}
</p>
<table>
<thead>
<tr>
<th>Món ăn / thức uống</th>
<th style="text-align:center">SL</th>
<th style="text-align:right">Đơn giá</th>
<th style="text-align:right">Thành tiền</th>
</tr>
</thead>
<tbody>{rows}</tbody>
</table>
<p style="text-align:right">Tạm tính: <b>{money(order['subtotal'])}</b></p>
<p style="text-align:right">Voucher: <b>-{money(order['discount'])}</b></p>
<p class="total">TỔNG THANH TOÁN: {money(order['total'])}</p>
<p>Điểm tích lũy nhận được: <b>{order['points_earned']} điểm</b></p>
<p style="text-align:center;margin-top:35px">
    Cảm ơn quý khách đã lựa chọn N2 Sushi!<br>
    Hẹn gặp lại quý khách ❤️
</p>
<button onclick="window.print()">In hóa đơn / Lưu PDF</button>
</body>
</html>"""


# =========================================================
# 5. HEADER - HÌNH ẢNH QUÁN
# =========================================================

try:
    st.image(BANNER_URL, use_container_width=True)
except Exception:
    st.markdown("""
    <div class="hero">
        <h1>🍣 N2 SUSHI</h1>
        <p>Japanese Dining · Fresh Taste · Premium Experience</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="hero">
    <h1>🍣 N2 SUSHI</h1>
    <p>
        JAPANESE DINING · FRESH TASTE · PREMIUM EXPERIENCE<br>
        📍 {html.escape(SHOP_ADDRESS)}<br>
        ☎️ {html.escape(SHOP_PHONE)}
        &nbsp;&nbsp; | &nbsp;&nbsp;
        🕒 {html.escape(SHOP_HOURS)}
    </p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 6. KHỞI TẠO SESSION
# =========================================================

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "last_invoice" not in st.session_state:
    st.session_state.last_invoice = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": (
                "Xin chào! 🍣 Mình là trợ lý N2 Sushi. "
                "Bạn muốn hỏi về menu, món best seller, "
                "địa chỉ, giờ mở cửa hay voucher?"
            )
        }
    ]

if "customer_phone_input" not in st.session_state:
    st.session_state.customer_phone_input = ""

# =========================================================
# 7. SIDEBAR - ĐIỀU HƯỚNG
# =========================================================

st.sidebar.markdown("# 🍣 N2 SUSHI")
st.sidebar.caption("PREMIUM POS SYSTEM")

page = st.sidebar.radio(
    "CHỨC NĂNG",
    [
        "🧾 Tạo đơn & tính tiền",
        "🍱 Quản lý thực đơn",
        "📊 Báo cáo doanh thu",
        "🗂️ Lịch sử hóa đơn",
        "💬 Chatbot tư vấn",
    ]
)

st.sidebar.divider()
st.sidebar.markdown("### 🎟️ VOUCHER")
st.sidebar.markdown("""
**N2WELCOME**  
Giảm 10%, tối đa 50.000đ.

**SUSHI20**  
Giảm 20.000đ cho đơn từ 200.000đ.

**N2VIP**  
Giảm 15%, tối đa 100.000đ cho đơn từ 500.000đ.
""")

st.sidebar.caption("N2 Sushi POS • SQLite Database")

# =========================================================
# 8. TRANG TẠO ĐƠN HÀNG
# =========================================================

if page == "🧾 Tạo đơn & tính tiền":

    st.markdown(
        '<div class="section-title">🧾 THÔNG TIN KHÁCH HÀNG</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        customer_name = st.text_input(
            "👤 Tên khách hàng",
            placeholder="Nhập tên khách hàng"
        )

    with c2:
        customer_phone = st.text_input(
            "📱 Số điện thoại",
            key="customer_phone_input",
            placeholder="Nhập số điện thoại"
        )

    with c3:
        table_number = st.text_input(
            "🪑 Số bàn",
            placeholder="VD: B01"
        )

    existing_customer = get_customer(customer_phone)

    if existing_customer:
        st.success(
            f"🌟 Khách hàng thân thiết: "
            f"{existing_customer['name']} · "
            f"{existing_customer['points']} điểm · "
            f"{existing_customer['visits']} lượt ghé"
        )

    st.divider()

    menu_df = get_menu()

    st.markdown(
        '<div class="section-title">🍱 MENU N2 SUSHI</div>',
        unsafe_allow_html=True
    )

    category_options = [
        "Tất cả",
        "Sushi",
        "Sashimi",
        "Món nóng",
        "Combo",
        "Thức uống"
    ]

    selected_category = st.selectbox(
        "Chọn danh mục món",
        category_options
    )

    if selected_category == "Tất cả":
        filtered_menu = menu_df
    else:
        filtered_menu = menu_df[
            menu_df["category"] == selected_category
        ]

    if not filtered_menu.empty:
        menu_display = filtered_menu[
            ["name", "category", "price", "bestseller"]
        ].copy()

        menu_display.columns = [
            "Tên món",
            "Danh mục",
            "Giá (đ)",
            "Best seller"
        ]

        menu_display["Giá (đ)"] = menu_display["Giá (đ)"].apply(
            money
        )
        menu_display["Best seller"] = menu_display[
            "Best seller"
        ].map({1: "⭐ Bán chạy", 0: ""})

        st.dataframe(
            menu_display,
            use_container_width=True,
            hide_index=True
        )

    st.markdown("### 🛒 Chọn nhiều món cho cùng một đơn")

    available_names = filtered_menu["name"].tolist()

    if available_names:
        selected_items = st.multiselect(
            "Chọn món ăn, combo và thức uống",
            options=available_names,
            key="selected_items"
        )

        for item_name in selected_items:
            item_row = menu_df[
                menu_df["name"] == item_name
            ].iloc[0]

            item_price = int(item_row["price"])

            col1, col2, col3 = st.columns([4, 2, 2])

            with col1:
                st.write(f"**{item_name}**")
                st.caption(money(item_price))

            with col2:
                qty = st.number_input(
                    "Số lượng",
                    min_value=1,
                    max_value=100,
                    value=st.session_state.cart.get(
                        item_name, 1
                    ),
                    step=1,
                    key="qty_" + str(item_row["id"])
                )

            with col3:
                st.write("Thành tiền")
                st.write(f"**{money(item_price * qty)}**")

            st.session_state.cart[item_name] = int(qty)

    # Xóa món khỏi đơn nếu người dùng bỏ chọn
    current_selected = set(
        st.session_state.get("selected_items", [])
    )

    for old_item in list(st.session_state.cart.keys()):
        if old_item not in current_selected:
            del st.session_state.cart[old_item]

    st.divider()

    st.markdown(
        '<div class="section-title">🧮 TỔNG KẾT ĐƠN HÀNG</div>',
        unsafe_allow_html=True
    )

    # Tạo dữ liệu giỏ hàng
    order_items = []

    for item_name, qty in st.session_state.cart.items():
        rows = menu_df[menu_df["name"] == item_name]

        if rows.empty:
            continue

        row = rows.iloc[0]
        price = int(row["price"])
        qty = int(qty)

        order_items.append({
            "name": item_name,
            "category": row["category"],
            "price": price,
            "quantity": qty,
            "line_total": price * qty
        })

    subtotal = sum(
        item["line_total"] for item in order_items
    )

    left, right = st.columns([3, 2])

    with left:
        st.markdown("#### Chi tiết món đã gọi")

        if order_items:
            order_df = pd.DataFrame(order_items)
            order_df = order_df.rename(columns={
                "name": "Tên món",
                "category": "Danh mục",
                "price": "Đơn giá",
                "quantity": "Số lượng",
                "line_total": "Thành tiền"
            })

            order_df["Đơn giá"] = order_df["Đơn giá"].apply(money)
            order_df["Thành tiền"] = order_df["Thành tiền"].apply(money)

            st.dataframe(
                order_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Chưa có món nào trong đơn hàng.")

    with right:
        st.markdown("#### 💳 Thanh toán")

        st.write("Tạm tính:", money(subtotal))

        voucher_code = st.text_input(
            "🎟️ Nhập mã voucher",
            placeholder="VD: N2WELCOME",
            key="voucher_code"
        )

        discount, voucher_message = calculate_voucher(
            voucher_code, subtotal
        )

        discount = min(discount, subtotal)
        total = max(0, subtotal - discount)

        if voucher_code.strip():
            if discount > 0:
                st.success(voucher_message)
            else:
                st.warning(voucher_message)

        st.markdown(
            f"""
            <div class="total-card">
                <div>TỔNG THANH TOÁN</div>
                <div class="total-number">{money(total)}</div>
                <hr>
                <div>Giảm giá: -{money(discount)}</div>
                <div>Điểm dự kiến: {total // 10000} điểm</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        payment_method = st.selectbox(
            "Phương thức thanh toán",
            [
                "Tiền mặt",
                "Chuyển khoản",
                "Thẻ ngân hàng",
                "Ví điện tử"
            ]
        )

        confirm_payment = st.button(
            "✅ XÁC NHẬN THANH TOÁN & XUẤT HÓA ĐƠN",
            type="primary",
            use_container_width=True
        )

        if confirm_payment:
            if not customer_name.strip():
                st.error("Vui lòng nhập tên khách hàng.")

            elif not order_items:
                st.error("Vui lòng chọn ít nhất một món.")

            elif customer_phone.strip() and not customer_phone.strip().isdigit():
                st.error("Số điện thoại chỉ nên gồm các chữ số.")

            else:
                now = datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                )

                order_code = generate_order_code()
                points_earned = total // 10000
                phone = customer_phone.strip()
                name = customer_name.strip()

                voucher_saved = (
                    voucher_code.strip().upper()
                    if discount > 0 else ""
                )

                try:
                    with get_connection() as conn:
                        cur = conn.cursor()

                        cur.execute("""
                            INSERT INTO orders(
                                order_code, customer_name,
                                customer_phone, table_number,
                                created_at, subtotal, discount,
                                total, points_earned, voucher,
                                payment_method, status
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            order_code,
                            name,
                            phone,
                            table_number.strip(),
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            subtotal,
                            discount,
                            total,
                            points_earned,
                            voucher_saved,
                            payment_method,
                            "Đã thanh toán"
                        ))

                        order_id = cur.lastrowid

                        for item in order_items:
                            cur.execute("""
                                INSERT INTO order_items(
                                    order_id, item_name, category,
                                    price, quantity, line_total
                                )
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                order_id,
                                item["name"],
                                item["category"],
                                item["price"],
                                item["quantity"],
                                item["line_total"]
                            ))

                        # Lưu khách hàng và cộng điểm
                        if phone:
                            cur.execute("""
                                INSERT INTO customers(
                                    phone, name, points,
                                    total_spent, visits
                                )
                                VALUES (?, ?, ?, ?, 1)
                                ON CONFLICT(phone) DO UPDATE SET
                                    name = excluded.name,
                                    points = customers.points
                                        + excluded.points,
                                    total_spent =
                                        customers.total_spent
                                        + excluded.total_spent,
                                    visits = customers.visits + 1
                            """, (
                                phone,
                                name,
                                points_earned,
                                total
                            ))

                        conn.commit()

                    invoice_order = {
                        "order_code": order_code,
                        "customer_name": name,
                        "customer_phone": phone or "Không cung cấp",
                        "table_number": table_number.strip() or "Mang đi",
                        "created_at": now,
                        "subtotal": subtotal,
                        "discount": discount,
                        "total": total,
                        "points_earned": points_earned,
                        "payment_method": payment_method
                    }

                    invoice_html = build_invoice_html(
                        invoice_order, order_items
                    )

                    st.session_state.last_invoice = {
                        "order": invoice_order,
                        "items": order_items,
                        "html": invoice_html
                    }

                    st.session_state.cart = {}
                    st.session_state["selected_items"] = []

                    st.success(
                        f"Thanh toán thành công! "
                        f"Mã hóa đơn: {order_code}"
                    )

                    st.rerun()

                except sqlite3.Error as e:
                    st.error(f"Lỗi lưu database: {e}")

    # Hiển thị hóa đơn gần nhất sau khi thanh toán
    if st.session_state.last_invoice:
        invoice = st.session_state.last_invoice
        order = invoice["order"]

        st.divider()
        st.markdown("## 🧾 HÓA ĐƠN VỪA THANH TOÁN")

        a, b, c = st.columns(3)

        a.metric("Mã hóa đơn", order["order_code"])
        b.metric("Tổng thanh toán", money(order["total"]))
        c.metric("Điểm tích lũy", order["points_earned"])

        st.write("Khách hàng:", order["customer_name"])
        st.write("Số điện thoại:", order["customer_phone"])
        st.write("Số bàn:", order["table_number"])

        st.download_button(
            "📥 TẢI FILE HÓA ĐƠN HTML",
            data=invoice["html"].encode("utf-8"),
            file_name=f"hoa_don_{order['order_code']}.html",
            mime="text/html",
            use_container_width=True
        )

        with st.expander("👁️ Xem nội dung hóa đơn"):
            st.dataframe(
                pd.DataFrame(invoice["items"]),
                use_container_width=True,
                hide_index=True
            )

        st.caption(
            "Mở file HTML vừa tải bằng trình duyệt, "
            "bấm 'In hóa đơn / Lưu PDF' để in hoặc lưu PDF."
        )

# =========================================================
# 9. QUẢN LÝ MENU
# =========================================================

elif page == "🍱 Quản lý thực đơn":

    st.markdown(
        '<div class="section-title">🍱 QUẢN LÝ THỰC ĐƠN</div>',
        unsafe_allow_html=True
    )

    menu_df = get_menu(active_only=False)

    st.dataframe(
        menu_df.rename(columns={
            "id": "Mã",
            "name": "Tên món",
            "category": "Danh mục",
            "price": "Giá",
            "bestseller": "Best seller",
            "active": "Đang bán"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.markdown("### ➕ Thêm món mới")

    with st.form("add_menu_form"):
        new_name = st.text_input("Tên món")
        new_category = st.selectbox(
            "Danh mục",
            ["Sushi", "Sashimi", "Món nóng", "Combo", "Thức uống"]
        )
        new_price = st.number_input(
            "Giá bán (VNĐ)",
            min_value=1000,
            max_value=100000000,
            value=30000,
            step=1000
        )
        new_best = st.checkbox("Đánh dấu best seller")

        submitted = st.form_submit_button("Thêm món")

        if submitted:
            if not new_name.strip():
                st.error("Vui lòng nhập tên món.")
            else:
                try:
                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO menu(
                                name, category, price,
                                bestseller, active
                            )
                            VALUES (?, ?, ?, ?, 1)
                        """, (
                            new_name.strip(),
                            new_category,
                            int(new_price),
                            int(new_best)
                        ))
                        conn.commit()

                    st.success("Đã thêm món mới!")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error("Tên món này đã tồn tại.")

    st.divider()
    st.markdown("### ✏️ Cập nhật giá / trạng thái món")

    active_df = get_menu(active_only=False)

    if not active_df.empty:
        edit_name = st.selectbox(
            "Chọn món cần chỉnh sửa",
            active_df["name"].tolist()
        )

        edit_row = active_df[
            active_df["name"] == edit_name
        ].iloc[0]

        edit_price = st.number_input(
            "Giá mới (VNĐ)",
            min_value=1000,
            max_value=100000000,
            value=int(edit_row["price"]),
            step=1000
        )

        edit_active = st.checkbox(
            "Đang kinh doanh",
            value=bool(edit_row["active"])
        )

        if st.button("💾 Lưu thay đổi"):
            with get_connection() as conn:
                conn.execute("""
                    UPDATE menu
                    SET price = ?, active = ?
                    WHERE name = ?
                """, (
                    int(edit_price),
                    int(edit_active),
                    edit_name
                ))
                conn.commit()

            st.success("Đã cập nhật thực đơn.")
            st.rerun()

# =========================================================
# 10. BÁO CÁO DOANH THU
# =========================================================

elif page == "📊 Báo cáo doanh thu":

    st.markdown(
        '<div class="section-title">📊 BÁO CÁO KINH DOANH</div>',
        unsafe_allow_html=True
    )

    today_data, all_data = get_sales_summary()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Đơn hôm nay", f"{today_data[0]:,}")
    col2.metric("Doanh thu hôm nay", money(today_data[1]))
    col3.metric("Tổng đơn", f"{all_data[0]:,}")
    col4.metric("Tổng doanh thu", money(all_data[1]))

    st.divider()

    with get_connection() as conn:
        daily = pd.read_sql_query("""
            SELECT substr(created_at, 1, 10) AS ngay,
                   COUNT(*) AS so_don,
                   SUM(total) AS doanh_thu
            FROM orders
            WHERE status = 'Đã thanh toán'
            GROUP BY substr(created_at, 1, 10)
            ORDER BY ngay
        """, conn)

        best_items = pd.read_sql_query("""
            SELECT item_name AS ten_mon,
                   SUM(quantity) AS so_luong,
                   SUM(line_total) AS doanh_thu
            FROM order_items
            JOIN orders ON order_items.order_id = orders.id
            WHERE orders.status = 'Đã thanh toán'
            GROUP BY item_name
            ORDER BY so_luong DESC
            LIMIT 10
        """, conn)

    st.markdown("### 📈 Doanh thu theo ngày")

    if not daily.empty:
        chart_df = daily.set_index("ngay")
        st.bar_chart(chart_df["doanh_thu"])
        st.dataframe(daily, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu doanh thu.")

    st.markdown("### 🏆 Top 10 món được gọi nhiều nhất")

    if not best_items.empty:
        best_items["doanh_thu"] = best_items["doanh_thu"].apply(money)
        st.dataframe(
            best_items,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Chưa có dữ liệu món bán.")

# =========================================================
# 11. LỊCH SỬ HÓA ĐƠN
# =========================================================

elif page == "🗂️ Lịch sử hóa đơn":

    st.markdown(
        '<div class="section-title">🗂️ LỊCH SỬ HÓA ĐƠN</div>',
        unsafe_allow_html=True
    )

    search_term = st.text_input(
        "🔎 Tìm theo mã hóa đơn, tên khách hoặc số điện thoại"
    )

    with get_connection() as conn:
        orders_df = pd.read_sql_query("""
            SELECT id, order_code, customer_name,
                   customer_phone, table_number, created_at,
                   subtotal, discount, total,
                   points_earned, payment_method, status
            FROM orders
            ORDER BY id DESC
        """, conn)

    if search_term.strip():
        term = search_term.strip().lower()

        mask = (
            orders_df["order_code"].astype(str).str.lower().str.contains(
                term, na=False
            )
            | orders_df["customer_name"].astype(str).str.lower().str.contains(
                term, na=False
            )
            | orders_df["customer_phone"].astype(str).str.lower().str.contains(
                term, na=False
            )
        )

        orders_df = orders_df[mask]

    if not orders_df.empty:
        st.dataframe(
            orders_df,
            use_container_width=True,
            hide_index=True
        )

        selected_order_code = st.selectbox(
            "Chọn hóa đơn để xem chi tiết",
            orders_df["order_code"].tolist()
        )

        if st.button("👁️ Xem chi tiết hóa đơn"):
            with get_connection() as conn:
                order_row = conn.execute("""
                    SELECT id, order_code, customer_name,
                           customer_phone, table_number, created_at,
                           subtotal, discount, total,
                           points_earned, payment_method
                    FROM orders WHERE order_code = ?
                """, (selected_order_code,)).fetchone()

                item_rows = conn.execute("""
                    SELECT item_name, category, price,
                           quantity, line_total
                    FROM order_items
                    WHERE order_id = ?
                """, (order_row[0],)).fetchall()

            if order_row:
                st.markdown(f"### 🧾 Hóa đơn {order_row[1]}")
                st.write("Khách hàng:", order_row[2])
                st.write("Số điện thoại:", order_row[3])
                st.write("Số bàn:", order_row[4])
                st.write("Thời gian:", order_row[5])

                detail_items = [
                    {
                        "name": r[0],
                        "category": r[1],
                        "price": r[2],
                        "quantity": r[3],
                        "line_total": r[4]
                    }
                    for r in item_rows
                ]

                st.dataframe(
                    pd.DataFrame(detail_items),
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown(
                    f"**Tổng thanh toán: {money(order_row[8])}**"
                )

                invoice_order = {
                    "order_code": order_row[1],
                    "customer_name": order_row[2],
                    "customer_phone": order_row[3],
                    "table_number": order_row[4],
                    "created_at": order_row[5],
                    "subtotal": order_row[6],
                    "discount": order_row[7],
                    "total": order_row[8],
                    "points_earned": order_row[9],
                    "payment_method": order_row[10]
                }

                invoice_html = build_invoice_html(
                    invoice_order, detail_items
                )

                st.download_button(
                    "📥 Tải lại hóa đơn HTML",
                    data=invoice_html.encode("utf-8"),
                    file_name=f"hoa_don_{order_row[1]}.html",
                    mime="text/html"
                )

        csv_data = orders_df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "📥 Xuất danh sách hóa đơn CSV",
            data=csv_data,
            file_name="lich_su_hoa_don_n2_sushi.csv",
            mime="text/csv"
        )

    else:
        st.info("Chưa có hóa đơn phù hợp.")

# =========================================================
# 12. CHATBOT TƯ VẤN
# =========================================================

elif page == "💬 Chatbot tư vấn":

    st.markdown(
        '<div class="section-title">💬 TRỢ LÝ N2 SUSHI</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="chat-panel">
        <h3>🍣 N2 Sushi Assistant</h3>
        <p style="color:#c7b9ab">
            Trợ lý tư vấn menu · Giờ mở cửa · Địa chỉ · Voucher
        </p>
    </div>
    """, unsafe_allow_html=True)

    def chatbot_reply(question):
        q = question.lower().strip()
        menu = get_menu()

        if any(x in q for x in [
            "xin chào", "hello", "hi", "chào"
        ]):
            return (
                "Xin chào bạn! 🍣 Chào mừng đến với N2 Sushi. "
                "Mình có thể tư vấn món ăn, combo, giá cả, "
                "giờ mở cửa và chương trình tích điểm nhé!"
            )

        if any(x in q for x in [
            "giờ", "mở cửa", "đóng cửa", "mấy giờ"
        ]):
            return (
                f"🕒 N2 Sushi mở cửa: {SHOP_HOURS}. "
                "Nếu có lịch nghỉ lễ đặc biệt, bạn nên xác nhận "
                "lại với cửa hàng trước khi ghé nhé."
            )

        if any(x in q for x in [
            "địa chỉ", "ở đâu", "đường nào", "chỗ nào"
        ]):
            return (
                f"📍 Địa chỉ N2 Sushi: {SHOP_ADDRESS}. "
                f"Bạn có thể liên hệ {SHOP_PHONE} "
                "để hỏi đường đến quán."
            )

        if any(x in q for x in [
            "số điện thoại", "liên hệ", "hotline", "gọi"
        ]):
            return f"☎️ Số điện thoại liên hệ N2 Sushi: {SHOP_PHONE}."

        if any(x in q for x in [
            "best seller", "bán chạy", "nổi tiếng",
            "ngon nhất", "món nào ngon", "nên ăn gì"
        ]):
            best = menu[menu["bestseller"] == 1]

            if best.empty:
                return "Hiện chưa có dữ liệu món best seller."

            lines = []
            for _, r in best.head(8).iterrows():
                lines.append(
                    f"• {r['name']}: {money(r['price'])}"
                )

            return (
                "⭐ Những món được quán đánh dấu best seller "
                "trong menu hiện tại:\n" + "\n".join(lines)
            )

        if any(x in q for x in [
            "combo", "đi nhóm", "đi gia đình", "đi hai người"
        ]):
            combos = menu[
                (menu["category"] == "Combo")
                & (menu["active"] == 1)
            ]

            lines = [
                f"• {r['name']}: {money(r['price'])}"
                for _, r in combos.iterrows()
            ]

            return (
                "🎎 Bạn có thể tham khảo các combo sau:\n"
                + "\n".join(lines)
                + "\nGiá và thành phần combo hiện là dữ liệu mẫu; "
                "hãy kiểm tra lại trước khi tư vấn khách."
            )

        if any(x in q for x in [
            "voucher", "giảm giá", "khuyến mãi", "mã giảm"
        ]):
            return (
                "🎟️ Các voucher đang được cấu hình trong app:\n"
                "• N2WELCOME: giảm 10%, tối đa 50.000đ.\n"
                "• SUSHI20: giảm 20.000đ cho đơn từ 200.000đ.\n"
                "• N2VIP: giảm 15%, tối đa 100.000đ cho đơn từ 500.000đ.\n"
                "Nhập mã tại mục thanh toán để kiểm tra điều kiện."
            )

        if any(x in q for x in [
            "tích điểm", "điểm", "thành viên", "thân thiết"
        ]):
            return (
                "🌟 Chính sách tích điểm hiện tại của app mẫu: "
                "mỗi 10.000đ thanh toán được cộng 1 điểm. "
                "Điểm được lưu theo số điện thoại khi thanh toán."
            )

        if any(x in q for x in [
            "menu", "thực đơn", "có món gì", "giá món"
        ]):
            lines = []

            for category in [
                "Sushi", "Sashimi", "Món nóng",
                "Combo", "Thức uống"
            ]:
                subset = menu[
                    (menu["category"] == category)
                    & (menu["active"] == 1)
                ]

                if not subset.empty:
                    lines.append(f"\n{category}:")
                    for _, r in subset.head(5).iterrows():
                        lines.append(
                            f"• {r['name']}: {money(r['price'])}"
                        )

            return "🍱 Menu N2 Sushi:\n" + "\n".join(lines)

        if any(x in q for x in [
            "sushi", "sashimi", "ramen", "nước",
            "uống", "tempura", "cá hồi", "cơm bò"
        ]):
            matched = menu[
                menu["name"].str.lower().str.contains(
                    q.replace("giá", "").strip(),
                    regex=False,
                    na=False
                )
            ]

            if not matched.empty:
                lines = [
                    f"• {r['name']}: {money(r['price'])}"
                    for _, r in matched.head(10).iterrows()
                ]

                return "🍣 Món phù hợp với câu hỏi của bạn:\n" + "\n".join(lines)

            category_map = {
                "sushi": "Sushi",
                "sashimi": "Sashimi",
                "ramen": "Món nóng",
                "tempura": "Món nóng",
                "nước": "Thức uống",
                "uống": "Thức uống"
            }

            for keyword, category in category_map.items():
                if keyword in q:
                    subset = menu[
                        (menu["category"] == category)
                        & (menu["active"] == 1)
                    ]

                    return (
                        f"🍱 Một số lựa chọn thuộc nhóm {category}:\n"
                        + "\n".join([
                            f"• {r['name']}: {money(r['price'])}"
                            for _, r in subset.head(8).iterrows()
                        ])
                    )

        return (
            "Mình chưa hiểu rõ câu hỏi này. 😊 Bạn thử hỏi:\n"
            "• N2 Sushi mở cửa lúc mấy giờ?\n"
            "• Địa chỉ quán ở đâu?\n"
            "• Món nào best seller?\n"
            "• Có combo nào cho 2 người?\n"
            "• Voucher nào đang dùng được?\n"
            "• Giá sushi cá hồi bao nhiêu?\n\n"
            "Mình hiện trả lời theo dữ liệu trong database của quán."
        )

    # Hiển thị lịch sử hội thoại
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user">👤 '
                f'{html.escape(msg["content"]).replace(chr(10), "<br>")}'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="chat-bubble">🍣 '
                f'{html.escape(msg["content"]).replace(chr(10), "<br>")}'
                f'</div>',
                unsafe_allow_html=True
            )

    # Các câu hỏi gợi ý nhanh
    st.markdown("### ⚡ Câu hỏi nhanh")

    quick_cols = st.columns(3)

    quick_questions = [
        "Giờ mở cửa",
        "Món best seller",
        "Voucher",
        "Địa chỉ quán",
        "Combo cho 2 người",
        "Menu"
    ]

    for i, question in enumerate(quick_questions):
        with quick_cols[i % 3]:
            if st.button(
                question,
                key=f"quick_{i}",
                use_container_width=True
            ):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": question
                })

                answer = chatbot_reply(question)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

                st.rerun()

    with st.form("chat_form", clear_on_submit=True):
        user_question = st.text_input(
            "Nhập câu hỏi",
            placeholder="VD: Món nào ngon nhất ở N2 Sushi?"
        )

        send = st.form_submit_button(
            "Gửi tin nhắn ✉️",
            use_container_width=True
        )

        if send and user_question.strip():
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question.strip()
            })

            answer = chatbot_reply(user_question)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })

            st.rerun()

    if st.button("🗑️ Xóa hội thoại"):
        st.session_state.chat_history = []
        st.rerun()

# =========================================================
# 13. FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; padding:12px; color:#887b6c">
        <b style="color:#7d1f2a">🍣 N2 SUSHI</b><br>
        Japanese Dining · Fresh Taste · Premium Experience<br>
        <small>Hệ thống quản lý đơn hàng & tích điểm khách hàng</small>
    </div>
    """,
    unsafe_allow_html=True
)
