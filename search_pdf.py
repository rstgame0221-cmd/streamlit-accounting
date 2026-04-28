import os
from pathlib import Path
from pypdf import PdfReader


def search_pdf_files(folder_path: str, keyword: str):
    folder = Path(folder_path)

    if not folder.exists():
        print(f"資料夾不存在：{folder}")
        return

    if not folder.is_dir():
        print(f"這不是資料夾：{folder}")
        return

    keyword_lower = keyword.lower()
    filename_matches = []
    content_matches = []

    for root, dirs, files in os.walk(folder):
        for file_name in files:
            file_path = Path(root) / file_name

            # 只處理 PDF
            if file_path.suffix.lower() != ".pdf":
                continue

            # 搜尋檔名
            if keyword_lower in file_name.lower():
                filename_matches.append(str(file_path))

            # 搜尋 PDF 內文
            try:
                reader = PdfReader(str(file_path))

                for page_no, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()

                    if not text:
                        continue

                    lines = text.splitlines()
                    for line_no, line in enumerate(lines, start=1):
                        if keyword_lower in line.lower():
                            content_matches.append({
                                "file": str(file_path),
                                "page": page_no,
                                "line": line_no,
                                "text": line.strip()
                            })

            except Exception as e:
                print(f"讀取 PDF 失敗：{file_path}")
                print(f"原因：{e}")

    print("\n=== 檔名包含關鍵字的 PDF ===")
    if filename_matches:
        for path in filename_matches:
            print(path)
    else:
        print("沒有找到")

    print("\n=== 內文包含關鍵字的 PDF ===")
    if content_matches:
        for item in content_matches:
            print(f"{item['file']} | 第 {item['page']} 頁 | 第 {item['line']} 行")
            print(f"  {item['text']}")
    else:
        print("沒有找到")


if __name__ == "__main__":
    folder_path = input("請輸入要搜尋的資料夾路徑：").strip()
    keyword = input("請輸入關鍵字：").strip()

    if not keyword:
        print("關鍵字不能為空")
    else:
        search_pdf_files(folder_path, keyword)