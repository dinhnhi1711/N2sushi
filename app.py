def format_price(price):
    return f"{int(price):,}".replace(",", ".") + "đ"


def normalize_text(text):
    text = unicodedata.normalize("NFD", str(text).lower())
    return "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )


def calculate_subtotal():
    subtotal = 0
    for item_id, quantity in st.session_state.cart.items():
        item = MENU_BY_ID.get(item_id)
        if item:
            subtotal += item["price"] * quantity
    return subtotal


def calculate_discount(subtotal, voucher_code):
    if not voucher_code:
        return 0

    voucher = VOUCHERS.get(voucher_code.upper().strip())
    if not voucher or subtotal < voucher["minimum"]:
        return 0

    if voucher["type"] == "percent":
        return min(
            int(subtotal * voucher["value"] / 100),
            voucher["max_discount"],
        )

    return min(voucher["value"], subtotal)


def get_cart_items():
    items = []
    for item_id, quantity in st.session_state.cart.items():
        item = MENU_BY_ID.get(item_id)
        if not item:
            continue

        items.append({
            "id": item_id,
            "name": item["name"],
            "price": item["price"],
            "quantity": quantity,
            "note": st.session_state.notes.get(item_id, ""),
            "total": item["price"] * quantity,
        })
    return items


# =========================================================
# 7. CHATBOT - NHẬN DIỆN Ý ĐỊNH
# =========================================================

def find_menu_items_in_message(message):
    normalized_message = normalize_text(message)
    matches = []

    for item in MENU:
        normalized_name = normalize_text(item["name"])
        if normalized_name and normalized_name in normalized_message:
            matches.append(item)

    return matches


def local_chatbot(question):
    text = normalize_text(question)

    if any(word in text for word in [
        "xin chao", "chao ban", "hello", "hi", "alo"
    ]):
        return (
            f"Xin chào bạn! 🍣 Mình là trợ lý của {RESTAURANT_NAME}. "
            "Bạn muốn xem menu, hỏi giá món, combo hay voucher?"
        )

    if any(word in text for word in [
        "dia chi", "o dau", "chi nhanh", "vi tri", "duong nao"
    ]):
        return f"📍 Địa chỉ quán: {RESTAURANT_ADDRESS}."

    if any(word in text for word in [
        "gio mo cua", "may gio", "gio dong cua", "mo cua", "dong cua"
    ]):
        return f"⏰ Giờ mở cửa: {RESTAURANT_HOURS}."

    if any(word in text for word in [
        "hotline", "so dien thoai", "lien he", "goi dien"
    ]):
        return f"☎️ Hotline {RESTAURANT_NAME}: {RESTAURANT_PHONE}."

    if any(word in text for word in [
        "voucher", "khuyen mai", "giam gia", "uu dai", "ma giam"
    ]):
        return (
            "🎁 Các voucher hiện có:\n"
            "- **N2WELCOME**: giảm 10%, tối đa 100.000đ, "
            "áp dụng từ đơn 200.000đ.\n"
            "- **N2SAVE50**: giảm 50.000đ, áp dụng từ đơn 300.000đ.\n"
            "- **N2VIP**: giảm 15%, tối đa 150.000đ, "
            "áp dụng từ đơn 500.000đ."
        )

    if any(word in text for word in [
        "combo", "di 2 nguoi", "di 3 nguoi", "di gia dinh",
        "di nhom", "di 4 nguoi", "di 5 nguoi"
    ]):
        combos = [
            item for item in MENU
            if item["category"] == "Combo"
        ]
        lines = ["🍱 Các combo của quán:"]
        for item in combos:
            lines.append(
                f"- **{item['name']}**: {format_price(item['price'])} "
                f"({item['description']})."
            )
        lines.append(
            "Bạn cho mình biết đi mấy người để mình tư vấn phù hợp hơn nha!"
        )
        return "\n".join(lines)

    if any(word in text for word in [
        "menu", "thuc don", "co mon gi", "ban gi", "xem mon"
    ]):
        lines = ["🍣 **Menu N2 Sushi**"]
        categories = list(dict.fromkeys(
            item["category"] for item in MENU
        ))
        for category in categories:
            lines.append(f"\n**{category}:**")
            for item in MENU:
                if item["category"] == category:
                    lines.append(
                        f"- {item['name']}: {format_price(item['price'])}"
                    )
        return "\n".join(lines)

    matched_items = find_menu_items_in_message(question)
    if matched_items:
        lines = ["🍣 Mình tìm thấy món bạn hỏi:"]
        for item in matched_items:
            lines.append(
                f"- **{item['name']}** — {format_price(item['price'])}. "
                f"{item['description']}."
            )
        return "\n".join(lines)

    if any(word in text for word in [
        "gia", "bao nhieu", "bao tien", "dat khong", "re khong"
    ]):
        return (
            "Bạn muốn hỏi giá món nào vậy? Hãy gửi tên món cụ thể, "
            "mình sẽ tra giá trên menu cho bạn nha. 🍣"
        )

    if any(word in text for word in [
        "cam on", "thanks", "thank you"
    ]):
        return "Không có gì nha bạn! 💖 N2 Sushi luôn sẵn sàng hỗ trợ."

    return (
        "Mình có thể giúp bạn xem menu, tra giá món, tìm combo, "
        "kiểm tra voucher, địa chỉ và giờ mở cửa. 🍣 "
        "Bạn muốn hỏi thông tin nào?"
    )


def get_recent_chat_history(limit=8):
    return st.session_state.chat_messages[-limit:]


def chatbot_reply(question):
    """Ưu tiên AI qua OpenRouter; lỗi API thì chuyển sang chatbot cục bộ."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if not api_key:
        return local_chatbot(question)

    menu_text = "\n".join(
        f"- {item['name']} | {item['category']} | "
        f"{format_price(item['price'])} | {item['description']}"
        for item in MENU
    )

    voucher_text = (
        "N2WELCOME: giảm 10%, tối đa 100.000đ, đơn tối thiểu 200.000đ.\n"
        "N2SAVE50: giảm 50.000đ, đơn tối thiểu 300.000đ.\n"
        "N2VIP: giảm 15%, tối đa 150.000đ, đơn tối thiểu 500.000đ."
    )

    system_prompt = f"""
Bạn là trợ lý tư vấn khách hàng thân thiện của {RESTAURANT_NAME}.

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
- Luôn trả lời bằng tiếng Việt, ngắn gọn, thân thiện.
- Chỉ cung cấp giá và thông tin dựa trên dữ liệu bên trên.
- Không tự bịa món ăn, giá, chương trình khuyến mãi hoặc chính sách.
- Nếu khách hỏi món cụ thể, nêu đúng giá và mô tả trong menu.
- Nếu không biết câu trả lời, hướng dẫn khách liên hệ nhân viên.
- Có thể gợi ý combo theo số người và ngân sách khách nêu.
- Không tự tuyên bố đã đặt món hoặc thanh toán thay khách.
"""

    messages = [{"role": "system", "content": system_prompt}]

    for entry in get_recent_chat_history():
        role = entry.get("role")
        content = entry.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({
                "role": role,
                "content": content,
            })

    messages.append({
        "role": "user",
        "content": question,
    })

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
                "messages": messages,
                "temperature": 0.3,
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        if not isinstance(answer, str) or not answer.strip():
            return local_chatbot(question)

        return answer.strip()

    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return local_chatbot(question)


# =========================================================
# 8. CSS
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

def normalize_text(value):
    """Chuẩn hóa chữ thường và bỏ dấu để nhận diện câu hỏi linh hoạt hơn."""
    value = str(value or "").lower().strip()
    value = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn").replace("đ", "d")


def find_menu_matches(question):
    q = normalize_text(question)
    matches = []
    for item in MENU:
        name = normalize_text(item["name"])
        words = [w for w in name.split() if len(w) > 2]
        if name in q or (words and sum(w in q for w in words) >= max(1, len(words) - 1)):
            matches.append(item)
    return matches


def local_chatbot(question):
    """Chế độ dự phòng không cần API; trả lời dựa trên menu và dữ liệu quán."""
    q = normalize_text(question)

    if any(k in q for k in ["xin chao", "hello", "hi ", "chao ban", "hey"]):
        return "Xin chào 👋 Mình là N2 Assistant. Bạn muốn xem menu, tìm món, hỏi combo, voucher hay thông tin quán nè?"

    if any(k in q for k in ["best seller", "best-seller", "ban chay", "mon hot", "mon duoc yeu thich"]):
        names = [f"- {x['name']} — {money(x['price'])}" for x in MENU if x["best"]]
        return "⭐ **Best seller của N2 Sushi:**\n\n" + "\n".join(names)

    if any(k in q for k in ["voucher", "khuyen mai", "uu dai", "giam gia", "ma giam"]):
        return ("🎁 **Voucher hiện có:**\n\n"
                "- **N2WELCOME:** giảm 10%, tối đa 100.000đ, đơn tối thiểu 200.000đ.\n"
                "- **N2SAVE50:** giảm 50.000đ, đơn tối thiểu 300.000đ.\n"
                "- **N2VIP:** giảm 15%, tối đa 150.000đ, đơn tối thiểu 500.000đ.")

    if any(k in q for k in ["dia chi", "o dau", "dia diem", "duong nao"]):
        return f"📍 **Địa chỉ N2 Sushi:**\n\n{RESTAURANT_ADDRESS}"

    if any(k in q for k in ["gio mo cua", "mo cua", "dong cua", "may gio", "thoi gian hoat dong"]):
        return f"🕐 **Giờ mở cửa:**\n\n{RESTAURANT_HOURS}"

    if any(k in q for k in ["so dien thoai", "hotline", "lien he", "sdt"]):
        return f"📞 **Hotline N2 Sushi:**\n\n{RESTAURANT_PHONE}"

    # Gợi ý combo theo số người kể cả cách viết không dấu.
    if "2 nguoi" in q or "hai nguoi" in q or "cap doi" in q:
        return "👫 **Combo N2 Couple — 299.000đ**, dành cho 2 người. Bạn có thể gọi thêm nước uống tùy sở thích nha."

    if "3 nguoi" in q or "ba nguoi" in q:
        return "👨‍👩‍👧 **Combo N2 Family — 429.000đ**, dành cho 3 người."

    if any(k in q for k in ["4-5 nguoi", "4 5 nguoi", "4 nguoi", "5 nguoi", "nhom dong"]):
        return "👨‍👩‍👧‍👦 **Combo N2 Party — 649.000đ**, dành cho 4–5 người."

    matches = find_menu_matches(question)
    if matches:
        lines = [
            f"- **{m['name']}** ({m['category']}): "
            f"{money(m['price'])} — {m['description']}."
            for m in matches[:5]
        ]
        return "🍣 Mình tìm thấy món này trong menu N2 Sushi nè:\n\n" + "\n".join(lines)

    if any(k in q for k in ["menu", "co mon gi", "mon an", "thuc don", "gia mon"]):
        categories = {}
        for item in MENU:
            categories.setdefault(item["category"], []).append(item)

        lines = []
        for cat, items in categories.items():
            lines.append(
                f"**{cat}:** " + ", ".join(
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
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return local_chatbot(question)

    # Đưa dữ liệu menu/voucher và vài lượt hội thoại gần nhất vào ngữ cảnh.
    menu_text = "\n".join(
        f"{item['name']} | danh mục: {item['category']} | "
        f"giá: {money(item['price'])} | mô tả: {item['description']} | "
        f"best seller: {'có' if item['best'] else 'không'}"
        for item in MENU
    )

    voucher_text = "\n".join(
        f"{code}: giảm {v['value']}{'%' if v['type'] == 'percent' else 'đ'}, "
        f"tối đa {money(v['max_discount'])}, "
        f"đơn tối thiểu {money(v['minimum'])}"
        for code, v in VOUCHERS.items()
    )

    system_prompt = f"""Bạn là trợ lý AI chính thức của N2 Sushi, trả lời bằng tiếng Việt tự nhiên, thân thiện, ngắn gọn.
THÔNG TIN ĐÃ XÁC NHẬN:
Tên: {RESTAURANT_NAME}
Địa chỉ: {RESTAURANT_ADDRESS}
Điện thoại: {RESTAURANT_PHONE}
Giờ mở cửa: {RESTAURANT_HOURS}

MENU:
{menu_text}

VOUCHER:
{voucher_text}

QUY TẮC:
- Chỉ khẳng định giá, thành phần, ưu đãi và thông tin có trong dữ liệu trên.
- Combo N2 Couple 299.000đ cho 2 người; N2 Family 429.000đ cho 3 người; N2 Party 649.000đ cho 4-5 người.
- Khi khách hỏi gợi ý món, hãy hỏi hoặc cân nhắc số người/ngân sách/sở thích nếu cần; ưu tiên gợi ý món có thật trong menu.
- Hiểu câu hỏi tiếp nối dựa vào lịch sử hội thoại, nhưng không tự suy đoán dữ liệu cá nhân hay tình trạng đơn hàng.
- Nếu không có thông tin, nói rõ chưa có dữ liệu và hướng khách liên hệ nhân viên; tuyệt đối không bịa.
"""

    history = []
    for message in st.session_state.get("chat_messages", [])[-8:]:
        role = "assistant" if message.get("role") == "assistant" else "user"
        history.append({
            "role": role,
            "content": str(message.get("content", ""))[:2000],
        })

    # Tránh gửi lại câu hỏi hiện tại nếu nó đã được thêm vào session_state.
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

section[data-testid="stSidebar"] label {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] {
    color: #ffffff;
}

/* ===== Ô NHẬP CHATBOT ===== */

section[data-testid="stSidebar"] div[data-testid="stChatInput"] textarea,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] [contenteditable="true"] {
    background: #ffffff !important;
    color: #b31d1d !important;
    -webkit-text-fill-color: #b31d1d !important;
    caret-color: #b31d1d !important;
    border: 2px solid #d9b9ae !important;
    border-radius: 14px !important;
    font-size: 13px !important;
}

section[data-testid="stSidebar"] div[data-testid="stChatInput"] textarea:focus,
section[data-testid="stSidebar"] textarea:focus {
    background: #ffffff !important;
    color: #b31d1d !important;
    -webkit-text-fill-color: #b31d1d !important;
    border-color: #d13a32 !important;
    box-shadow: 0 0 0 2px rgba(209, 58, 50, 0.18) !important;
}

section[data-testid="stSidebar"] div[data-testid="stChatInput"] textarea::placeholder,
section[data-testid="stSidebar"] textarea::placeholder {
    color: #a18d86 !important;
    -webkit-text-fill-color: #a18d86 !important;
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
    border-radius: 15px 15px 4px 15px;
    margin: 8px 0 8px 20px;
    font-size: 12px;
    line-height: 1.55;
}

.chat-bot {
    background: #3a2723;
    color: #ffffff;
    padding: 11px 13px;
    border-radius: 15px 15px 15px 4px;
    margin: 8px 20px 8px 0;
    font-size: 12px;
    line-height: 1.55;
    border: 1px solid #513832;
}

/* Sidebar button */

section[data-testid="stSidebar"] .stButton > button {
    background: #3a2723 !important;
    color: #ffffff !important;
    border: 1px solid #5a3d36 !important;
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
    padding: 35px 0 15px;
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
<div class="info-label">ĐỊA CHỈ</div>
<div class="info-value">📍 N2 Sushi</div>
<div style="font-size:11px;color:#8f7b74;margin-top:5px;">
{RESTAURANT_ADDRESS}
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
        if message["role"] == "user":
            safe_chat_content = html.escape(
                str(message["content"])
            ).replace("\n", "<br>")

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
            content = html.escape(
                str(message["content"])
            ).replace("\n", "<br>")

            html_markdown(
                f"""
<div class="chat-bot">
<b>🍣 N2 Sushi</b><br>
{content}
</div>
""",
                unsafe_allow_html=True,
            )

    user_question = st.chat_input("Hỏi N2 Sushi...")

    if user_question:
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_question,
        })
        save_chat_message(
            st.session_state.chat_session_id,
            "user",
            user_question,
        )

        answer = ask_chatbot(user_question)

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": answer,
        })
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
# 16. MENU
# =========================================================

with menu_column:
    html_markdown(
        '<div class="section-title">🍣 Chọn món</div>',
        unsafe_allow_html=True,
    )

    filter1, filter2 = st.columns([1, 2])

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
            item for item in filtered_menu
            if item["category"] == category
        ]

    if search.strip():
        filtered_menu = [
            item for item in filtered_menu
            if search.lower() in item["name"].lower()
        ]

    food_columns = st.columns(2)

    for index, item in enumerate(filtered_menu):
        with food_columns[index % 2]:
            best_badge = ""

            if item["best"]:
                best_badge = (
                    '<span class="best">⭐ BEST SELLER</span>'
                )

            html_markdown(
                f"""
<div class="food-card">
{best_badge}
<div style="height:8px;"></div>
<div class="food-name">{item["name"]}</div>
<div class="food-description">{item["description"]}</div>
<div class="food-price">{money(item["price"])}</div>
<span class="category">{item["category"]}</span>
</div>
""",
                unsafe_allow_html=True,
            )

            if st.button(
                "＋ Thêm vào giỏ",
                key=f"add_{item['id']}",
                use_container_width=True,
            ):
                add_item(item["id"])
                st.rerun()


# =========================================================
# 17. GIỎ HÀNG
# =========================================================

with cart_column:
    html_markdown(
        '<div class="section-title">🛒 Giỏ hàng</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:
        st.info("Giỏ hàng đang trống. Chọn món bạn thích nha!")

    else:
        html_markdown(
            '<div class="cart-card">',
            unsafe_allow_html=True,
        )

        for item_id, quantity in list(st.session_state.cart.items()):
            item = MENU_BY_ID[item_id]

            html_markdown(
                f"""
<div class="cart-item">
<div class="cart-name">{item["name"]}</div>
<div class="cart-price">{money(item["price"] * quantity)}</div>
<div style="font-size:12px;color:#95817a;">
{money(item["price"])} × {quantity}
</div>
</div>
""",
                unsafe_allow_html=True,
            )

            qty_col1, qty_col2, qty_col3 = st.columns([1, 1, 2])

            with qty_col1:
                if st.button(
                    "−",
                    key=f"minus_{item_id}",
                    use_container_width=True,
                ):
                    remove_item(item_id)
                    st.rerun()

            with qty_col2:
                st.write(f"**{quantity}**")

            with qty_col3:
                if st.button(
                    "＋",
                    key=f"plus_{item_id}",
                    use_container_width=True,
                ):
                    add_item(item_id)
                    st.rerun()

            note = st.text_input(
                "Ghi chú món",
                value=st.session_state.notes.get(item_id, ""),
                key=f"note_{item_id}",
                placeholder="VD: ít cay, không hành...",
            )
            st.session_state.notes[item_id] = note

        html_markdown("</div>", unsafe_allow_html=True)

    st.divider()

    subtotal_amount = subtotal()

    html_markdown(
        f"""
<div class="total-card">
<div class="total-label">Tạm tính</div>
<div class="total-number">{money(subtotal_amount)}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    voucher_code = st.text_input(
        "🎁 Mã voucher",
        placeholder="Nhập mã giảm giá...",
    )

    discount_amount, voucher_message = calculate_voucher(
        voucher_code,
        subtotal_amount,
    )

    if voucher_message:
        if discount_amount > 0:
            st.success(voucher_message)
        else:
            st.warning(voucher_message)

    total_amount = max(0, subtotal_amount - discount_amount)

    st.metric("Giảm giá", money(discount_amount))
    st.metric("Tổng thanh toán", money(total_amount))
with info1:
    html_markdown(
        f"""
<div class="info-box">
<div class="info-label">ĐỊA CHỈ</div>
<div class="info-value">📍 N2 Sushi</div>
<div style="font-size:11px;color:#8f7b74;margin-top:5px;">
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
        if message["role"] == "user":
            safe_chat_content = html.escape(
                str(message["content"])
            ).replace("\n", "<br>")

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
            content = html.escape(
                str(message["content"])
            ).replace("\n", "<br>")

            html_markdown(
                f"""
<div class="chat-bot">
<b>🍣 N2 Sushi</b><br>
{content}
</div>
""",
                unsafe_allow_html=True,
            )

    user_question = st.chat_input("Hỏi N2 Sushi...")

    if user_question:
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_question,
        })

        save_chat_message(
            st.session_state.chat_session_id,
            "user",
            user_question,
        )

        answer = ask_chatbot(user_question)

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": answer,
        })

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

menu_column, cart_column = st.columns(
    [1.7, 1],
    gap="large",
)


# =========================================================
# 16. MENU
# =========================================================

with menu_column:
    html_markdown(
        '<div class="section-title">🍣 Chọn món</div>',
        unsafe_allow_html=True,
    )

    filter1, filter2 = st.columns([1, 2])

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
            if search.lower() in item["name"].lower()
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
<div class="food-name">{item['name']}</div>
<div class="food-description">{item['description']}</div>
<span class="category">{item['category']}</span>
<div class="food-price">{money(item['price'])}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            current_quantity = st.session_state.cart.get(
                item["id"],
                0,
            )

            if current_quantity == 0:
                if st.button(
                    "＋  Thêm món",
                    key=f"add_{item['id']}",
                    use_container_width=True,
                ):
                    add_item(item["id"])
                    st.rerun()

            else:
                minus_col, qty_col, plus_col = st.columns([1, 1.2, 1])

                with minus_col:
                    if st.button(
                        "−",
                        key=f"minus_{item['id']}",
                        use_container_width=True,
                    ):
                        remove_item(item["id"])
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
                        add_item(item["id"])
                        st.rerun()

                note_key = f"note_{item['id']}"
                current_note = st.session_state.notes.get(
                    item["id"],
                    "",
                )

                note = st.text_input(
                    "Ghi chú",
                    value=current_note,
                    placeholder="Ít wasabi, không hành...",
                    key=note_key,
                    label_visibility="collapsed",
                )

                st.session_state.notes[item["id"]] = note
                # =========================================================
# 17. GIỎ HÀNG
# =========================================================

with cart_column:
    html_markdown(
        '<div class="section-title">🛒 Đơn hàng</div>',
        unsafe_allow_html=True,
    )

    html_markdown(
        '<div class="cart-card">',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:
        html_markdown(
            """
<div style="text-align:center;padding:35px 10px;color:#9b8881;">
<div style="font-size:45px;">🍣</div>
<div style="font-weight:700;color:#5d4640;margin-top:8px;">
Chưa có món
</div>
<div style="font-size:12px;margin-top:5px;">
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
            line_total = item["price"] * quantity

            html_markdown(
                f"""
<div class="cart-item">
<div style="display:flex;justify-content:space-between;gap:10px;">
<div>
<div class="cart-name">{item['name']}</div>
<div style="font-size:11px;color:#9a8780;margin-top:3px;">
{money(item['price'])} × {quantity}
</div>
</div>
<div class="cart-price">{money(line_total)}</div>
</div>
</div>
""",
                unsafe_allow_html=True,
            )

        html_markdown("<br>", unsafe_allow_html=True)

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
                st.success(voucher_message)
            else:
                st.warning(voucher_message)

        total = max(0, current_subtotal - discount)
        points = loyalty_points(total)

        html_markdown(
            f"""
<div style="display:flex;justify-content:space-between;margin-top:15px;
color:#75615a;font-size:13px;">
<span>Tạm tính</span><b>{money(current_subtotal)}</b>
</div>
<div style="display:flex;justify-content:space-between;margin-top:10px;
color:#198754;font-size:13px;">
<span>Voucher</span><b>- {money(discount)}</b>
</div>
<div style="display:flex;justify-content:space-between;margin-top:10px;
color:#75615a;font-size:13px;">
<span>Điểm tích lũy</span><b>+{points} điểm</b>
</div>
""",
            unsafe_allow_html=True,
        )

        html_markdown(
            f"""
<div class="total-card">
<div class="total-label">TỔNG THANH TOÁN</div>
<div class="total-number">{money(total)}</div>
<div style="font-size:11px;opacity:.72;margin-top:5px;">
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
                errors.append("Vui lòng nhập số bàn.")

            if not customer_name.strip():
                errors.append("Vui lòng nhập tên khách hàng.")

            if not st.session_state.cart:
                errors.append("Chưa có món trong đơn hàng.")

            if errors:
                for error in errors:
                    st.error(error)

            else:
                invoice_items = []

                for item_id, quantity in st.session_state.cart.items():
                    item = MENU_BY_ID[item_id]

                    invoice_items.append({
                        "name": item["name"],
                        "price": item["price"],
                        "quantity": quantity,
                        "note": st.session_state.notes.get(
                            item_id,
                            "",
                        ),
                        "total": item["price"] * quantity,
                    })

                invoice_number = (
                    "N2-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S")
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

                try:
                    save_order_to_database(
                        st.session_state.invoice
                    )
                except sqlite3.IntegrityError:
                    st.error(
                        "Hóa đơn này đã tồn tại trong database. "
                        "Vui lòng kiểm tra lại để tránh lưu trùng."
                    )
                    st.stop()
                except sqlite3.Error as exc:
                    st.error(
                        f"Không thể lưu hóa đơn vào database: {exc}"
                    )
                    st.stop()

                st.success(
                    "🎉 Thanh toán thành công! "
                    "Hóa đơn đã được lưu vào database."
                )
                st.balloons()

    html_markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 18. HÓA ĐƠN
# =========================================================

invoice = st.session_state.invoice

if invoice:
    html_markdown(
        '<div class="section-title">📄 Hóa đơn vừa thanh toán</div>',
        unsafe_allow_html=True,
    )

    invoice_left, invoice_right = st.columns([1.5, 1])

    with invoice_left:
        html_markdown(
            f"""
<div class="info-box">
<h3 style="color:#a51616;margin-top:0;">🍣 N2 SUSHI</h3>
<div style="font-size:12px;color:#75615a;line-height:1.9;">
<b>Mã hóa đơn:</b> {invoice['number']}<br>
<b>Thời gian:</b> {invoice['time'].strftime('%d/%m/%Y %H:%M:%S')}<br>
<b>Số bàn:</b> {invoice['table']}<br>
<b>Khách hàng:</b> {invoice['customer']}<br>
<b>Số điện thoại:</b> {invoice['phone'] or '---'}
</div>
<hr>
""",
            unsafe_allow_html=True,
        )

        for item in invoice["items"]:
            note_html = ""

            if item["note"]:
                note_html = f"""
<div style="font-size:10px;color:#9a8780;margin-top:3px;">
📝 {html.escape(str(item['note']))}
</div>
"""

            html_markdown(
                f"""
<div style="display:flex;justify-content:space-between;padding:10px 0;
border-bottom:1px solid #eee;">
<div>
<b>{html.escape(str(item['name']))}</b>
<div style="font-size:11px;color:#8f7c75;">
SL: {item['quantity']}
</div>
{note_html}
</div>
<div style="font-weight:700;color:#a71919;">
{money(item['total'])}
</div>
</div>
""",
                unsafe_allow_html=True,
            )

        html_markdown("</div>", unsafe_allow_html=True)

    with invoice_right:
        html_markdown(
            f"""
<div class="total-card">
<div class="total-label">TỔNG THANH TOÁN</div>
<div class="total-number">{money(invoice['total'])}</div>
<div style="margin-top:15px;font-size:13px;line-height:1.8;opacity:.88;">
Tạm tính: {money(invoice['subtotal'])}<br>
Voucher: - {money(invoice['discount'])}<br>
Điểm tích lũy: +{invoice['points']} điểm
</div>
</div>
""",
            unsafe_allow_html=True,
        )

        html_markdown("<br>", unsafe_allow_html=True)

        csv_text = (
            "N2 Sushi\n"
            f"Hóa đơn: {invoice['number']}\n"
            f"Khách hàng: {invoice['customer']}\n"
            f"Số bàn: {invoice['table']}\n"
            f"Số điện thoại: {invoice['phone']}\n"
            f"Thời gian: "
            f"{invoice['time'].strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        )

        csv_text += "Món,Số lượng,Đơn giá,Thành tiền,Ghi chú\n"

        for item in invoice["items"]:
            item_name = str(item["name"]).replace('"', '""')
            item_note = str(item["note"]).replace('"', '""')

            csv_text += (
                f'"{item_name}",'
                f'{item["quantity"]},'
                f'{item["price"]},'
                f'{item["total"]},'
                f'"{item_note}"\n'
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
