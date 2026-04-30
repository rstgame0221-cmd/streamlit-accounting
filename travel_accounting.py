import datetime
import sqlite3
import re
from pathlib import Path
from dataclasses import dataclass

import streamlit as st
from PIL import Image

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# =========================
# 🗄 DB
# =========================
DB = Path("expenses.db")


@dataclass
class Expense:
    id: int | None
    date: str
    category: str
    amount: float
    currency: str
    payment: str
    desc: str


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            currency TEXT,
            payment TEXT,
            desc TEXT
        )
    """)
    conn.commit()
    conn.close()


def load():
    init_db()
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id,date,category,amount,currency,payment,desc FROM expenses ORDER BY date DESC"
    ).fetchall()
    conn.close()
    return [Expense(*r) for r in rows]


def add(e: Expense):
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT INTO expenses(date,category,amount,currency,payment,desc)
        VALUES (?,?,?,?,?,?)
    """, (e.date, e.category, e.amount, e.currency, e.payment, e.desc))
    conn.commit()
    conn.close()


def delete(exp_id: int):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM expenses WHERE id=?", (exp_id,))
    conn.commit()
    conn.close()


# =========================
# 🤖 OCR
# =========================
def parse(text: str):
    result = {
        "date": "",
        "amount": "",
        "desc": ""
    }

    m = re.search(r"(\d{4})[\/\-年](\d{1,2})[\/\-月](\d{1,2})", text)
    if m:
        y, mth, d = m.groups()
        result["date"] = f"{y}-{mth.zfill(2)}-{d.zfill(2)}"

    a = re.search(r"([0-9,]+)\s*円|￥\s*([0-9,]+)", text)
    if a:
        amt = a.group(1) or a.group(2)
        result["amount"] = amt.replace(",", "")

    result["desc"] = text.splitlines()[0][:30] if text else ""

    return result


# =========================
# 🎨 UI
# =========================
def style():
    st.markdown("""
    <style>
    .block-container {
        padding: 1rem;
    }

    .card {
        padding: 10px;
        border-radius: 12px;
        background: #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 8px;
    }

    h1, h2 {
        font-size: 20px !important;
    }

    </style>
    """, unsafe_allow_html=True)


# =========================
# 🚀 APP
# =========================
def main():
    st.set_page_config(page_title="記帳App", layout="centered")

    style()
    init_db()

    if "data" not in st.session_state:
        st.session_state.data = load()

    st.title("📱 記帳 App")

    # =========================
    # 📊 Summary
    # =========================
    if st.session_state.data:
        total = sum(x.amount for x in st.session_state.data)

        col1, col2 = st.columns(2)
        col1.metric("💰 總支出", int(total))
        col2.metric("📋 筆數", len(st.session_state.data))
    else:
        st.info("尚無資料")

    st.divider()

    # =========================
    # ➕ Add
    # =========================
    st.subheader("➕ 新增")

    with st.form("f"):
        c1, c2 = st.columns(2)

        date = c1.date_input("日期", datetime.date.today())
        cat = c2.selectbox("類別", ["交通", "住宿", "餐飲", "購物", "門票", "其他"])

        amt = st.text_input("金額")
        cur = st.selectbox("幣別", ["JPY", "TWD", "USD"])
        pay = st.selectbox("付款", ["現金", "信用卡"])
        desc = st.text_input("備註")

        if st.form_submit_button("新增"):
            try:
                e = Expense(
                    None,
                    date.isoformat(),
                    cat,
                    float(amt),
                    cur,
                    pay,
                    desc
                )
                add(e)
                st.session_state.data = load()
                st.rerun()
            except:
                st.error("金額錯誤")

    st.divider()

    # =========================
    # 📷 OCR
    # =========================
    st.subheader("📷 掃描發票")

    file = st.file_uploader("上傳圖片", type=["jpg", "png"])

    if file:
        img = Image.open(file)
        st.image(img, use_column_width=True)

        if OCR_AVAILABLE:
            text = pytesseract.image_to_string(img, lang="jpn+eng")
            st.text_area("OCR", text, height=100)

            p = parse(text)

            st.write(p)

            if st.button("用OCR新增"):
                if p["amount"]:
                    e = Expense(
                        None,
                        p["date"] or datetime.date.today().isoformat(),
                        "其他",
                        float(p["amount"]),
                        "JPY",
                        "現金",
                        p["desc"]
                    )
                    add(e)
                    st.session_state.data = load()
                    st.rerun()

    st.divider()

    # =========================
    # 📋 List (mobile card UI)
    # =========================
    st.subheader("📋 記錄")

    for e in st.session_state.data:
        st.markdown(f"""
        <div class="card">
        📅 {e.date}<br>
        🏷 {e.category}<br>
        💰 {int(e.amount)} {e.currency}<br>
        📝 {e.desc}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑 刪除", key=f"d{e.id}"):
            delete(e.id)
            st.session_state.data = load()
            st.rerun()

    # =========================
    # 📤 Export
    # =========================
    st.divider()
    st.subheader("📤 匯出")

    if st.session_state.data:
        csv = "date,category,amount,currency,payment,desc\n"
        for e in st.session_state.data:
            csv += f"{e.date},{e.category},{e.amount},{e.currency},{e.payment},{e.desc}\n"

        st.download_button("下載 CSV", csv, file_name="expense.csv")


if __name__ == "__main__":
    main()