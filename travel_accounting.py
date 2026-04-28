import csv
import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


@dataclass
class TravelExpense:
    date: str
    category: str
    amount: float
    currency: str
    description: str
    payer: str

    def to_row(self):
        return [self.date, self.category, f"{self.amount:.2f}", self.currency, self.payer, self.description]

    @staticmethod
    def from_row(row):
        try:
            return TravelExpense(
                date=row[0],
                category=row[1],
                amount=float(row[2]),
                currency=row[3],
                payer=row[4],
                description=row[5],
            )
        except Exception:
            return None


class TravelExpenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("旅遊計帳程式")
        self.root.geometry("920x600")
        self.expenses = []
        self.current_file = None

        self.date_var = tk.StringVar(value=datetime.date.today().isoformat())
        self.category_var = tk.StringVar(value="交通")
        self.amount_var = tk.StringVar()
        self.currency_var = tk.StringVar(value="TWD")
        self.payer_var = tk.StringVar(value="本人")
        self.description_var = tk.StringVar()
        self.status_var = tk.StringVar(value="請輸入旅遊支出後按「新增」")

        self.build_ui()

    def build_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        form_labels = ["日期", "類別", "金額", "幣別", "付款人", "備註"]
        for idx, label in enumerate(form_labels):
            ttk.Label(top_frame, text=label).grid(row=0, column=idx, sticky="w", padx=4)

        ttk.Entry(top_frame, textvariable=self.date_var, width=12).grid(row=1, column=0, padx=4)
        categories = ["交通", "住宿", "餐飲", "門票", "購物", "其他"]
        ttk.Combobox(top_frame, textvariable=self.category_var, values=categories, width=12, state="readonly").grid(row=1, column=1, padx=4)
        ttk.Entry(top_frame, textvariable=self.amount_var, width=12).grid(row=1, column=2, padx=4)
        ttk.Combobox(top_frame, textvariable=self.currency_var, values=["TWD", "USD", "JPY", "EUR", "CNY"], width=12, state="readonly").grid(row=1, column=3, padx=4)
        ttk.Entry(top_frame, textvariable=self.payer_var, width=12).grid(row=1, column=4, padx=4)
        ttk.Entry(top_frame, textvariable=self.description_var, width=30).grid(row=1, column=5, padx=4)

        button_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="新增", command=self.add_expense, width=10).pack(side="left", padx=3)
        ttk.Button(button_frame, text="刪除選取", command=self.delete_selected, width=10).pack(side="left", padx=3)
        ttk.Button(button_frame, text="清空資料", command=self.clear_expenses, width=10).pack(side="left", padx=3)
        ttk.Button(button_frame, text="載入 CSV", command=self.load_csv, width=10).pack(side="left", padx=3)
        ttk.Button(button_frame, text="儲存 CSV", command=self.save_csv, width=10).pack(side="left", padx=3)
        ttk.Button(button_frame, text="匯出摘要", command=self.export_summary, width=10).pack(side="left", padx=3)

        self.tree = ttk.Treeview(self.root, columns=("date", "category", "amount", "currency", "payer", "description"), show="headings", selectmode="extended")
        headings = ["日期", "類別", "金額", "幣別", "付款人", "備註"]
        widths = [90, 100, 90, 70, 100, 320]
        for col, heading, width in zip(self.tree["columns"], headings, widths):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        summary_frame = ttk.Frame(self.root, padding=10)
        summary_frame.pack(fill="x")
        self.summary_label = ttk.Label(summary_frame, text="目前合計：0 筆，總金額 TWD 0.00", foreground="blue")
        self.summary_label.pack(anchor="w")
        ttk.Label(summary_frame, textvariable=self.status_var, foreground="darkgreen").pack(anchor="w", pady=(4, 0))

    def add_expense(self):
        date_value = self.date_var.get().strip()
        category = self.category_var.get().strip()
        amount_text = self.amount_var.get().strip()
        currency = self.currency_var.get().strip()
        payer = self.payer_var.get().strip()
        description = self.description_var.get().strip()

        if not date_value:
            messagebox.showwarning("欄位不足", "請輸入日期。格式：YYYY-MM-DD")
            return
        try:
            datetime.date.fromisoformat(date_value)
        except ValueError:
            messagebox.showwarning("格式錯誤", "日期格式必須為 YYYY-MM-DD")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("格式錯誤", "金額必須為正數")
            return

        expense = TravelExpense(date=date_value, category=category, amount=amount, currency=currency, payer=payer, description=description)
        self.expenses.append(expense)
        self.tree.insert("", "end", values=expense.to_row())
        self.amount_var.set("")
        self.description_var.set("")
        self.status_var.set("已新增一筆支出。")
        self.update_summary()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("刪除", "請先選取要刪除的支出項目。")
            return
        for item in selected:
            index = self.tree.index(item)
            self.tree.delete(item)
            if 0 <= index < len(self.expenses):
                self.expenses.pop(index)
        self.status_var.set(f"已刪除 {len(selected)} 筆支出。")
        self.update_summary()

    def clear_expenses(self):
        if not self.expenses:
            return
        if not messagebox.askyesno("清空確認", "確認要清空所有旅遊支出嗎？"):
            return
        self.expenses.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.current_file = None
        self.status_var.set("已清空所有支出資料。")
        self.update_summary()

    def load_csv(self):
        path = filedialog.askopenfilename(title="載入旅遊支出 CSV", filetypes=[("CSV 檔案", "*.csv")])
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)

            if not rows:
                messagebox.showwarning("載入失敗", "CSV 檔案為空。")
                return

            self.expenses.clear()
            for item in self.tree.get_children():
                self.tree.delete(item)

            for idx, row in enumerate(rows):
                if idx == 0 and row[:6] == ["日期", "類別", "金額", "幣別", "付款人", "備註"]:
                    continue
                expense = TravelExpense.from_row(row)
                if expense is None:
                    continue
                self.expenses.append(expense)
                self.tree.insert("", "end", values=expense.to_row())

            self.current_file = path
            self.status_var.set(f"已從 {Path(path).name} 載入 {len(self.expenses)} 筆資料。")
            self.update_summary()
        except Exception as exc:
            messagebox.showerror("載入錯誤", f"讀取 CSV 時發生錯誤：{exc}")

    def save_csv(self):
        if not self.expenses:
            messagebox.showinfo("儲存", "目前沒有支出資料可儲存。")
            return
        path = filedialog.asksaveasfilename(title="儲存旅遊支出 CSV", defaultextension=".csv", filetypes=[("CSV 檔案", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["日期", "類別", "金額", "幣別", "付款人", "備註"])
                for expense in self.expenses:
                    writer.writerow(expense.to_row())
            self.current_file = path
            self.status_var.set(f"已儲存至 {Path(path).name}。")
        except Exception as exc:
            messagebox.showerror("儲存錯誤", f"儲存 CSV 時發生錯誤：{exc}")

    def export_summary(self):
        if not self.expenses:
            messagebox.showinfo("匯出摘要", "目前沒有資料可匯出摘要。")
            return
        totals = self.calculate_totals()
        summary_lines = ["旅遊支出摘要", "====================", f"總筆數：{len(self.expenses)}"]
        for currency, total in totals.items():
            summary_lines.append(f"總計 ({currency})：{total:.2f}")
        summary_lines.append("")
        summary_lines.append("按類別統計：")
        category_summary = self.category_summary()
        for category, amount_map in category_summary.items():
            for currency, amount in amount_map.items():
                summary_lines.append(f"  {category} ({currency})：{amount:.2f}")

        summary_text = "\n".join(summary_lines)
        summary_file = filedialog.asksaveasfilename(title="匯出摘要 TXT", defaultextension=".txt", filetypes=[("文字檔", "*.txt")])
        if summary_file:
            try:
                with open(summary_file, "w", encoding="utf-8") as txtfile:
                    txtfile.write(summary_text)
                self.status_var.set(f"已匯出摘要至 {Path(summary_file).name}。")
                messagebox.showinfo("匯出完成", "已成功匯出旅遊摘要。")
            except Exception as exc:
                messagebox.showerror("匯出錯誤", f"匯出摘要時發生錯誤：{exc}")
        else:
            self.status_var.set("已取消匯出摘要。")

    def calculate_totals(self):
        totals = {}
        for expense in self.expenses:
            totals.setdefault(expense.currency, 0.0)
            totals[expense.currency] += expense.amount
        return totals

    def category_summary(self):
        summary = {}
        for expense in self.expenses:
            summary.setdefault(expense.category, {})
            summary[expense.category].setdefault(expense.currency, 0.0)
            summary[expense.category][expense.currency] += expense.amount
        return summary

    def update_summary(self):
        totals = self.calculate_totals()
        total_texts = [f"{currency} {amount:.2f}" for currency, amount in totals.items()]
        text = f"目前合計：{len(self.expenses)} 筆，總金額 {' / '.join(total_texts) if total_texts else '0.00'}"
        self.summary_label.config(text=text)


def main():
    root = tk.Tk()
    TravelExpenseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
