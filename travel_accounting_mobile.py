import streamlit as st
import datetime
import pandas as pd
from supabase import create_client

# ======================
# Supabase 連線
# ======================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.set_page_config(page_title="家庭記帳", layout="centered")

st.title("💰 家庭記帳系統")

# ======================
# 新增資料
# ======================
with st.form("add_form"):
    date = st.date_input("日期", value=datetime.date.today())
    category = st.selectbox("類別", ["交通", "住宿", "餐飲", "門票", "購物", "其他"])
    amount = st.number_input("金額", min_value=0.0, step=1.0)
    currency = st.selectbox("幣別", ["JPY", "TWD", "USD", "EUR"])
    payment = st.selectbox("付款方式", ["現金", "信用卡"])
    desc = st.text_input("備註")

    submit = st.form_submit_button("新增")

    if submit:
        supabase.table("expenses").insert({
            "date": str(date),
            "category": category,
            "amount": amount,
            "currency": currency,
            "payment_method": payment,
            "description": desc
        }).execute()
        st.success("已新增")

# ======================
# 讀資料
# ======================
data = supabase.table("expenses").select("*").order("date", desc=True).execute()
rows = data.data or []

if not rows:
    st.info("目前沒有資料")
    st.stop()

df = pd.DataFrame(rows)

# ======================
# 刪除 / 修改
# ======================
st.subheader("📋 記帳列表（依日期）")

data = supabase.table("expenses").select("*").order("date", desc=True).execute()
rows = data.data or []

if not rows:
    st.info("目前沒有資料")
    st.stop()

from collections import defaultdict

grouped = defaultdict(list)

for r in rows:
    grouped[r["date"]].append(r)

# ===== 每一天折疊 =====
for date, items in grouped.items():

    with st.expander(f"📅 {date}（{len(items)} 筆）"):

        for item in items:

            col1, col2, col3, col4, col5 = st.columns([2,2,2,3,2])

            with col1:
                st.write(item["category"])

            with col2:
                st.write(f"{item['amount']} {item['currency']}")

            with col3:
                st.write(item["payment_method"])

            with col4:
                st.write(item["description"])

            with col5:
                edit = st.button("✏️", key=f"edit_{item['id']}")
                delete = st.button("🗑", key=f"del_{item['id']}")

            # ===== 刪除 =====
            if delete:
                supabase.table("expenses").delete().eq("id", item["id"]).execute()
                st.rerun()

            # ===== 修改 =====
            if edit:
                st.session_state["edit"] = item
                st.rerun()