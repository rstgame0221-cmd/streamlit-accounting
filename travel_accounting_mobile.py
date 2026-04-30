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
st.subheader("📋 記帳列表")

for i, row in df.iterrows():

    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,2,3,2])

        with col1:
            st.write(row["date"])
        with col2:
            st.write(row["category"])
        with col3:
            st.write(f"{row['amount']} {row['currency']}")
        with col4:
            st.write(row["payment_method"])
        with col5:
            st.write(row["description"])

        # ======================
        # 修改
        # ======================
        with col6:
            edit = st.button("✏️", key=f"edit_{row['id']}")
            delete = st.button("🗑", key=f"del_{row['id']}")

        # 刪除
        if delete:
            supabase.table("expenses").delete().eq("id", row["id"]).execute()
            st.rerun()

        # 修改
        if edit:
            st.session_state["edit_id"] = row["id"]
            st.session_state["edit_data"] = row

# ======================
# 編輯區
# ======================
if "edit_id" in st.session_state:

    st.divider()
    st.subheader("✏️ 編輯資料")

    edit = st.session_state["edit_data"]

    new_date = st.date_input("日期", value=pd.to_datetime(edit["date"]))
    new_category = st.selectbox("類別", ["交通","住宿","餐飲","門票","購物","其他"], index=0)
    new_amount = st.number_input("金額", value=float(edit["amount"]))
    new_currency = st.selectbox("幣別", ["JPY","TWD","USD","EUR"])
    new_payment = st.selectbox("付款方式", ["現金","信用卡"])
    new_desc = st.text_input("備註", value=edit["description"])

    if st.button("儲存修改"):
        supabase.table("expenses").update({
            "date": str(new_date),
            "category": new_category,
            "amount": new_amount,
            "currency": new_currency,
            "payment_method": new_payment,
            "description": new_desc
        }).eq("id", st.session_state["edit_id"]).execute()

        del st.session_state["edit_id"]
        st.rerun()

# ======================
# 匯出 CSV
# ======================
st.divider()
st.subheader("📤 匯出資料")

csv = df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "下載 CSV",
    csv,
    "expenses.csv",
    "text/csv"
)