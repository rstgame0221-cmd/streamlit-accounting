import os
import csv
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from pypdf import PdfReader

MAX_FILE_SIZE_MB = 50
MAX_PAGES_PER_PDF = 30


class PDFSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 搜尋工具")
        self.root.geometry("980x700")

        self.folder_var = tk.StringVar()
        self.keyword_var = tk.StringVar()
        self.status_var = tk.StringVar(value="請選擇資料夾並輸入關鍵字")

        self.filename_matches = []
        self.content_matches = []
        self.skipped_files = []
        self.failed_files = []

        self.build_ui()

    def build_ui(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_top, text="資料夾：").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_top, textvariable=self.folder_var, width=80).grid(row=0, column=1, padx=5)
        tk.Button(frame_top, text="選擇資料夾", command=self.choose_folder, width=12).grid(row=0, column=2)

        tk.Label(frame_top, text="關鍵字：").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Entry(frame_top, textvariable=self.keyword_var, width=30).grid(row=1, column=1, sticky="w", padx=5, pady=(8, 0))

        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(frame_buttons, text="開始搜尋", command=self.start_search, width=12).pack(side="left")
        tk.Button(frame_buttons, text="清空結果", command=self.clear_results, width=12).pack(side="left", padx=5)
        tk.Button(frame_buttons, text="匯出 TXT", command=self.export_txt, width=12).pack(side="left")
        tk.Button(frame_buttons, text="匯出 CSV", command=self.export_csv, width=12).pack(side="left", padx=5)

        tk.Label(self.root, textvariable=self.status_var, anchor="w", fg="blue").pack(fill="x", padx=10)

        self.result_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Consolas", 10))
        self.result_box.pack(fill="both", expand=True, padx=10, pady=10)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def clear_results(self):
        self.filename_matches = []
        self.content_matches = []
        self.skipped_files = []
        self.failed_files = []
        self.result_box.delete("1.0", tk.END)
        self.status_var.set("結果已清空")

    def start_search(self):
        folder = self.folder_var.get().strip()
        keyword = self.keyword_var.get().strip()

        if not folder:
            messagebox.showwarning("提醒", "請先選擇資料夾")
            return

        if not keyword:
            messagebox.showwarning("提醒", "請先輸入關鍵字")
            return

        if not Path(folder).exists():
            messagebox.showerror("錯誤", "資料夾不存在")
            return

        self.filename_matches = []
        self.content_matches = []
        self.skipped_files = []
        self.failed_files = []
        self.result_box.delete("1.0", tk.END)
        self.status_var.set("搜尋中，請稍候...")

        thread = threading.Thread(target=self.search_pdf_files, args=(folder, keyword), daemon=True)
        thread.start()

    def search_pdf_files(self, folder_path: str, keyword: str):
        folder = Path(folder_path)
        keyword_lower = keyword.lower()
        scanned_files = 0

        for root_dir, dirs, files in os.walk(folder):
            for file_name in files:
                file_path = Path(root_dir) / file_name

                if file_path.suffix.lower() != ".pdf":
                    continue

                scanned_files += 1

                if keyword_lower in file_name.lower():
                    self.filename_matches.append(str(file_path))

                try:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    if file_size_mb > MAX_FILE_SIZE_MB:
                        self.skipped_files.append((str(file_path), f"檔案過大：{file_size_mb:.1f} MB"))
                        continue
                except Exception as e:
                    self.failed_files.append((str(file_path), f"無法讀取檔案大小：{e}"))
                    continue

                try:
                    reader = PdfReader(str(file_path))

                    if reader.is_encrypted:
                        try:
                            result = reader.decrypt("")
                            if result == 0:
                                self.failed_files.append((str(file_path), "PDF 已加密，且無法用空密碼解密"))
                            continue
                        except Exception as e:
                            self.failed_files.append((str(file_path), f"PDF 加密，無法解密：{e}"))
                            continue

                except Exception as e:
                    self.failed_files.append((str(file_path), f"無法開啟 PDF：{e}"))
                    continue

                pages_to_scan = min(len(reader.pages), MAX_PAGES_PER_PDF)

                for page_index in range(pages_to_scan):
                    page_no = page_index + 1

                    try:
                        page = reader.pages[page_index]
                        text = page.extract_text()
                    except Exception as e:
                        self.failed_files.append((str(file_path), f"第 {page_no} 頁讀取失敗：{e}"))
                        continue

                    if not text:
                        continue

                    for line_no, line in enumerate(text.splitlines(), start=1):
                        if keyword_lower in line.lower():
                            self.content_matches.append({
                                "file": str(file_path),
                                "page": page_no,
                                "line": line_no,
                                "text": line.strip()
                            })

        self.root.after(0, lambda: self.show_results(scanned_files))

    def show_results(self, scanned_files: int):
        self.result_box.delete("1.0", tk.END)

        self.append_text("=" * 90 + "\n")
        self.append_text("搜尋完成\n")
        self.append_text("=" * 90 + "\n")
        self.append_text(f"共掃描 PDF：{scanned_files} 個\n")
        self.append_text(f"檔名命中：{len(self.filename_matches)} 個\n")
        self.append_text(f"內文命中：{len(self.content_matches)} 筆\n")
        self.append_text(f"略過：{len(self.skipped_files)} 個\n")
        self.append_text(f"失敗：{len(self.failed_files)} 筆\n\n")

        self.append_text("=" * 90 + "\n")
        self.append_text("一、檔名符合的 PDF\n")
        self.append_text("=" * 90 + "\n")
        if self.filename_matches:
            for path in self.filename_matches:
                self.append_text(path + "\n")
        else:
            self.append_text("沒有找到\n")

        self.append_text("\n" + "=" * 90 + "\n")
        self.append_text("二、內文符合的 PDF\n")
        self.append_text("=" * 90 + "\n")
        if self.content_matches:
            for item in self.content_matches:
                self.append_text(f"檔案：{item['file']}\n")
                self.append_text(f"頁碼：第 {item['page']} 頁，第 {item['line']} 行\n")
                self.append_text(f"內容：{item['text']}\n")
                self.append_text("-" * 90 + "\n")
        else:
            self.append_text("沒有找到\n")

        self.append_text("\n" + "=" * 90 + "\n")
        self.append_text("三、略過的檔案\n")
        self.append_text("=" * 90 + "\n")
        if self.skipped_files:
            for file_path, reason in self.skipped_files:
                self.append_text(f"{file_path}\n")
                self.append_text(f"原因：{reason}\n")
                self.append_text("-" * 90 + "\n")
        else:
            self.append_text("沒有\n")

        self.append_text("\n" + "=" * 90 + "\n")
        self.append_text("四、讀取失敗的檔案或頁面\n")
        self.append_text("=" * 90 + "\n")
        if self.failed_files:
            for file_path, reason in self.failed_files:
                self.append_text(f"{file_path}\n")
                self.append_text(f"原因：{reason}\n")
                self.append_text("-" * 90 + "\n")
        else:
            self.append_text("沒有\n")

        self.status_var.set(
            f"搜尋完成：檔名 {len(self.filename_matches)} 個，內文 {len(self.content_matches)} 筆"
        )

    def append_text(self, text: str):
        self.result_box.insert(tk.END, text)
        self.result_box.see(tk.END)

    def export_txt(self):
        content = self.result_box.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("提醒", "目前沒有可匯出的結果")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            title="儲存 TXT"
        )
        if not save_path:
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("完成", f"已匯出 TXT：\n{save_path}")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗：\n{e}")

    def export_csv(self):
        if not self.content_matches and not self.filename_matches:
            messagebox.showwarning("提醒", "目前沒有可匯出的結果")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="儲存 CSV"
        )
        if not save_path:
            return

        try:
            with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["類型", "檔案路徑", "頁碼", "行號", "內容"])

                for path in self.filename_matches:
                    writer.writerow(["檔名命中", path, "", "", ""])

                for item in self.content_matches:
                    writer.writerow([
                        "內文命中",
                        item["file"],
                        item["page"],
                        item["line"],
                        item["text"]
                    ])

                for file_path, reason in self.skipped_files:
                    writer.writerow(["略過", file_path, "", "", reason])

                for file_path, reason in self.failed_files:
                    writer.writerow(["失敗", file_path, "", "", reason])

            messagebox.showinfo("完成", f"已匯出 CSV：\n{save_path}")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗：\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSearchApp(root)
    root.mainloop()