import streamlit as st
from supabase import create_client
import datetime

# ======================
# 連線 Supabase
# ======================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.set_page_config(page_title="家庭旅遊記帳", layout="centered")

st.title("💰 家庭旅遊記帳（Supabase版）")

# ======================
# 輸入區
# ======================
date = st.date_input("日期", value=datetime.date.today())
category = st.selectbox("類別", ["交通", "住宿", "餐飲", "門票", "購物", "其他"])
amount = st.number_input("金額", min_value=0.0, step=1.0)  # 手機會自動數字鍵盤
currency = st.selectbox("幣別", ["JPY", "TWD", "USD", "EUR"])
payment = st.selectbox("付款方式", ["現金", "信用卡"])
desc = st.text_input("備註")

# ======================
# 新增資料
# ======================
if st.button("新增支出"):
    supabase.table("expenses").insert({
        "date": str(date),
        "category": category,
        "amount": amount,
        "currency": currency,
        "payment_method": payment,
        "description": desc
    }).execute()

    st.success("✔ 已新增到 Supabase")

# ======================
# 讀取資料
# ======================
st.divider()
st.subheader("📋 記帳列表（依日期）")

data = supabase.table("expenses") \
    .select("*") \
    .order("date", desc=True) \
    .execute()

rows = data.data or []

if not rows:
    st.info("目前沒有資料")
else:
    # 去重
    unique = {r["id"]: r for r in rows}
    clean_rows = list(unique.values())

    # ======================
    # 依日期分組
    # ======================
    grouped = {}

    for r in clean_rows:
        grouped.setdefault(r["date"], []).append(r)

    # ======================
    # 顯示（每日折疊）
    # ======================
    for date, items in grouped.items():
        total = sum(float(i["amount"]) for i in items)

        with st.expander(f"📅 {date} ｜ {len(items)} 筆 ｜ 總額 {total}"):

            for r in items:
                st.write(
                    f"🏷️ {r['category']} ｜ "
                    f"💰 {r['amount']} {r['currency']} ｜ "
                    f"💳 {r['payment_method']} ｜ "
                    f"📝 {r['description']}"
                )