import streamlit as st
import datetime
from supabase import create_client
from collections import defaultdict
import pandas as pd

# ======================
# Supabase 連線
# ======================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.set_page_config(page_title="家庭記帳", layout="centered")

st.title("💰 家庭旅遊記帳")

# ======================
# CSS 卡片
# ======================
st.markdown("""
<style>
.card {
    border: 1px solid #e6e6e6;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 10px;
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.amount {
    font-size: 18px;
    font-weight: bold;
}

.small {
    font-size: 13px;
    color: #666;
}

.row {
    display: flex;
    justify-content: space-between;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

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
        st.rerun()

# ======================
# 讀資料
# ======================
data = supabase.table("expenses").select("*").order("date", desc=True).execute()
rows = data.data or []

if not rows:
    st.info("目前沒有資料")
    st.stop()

# ======================
# 分組（依日期）
# ======================
grouped = defaultdict(list)

for r in rows:
    grouped[r["date"]].append(r)

# ======================
# Card UI 列表
# ======================
st.subheader("📋 記帳列表")

for date, items in grouped.items():

    with st.expander(f"📅 {date}（{len(items)} 筆）"):

        for item in items:

            st.markdown(f"""
<div class="card">

<div class="amount">💰 {item['amount']} {item['currency']}</div>

<div class="row">
    <div>🏷️ {item['category']}</div>
    <div>💳 {item['payment_method']}</div>
</div>

<div class="small">📝 {item['description']}</div>

</div>
""", unsafe_allow_html=True)

btn1, btn2 = st.columns([1,1], gap="small")

with btn1:
    st.button("✏️ 修改", key=f"edit_{item['id']}")

with btn2:
    st.button("🗑 刪除", key=f"del_{item['id']}")

# ======================
# 修改功能
# ======================
if "edit" in st.session_state:

    st.divider()
    st.subheader("✏️ 修改資料")

    e = st.session_state["edit"]

    new_date = st.date_input("日期", value=datetime.datetime.strptime(e["date"], "%Y-%m-%d").date())
    new_category = st.selectbox("類別", ["交通","住宿","餐飲","門票","購物","其他"])
    new_amount = st.number_input("金額", value=float(e["amount"]))
    new_currency = st.selectbox("幣別", ["JPY","TWD","USD","EUR"])
    new_payment = st.selectbox("付款方式", ["現金","信用卡"])
    new_desc = st.text_input("備註", value=e["description"])

    if st.button("💾 儲存修改"):
        supabase.table("expenses").update({
            "date": str(new_date),
            "category": new_category,
            "amount": new_amount,
            "currency": new_currency,
            "payment_method": new_payment,
            "description": new_desc
        }).eq("id", e["id"]).execute()

        del st.session_state["edit"]
        st.rerun()

# ======================
# 匯出 CSV
# ======================
st.divider()
st.subheader("📤 匯出")

df = pd.DataFrame(rows)

csv = df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "下載 CSV",
    csv,
    "expenses.csv",
    "text/csv"
)