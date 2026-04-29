import csv
import datetime
import re
import sqlite3
from dataclasses import dataclass, asdict
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


@dataclass
class TravelExpense:
    id: int | None
    date: str
    category: str
    amount: float
    currency: str
    payment_method: str
    description: str

    def to_row(self):
        return [self.date, self.category, str(int(self.amount)), self.currency, self.payment_method, self.description]


def parse_invoice_text(text: str) -> dict:
    result = {
        "date": "",
        "amount": "",
        "currency": "JPY",
        "description": "",
    }

    date_patterns = [
        r"(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})",
        r"(\d{2})[\-/](\d{1,2})[\-/](\d{1,2})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            year, month, day = match.groups()
            if len(year) == 2:
                year = "20" + year
            try:
                result["date"] = datetime.date(int(year), int(month), int(day)).isoformat()
                break
            except ValueError:
                continue

    amount_patterns = [
        r"(?:(?:合計|請求金額|金額|税込|小計)\s*[:：]?\s*)([¥￥]?\s*[0-9,]+(?:\.[0-9]{1,2})?)",
        r"([¥￥]\s*[0-9,]+)",
        r"([0-9,]+\s*円)",
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, text)
        if match:
            amount_text = match.group(1)
            amount_text = amount_text.replace("¥", "").replace("￥", "").replace("円", "").replace(",", "").strip()
            try:
                result["amount"] = amount_text
                break
            except ValueError:
                continue

    vendor_match = re.search(r"(株式会社\S+|有限会社\S+|\S+会社|\S+ストア|\S+ショップ)", text)
    if vendor_match:
        result["description"] = vendor_match.group(1)
    else:
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        result["description"] = first_line[:40]

    return result


DB_FILE = Path("expenses.db")


def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            description TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def load_expenses_from_db():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, date, category, amount, currency, payment_method, description FROM expenses ORDER BY id"
    )
    rows = []
    for row in cursor.fetchall():
        rows.append(
            TravelExpense(
                id=row[0],
                date=row[1],
                category=row[2],
                amount=row[3],
                currency=row[4],
                payment_method=row[5],
                description=row[6] or "",
            )
        )
    conn.close()
    return rows


def save_expense_to_db(expense: TravelExpense):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (date, category, amount, currency, payment_method, description) VALUES (?, ?, ?, ?, ?, ?)",
        (expense.date, expense.category, expense.amount, expense.currency, expense.payment_method, expense.description),
    )
    expense.id = cursor.lastrowid
    conn.commit()
    conn.close()


def delete_expense_from_db(expense_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def clear_expenses_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM expenses")
    conn.commit()
    conn.close()


def init_session():
    init_db()
    if "expenses" not in st.session_state:
        st.session_state.expenses = load_expenses_from_db()
    if "last_scan" not in st.session_state:
        st.session_state.last_scan = {}
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0
    if "delete_pending" not in st.session_state:
        st.session_state.delete_pending = None
    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None
    if "edit_data" not in st.session_state:
        st.session_state.edit_data = {}


def add_expense(date: str, category: str, amount: str, currency: str, payment_method: str, description: str):
    try:
        amount_value = float(amount)
    except ValueError:
        st.warning("請輸入正確的金額，例如 1200 或 1200.50")
        return

    expense = TravelExpense(
        id=None,
        date=date,
        category=category,
        amount=amount_value,
        currency=currency,
        payment_method=payment_method,
        description=description,
    )
    save_expense_to_db(expense)
    st.session_state.expenses.append(expense)
    st.session_state.last_scan = {}  # 清空掃描結果
    st.session_state.form_key += 1  # 變更表單 key，強制重置表單
    st.success("已新增支出")
    st.session_state.expenses.append(expense)
    st.success("已新增支出")


def download_csv() -> BytesIO:
    output = BytesIO()
    lines = ["日期,類別,金額,幣別,付款方式,備註\n"]
    for expense in st.session_state.expenses:
        row = expense.to_row()
        lines.append(",".join(f'"{item}"' for item in row) + "\n")
    output.write("".join(lines).encode("utf-8-sig"))
    output.seek(0)
    return output


def update_expense_in_db(expense: TravelExpense):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET date=?, category=?, amount=?, currency=?, payment_method=?, description=? WHERE id=?",
        (expense.date, expense.category, expense.amount, expense.currency, expense.payment_method, expense.description, expense.id),
    )
    conn.commit()
    conn.close()


def build_summary() -> str:
    totals = {}
    for expense in st.session_state.expenses:
        totals.setdefault(expense.currency, 0.0)
        totals[expense.currency] += expense.amount
    lines = [f"總筆數：{len(st.session_state.expenses)}"]
    for currency, total in totals.items():
        lines.append(f"總計 ({currency})：{total:.2f}")
    return "\n".join(lines)


def main():
    st.set_page_config(page_title="旅遊快速記帳", page_icon="📱", layout="centered")
    init_session()

    st.title("📱 旅遊快速記帳（行動網頁版）")
    st.write("在手機瀏覽器上使用的快速記帳工具，支援上傳日本發票照片並自動辨識。")

    with st.expander("📥 快速使用說明", expanded=False):
        st.markdown(
            "1. 點選「掃描發票」上傳收據照片；\n"
            "2. 檢查辨識結果後按「新增發票支出」；\n"
            "3. 或直接使用下方表單快速記帳；\n"
            "4. 可下載 CSV，或將頁面加入手機書籤。"
        )

    with st.form(f"expense_form_{st.session_state.form_key}"):
        st.subheader("快速記帳表單")
        date_input = st.date_input("日期", value=datetime.date.today())
        category_input = st.selectbox("類別", ["交通", "住宿", "餐飲", "門票", "購物", "其他"], index=0)
        amount_input = st.text_input("金額", value=st.session_state.last_scan.get("amount", ""))
        currency_input = st.selectbox("幣別", ["JPY", "TWD", "USD", "EUR"], index=0)
        payment_method_input = st.selectbox("付款方式", ["現金", "信用卡"], index=0)
        description_input = st.text_input("備註", value=st.session_state.last_scan.get("description", ""))

        submitted = st.form_submit_button("新增支出")
        if submitted:
            add_expense(date_input.isoformat(), category_input, amount_input, currency_input, payment_method_input, description_input)
            st.rerun()

    st.markdown("---")
    st.subheader("發票掃描（日本發票）")
    st.write("上傳發票照片後，系統會自動辨識日期與金額。手機可直接拍照上傳。")
    uploaded_file = st.file_uploader("掃描發票照片", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption="發票預覽", use_column_width=True)
        except Exception:
            st.error("無法讀取圖片，請使用清晰的照片再試一次。")
            uploaded_file = None

        if uploaded_file:
            if not OCR_AVAILABLE:
                st.warning("OCR 尚未安裝，請先安裝 pytesseract 並確認 Tesseract 可執行。")
                st.code("pip install pytesseract")
                st.info("Tesseract 可從 https://github.com/tesseract-ocr/tesseract 下載並安裝。")
            else:
                try:
                    raw_text = pytesseract.image_to_string(image, lang="jpn+eng")
                    st.text_area("辨識文字", raw_text, height=200)
                    parsed = parse_invoice_text(raw_text)
                    st.session_state.last_scan = parsed
                    st.markdown("#### 建議填入結果")
                    st.write(f"- 日期：{parsed['date']}")
                    st.write(f"- 金額：{parsed['amount']}")
                    st.write(f"- 幣別：{parsed['currency']}")
                    st.write(f"- 備註：{parsed['description']}")
                    if st.button("新增發票支出"):
                        if not parsed["amount"]:
                            st.warning("未偵測到金額，請手動輸入。")
                        else:
                            expense = TravelExpense(
                                id=None,
                                date=parsed["date"] or date_input.isoformat(),
                                category="其他",
                                amount=float(parsed["amount"].replace(",", "")),
                                currency=parsed["currency"],
                                payment_method="現金",
                                description=parsed["description"],
                            )
                            save_expense_to_db(expense)
                            st.session_state.expenses.append(expense)
                            st.session_state.last_scan = {}
                            st.success("已將發票資料加入記帳列表。")
                            st.rerun()
                except Exception as exc:
                    st.error(f"OCR 解析失敗：{exc}")

    st.markdown("---")
    st.subheader("記帳列表")
    if st.session_state.expenses:
        # 檢查是否有待刪除的項目
        if st.session_state.delete_pending is not None:
            expense_id_to_delete = st.session_state.delete_pending
            st.session_state.delete_pending = None
            delete_expense_from_db(expense_id_to_delete)
            st.session_state.expenses = [e for e in st.session_state.expenses if e.id != expense_id_to_delete]
            st.rerun()
        
        # 按日期分組
        from itertools import groupby
        sorted_expenses = sorted(st.session_state.expenses, key=lambda x: x.date, reverse=True)
        grouped_expenses = [(date, list(group)) for date, group in groupby(sorted_expenses, key=lambda x: x.date)]
        
        # 顯示按日期分組的項目
        for date, expenses_on_date in grouped_expenses:
            with st.expander(f"📅 {date} ({len(expenses_on_date)} 筆)", expanded=False):
                for idx, expense in enumerate(expenses_on_date):
                    col_cat, col_amt, col_edt, col_del = st.columns([2, 1.2, 0.6, 0.6])
                    
                    with col_cat:
                        st.markdown(f"**{expense.category}** {expense.description[:12]}")
                    
                    with col_amt:
                        st.text(f"{int(expense.amount)} {expense.currency}")
                    
                    with col_edt:
                        if st.button("✏️ 編", key=f"edit_{idx}_{expense.id}"):
                            st.session_state.editing_id = expense.id
                            st.session_state.edit_data = {
                                "date": expense.date,
                                "category": expense.category,
                                "amount": str(int(expense.amount)),
                                "currency": expense.currency,
                                "payment_method": expense.payment_method,
                                "description": expense.description,
                            }
                            st.rerun()
                    
                    with col_del:
                        if st.button("🗑️ 刪", key=f"delete_{idx}_{expense.id}"):
                            st.session_state.delete_pending = expense.id
                            st.rerun()
        
        st.divider()
        if st.button("清空所有記帳"):
            clear_expenses_db()
            st.session_state.expenses.clear()
            st.session_state.form_key += 1
            st.rerun()
        
        # 編輯表單
        if st.session_state.editing_id is not None:
            st.divider()
            st.subheader("編輯支出")
            
            expense_to_edit = next((e for e in st.session_state.expenses if e.id == st.session_state.editing_id), None)
            if expense_to_edit:
                with st.form(f"edit_form_{st.session_state.editing_id}"):
                    edit_date = st.date_input("日期", value=datetime.datetime.strptime(st.session_state.edit_data["date"], "%Y-%m-%d").date())
                    edit_category = st.selectbox("類別", ["交通", "住宿", "餐飲", "門票", "購物", "其他"], index=["交通", "住宿", "餐飲", "門票", "購物", "其他"].index(st.session_state.edit_data["category"]))
                    edit_amount = st.text_input("金額", value=st.session_state.edit_data["amount"])
                    edit_currency = st.selectbox("幣別", ["JPY", "TWD", "USD", "EUR"], index=["JPY", "TWD", "USD", "EUR"].index(st.session_state.edit_data["currency"]))
                    edit_payment = st.selectbox("付款方式", ["現金", "信用卡"], index=["現金", "信用卡"].index(st.session_state.edit_data["payment_method"]))
                    edit_description = st.text_input("備註", value=st.session_state.edit_data["description"])
                    
                    col_save, col_cancel = st.columns([1, 1])
                    with col_save:
                        if st.form_submit_button("✅ 保存"):
                            try:
                                amount_value = float(edit_amount)
                                updated_expense = TravelExpense(
                                    id=expense_to_edit.id,
                                    date=edit_date.isoformat(),
                                    category=edit_category,
                                    amount=amount_value,
                                    currency=edit_currency,
                                    payment_method=edit_payment,
                                    description=edit_description,
                                )
                                update_expense_in_db(updated_expense)
                                
                                for i, e in enumerate(st.session_state.expenses):
                                    if e.id == st.session_state.editing_id:
                                        st.session_state.expenses[i] = updated_expense
                                        break
                                
                                st.session_state.editing_id = None
                                st.session_state.edit_data = {}
                                st.success("已保存")
                                st.rerun()
                            except ValueError:
                                st.error("金額格式錯誤")
                    
                    with col_cancel:
                        if st.form_submit_button("❌ 取消"):
                            st.session_state.editing_id = None
                            st.session_state.edit_data = {}
                            st.rerun()
    else:
        st.info("目前尚無支出資料，請先新增或掃描發票。")

    st.markdown("---")
    st.subheader("資料匯出")
    if st.session_state.expenses:
        st.download_button(
            label="下載 CSV",
            data=download_csv(),
            file_name="travel_expenses.csv",
            mime="text/csv",
        )
        st.text_area("摘要", build_summary(), height=140)

    st.markdown("---")
    if not OCR_AVAILABLE:
        st.warning("若要使用發票掃描，請安裝 pytesseract，並確認已安裝 Tesseract OCR 可執行檔。")


if __name__ == "__main__":
    main()
