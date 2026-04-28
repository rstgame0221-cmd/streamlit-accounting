import csv
import datetime
import re
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
    date: str
    category: str
    amount: float
    currency: str
    description: str

    def to_row(self):
        return [self.date, self.category, f"{self.amount:.2f}", self.currency, self.description]


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


def init_session():
    if "expenses" not in st.session_state:
        st.session_state.expenses = []
    if "last_scan" not in st.session_state:
        st.session_state.last_scan = {}


def add_expense(date: str, category: str, amount: str, currency: str, description: str):
    try:
        amount_value = float(amount)
    except ValueError:
        st.warning("請輸入正確的金額，例如 1200 或 1200.50")
        return

    expense = TravelExpense(
        date=date,
        category=category,
        amount=amount_value,
        currency=currency,
        description=description,
    )
    st.session_state.expenses.append(expense)
    st.success("已新增支出")


def download_csv() -> BytesIO:
    output = BytesIO()
    lines = ["日期,類別,金額,幣別,備註\n"]
    for expense in st.session_state.expenses:
        row = expense.to_row()
        lines.append(",".join(f'"{item}"' for item in row) + "\n")
    output.write("".join(lines).encode("utf-8-sig"))
    output.seek(0)
    return output


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

    with st.expander("📥 快速使用說明", expanded=True):
        st.markdown(
            "1. 點選「掃描發票」上傳收據照片；\n"
            "2. 檢查辨識結果後按「新增發票支出」；\n"
            "3. 或直接使用下方表單快速記帳；\n"
            "4. 可下載 CSV，或將頁面加入手機書籤。"
        )

    with st.form("expense_form"):
        st.subheader("快速記帳表單")
        date_input = st.date_input("日期", value=datetime.date.today())
        category_input = st.selectbox("類別", ["交通", "住宿", "餐飲", "門票", "購物", "其他"], index=0)
        amount_input = st.text_input("金額", value=st.session_state.last_scan.get("amount", ""))
        currency_input = st.selectbox("幣別", ["JPY", "TWD", "USD", "EUR"], index=0)
        description_input = st.text_input("備註", value=st.session_state.last_scan.get("description", ""))

        submitted = st.form_submit_button("新增支出")
        if submitted:
            add_expense(date_input.isoformat(), category_input, amount_input, currency_input, description_input)

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
                            st.session_state.expenses.append(
                                TravelExpense(
                                    date=parsed["date"] or date_input.isoformat(),
                                    category="其他",
                                    amount=float(parsed["amount"].replace(",", "")),
                                    currency=parsed["currency"],
                                    description=parsed["description"],
                                )
                            )
                            st.success("已將發票資料加入記帳列表。")
                except Exception as exc:
                    st.error(f"OCR 解析失敗：{exc}")

    st.markdown("---")
    st.subheader("記帳列表")
    if st.session_state.expenses:
        rows = [expense.to_row() for expense in st.session_state.expenses]
        st.table(rows)
        if st.button("清空所有記帳"):
            st.session_state.expenses.clear()
            st.success("已清空所有資料")
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
