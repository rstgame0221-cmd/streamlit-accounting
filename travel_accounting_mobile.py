import streamlit as st
import datetime
import pandas as pd

from supabase import create_client
from collections import defaultdict

# ======================
# Page
# ======================

st.set_page_config(
    page_title="家庭旅遊記帳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ======================
# CSS
# ======================

st.markdown("""
<style>

.block-container {
    padding-top: 1rem;
    padding-bottom: 4rem;
}

input {
    font-size: 20px !important;
}

button {
    height: 48px !important;
    border-radius: 12px !important;
}

.card {
    border: 1px solid #e6e6e6;
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.amount {
    font-size: 24px;
    font-weight: bold;
}

.small {
    font-size: 13px;
    color: #666;
}

</style>
""", unsafe_allow_html=True)

# ======================
# Supabase
# ======================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ======================
# Title
# ======================

st.title("💰 家庭旅遊記帳")

# ======================
# 新增資料
# ======================

with st.form("add_form"):

    date = st.date_input(
        "日期",
        value=datetime.date.today()
    )

    categories = ["交通", "住宿", "餐飲", "門票", "購物", "其他"]

    category = st.selectbox("類別", categories)

    amount = st.text_input(
        "金額",
        placeholder="輸入數字"
    )

    currency = st.selectbox(
        "幣別",
        ["JPY", "TWD", "USD", "EUR"]
    )

    payment = st.selectbox(
        "付款方式",
        ["現金", "信用卡"]
    )

    desc = st.text_input("備註")

    submit = st.form_submit_button("➕ 新增")

    if submit:

        try:
            supabase.table("expenses").insert({
                "date": str(date),
                "category": category,
                "amount": float(amount),
                "currency": currency,
                "payment_method": payment,
                "description": desc
            }).execute()

            st.success("已新增")
            st.rerun()

        except Exception as e:
            st.error(f"新增失敗：{e}")

# ======================
# 讀資料
# ======================

data = supabase.table("expenses") \
    .select("*") \
    .order("date", desc=True) \
    .execute()

rows = data.data or []

if not rows:
    st.info("目前沒有資料")
    st.stop()

df = pd.DataFrame(rows)

# ======================
# 統計
# ======================

st.subheader("📊 總支出")

st.metric("總計", f"{df['amount'].sum():,.0f}")

# ======================
# 幣別統計
# ======================

st.subheader("💱 幣別統計")

currency_summary = df.groupby("currency")["amount"].sum()

cols = st.columns(len(currency_summary))

for idx, (cur, total) in enumerate(currency_summary.items()):
    cols[idx].metric(cur, f"{total:,.0f}")

# ======================
# 列表
# ======================

st.subheader("📋 記帳列表")

grouped = defaultdict(list)

for r in rows:
    grouped[r["date"]].append(r)

for date in sorted(grouped.keys(), reverse=True):

    st.markdown(f"### 📅 {date}")

    for item in grouped[date]:

        st.markdown(f"""
<div class="card">

<div class="amount">
💰 {item['amount']:,.0f} {item['currency']}
</div>

<div>
🏷️ {item['category']} ｜ 💳 {item['payment_method']}
</div>

<div class="small">
📝 {item.get('description', '')}
</div>

</div>
""", unsafe_allow_html=True)

# ======================
# 圖表
# ======================

st.divider()

st.subheader("📈 類別統計")

chart_data = df.groupby("category")["amount"].sum()

st.bar_chart(chart_data)

# ======================
# CSV
# ======================

st.divider()

st.subheader("📤 匯出資料")

st.download_button(
    "下載 CSV",
    df.to_csv(index=False).encode("utf-8-sig"),
    "expenses.csv",
    "text/csv"
)