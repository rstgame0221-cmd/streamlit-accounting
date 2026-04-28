# 旅遊快速記帳程式

📱 一套專為旅遊設計的計帳工具，支援桌機版與手機網頁版。提供快速記帳、日本發票掃描辨識等功能。

## 功能特性

- ✅ **快速記帳** - 預設常用分類與金額
- 📸 **日本發票掃描** - 上傳照片自動辨識日期與金額
- 💱 **多幣別支援** - JPY、TWD、USD、EUR
- 📊 **資料統計** - 自動計算總金額與分類統計
- 📥 **CSV 匯出** - 輕鬆匯出至 Excel 或其他工具
- 📱 **手機友善** - 網頁版介面適配各種裝置

## 版本說明

### 桌機版
檔案：`travel_accounting.py`

```bash
python travel_accounting.py
```

完整功能的 Tkinter GUI 應用，適合在電腦上使用。

### 行動網頁版
檔案：`travel_accounting_mobile.py`

```bash
streamlit run travel_accounting_mobile.py
```

手機友善的 Streamlit 網頁應用，可在手機瀏覽器中使用。

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 發票掃描功能

如需使用日本發票掃描功能，需另外安裝 Tesseract OCR：

- **下載連結**：https://github.com/tesseract-ocr/tesseract
- **Windows**：下載並執行安裝程式
- **macOS**：`brew install tesseract`
- **Linux**：`sudo apt install tesseract-ocr`

安裝完成後，pytesseract 會自動偵測 Tesseract 位置。

## 手機使用

### 同一 Wi-Fi 網路

1. 在電腦啟動 Streamlit 版本
2. 記下終端機顯示的 **Network URL**，例如：`http://192.168.1.100:8501`
3. 手機瀏覽器打開此網址即可

### 外網使用（使用 ngrok）

1. 下載並安裝 ngrok
2. 啟動 Streamlit 版本
3. 另開終端執行：`ngrok http 8501`
4. 手機打開 ngrok 提供的公開網址

## 檔案結構

```
.
├── travel_accounting.py          # 桌機版 GUI
├── travel_accounting_mobile.py   # 行動網頁版
├── requirements.txt              # 依賴套件
└── README.md                     # 本檔案
```

## 使用說明

### 快速記帳

1. 選擇日期、類別、輸入金額
2. 點擊「新增支出」或使用預設快速按鈕
3. 支持多人付款人設定

### 掃描日本發票

1. 上傳發票或收據照片
2. 確認 OCR 辨識結果（日期、金額、備註）
3. 點擊「新增發票支出」自動加入記帳

### 資料匯出

- 下載 CSV 檔案供 Excel 使用
- 查看按幣別與分類的統計摘要

## 技術堆疊

- **桌機版**：Python 3.14 + Tkinter
- **行動版**：Python 3.14 + Streamlit
- **OCR**：Tesseract + pytesseract
- **資料處理**：CSV、Pandas

## 系統需求

- Python 3.10 或更新版本
- Windows / macOS / Linux

## 授權

MIT License

## 常見問題

### Q：手機連不到怎麼辦？
A：確保手機與電腦在同一 Wi-Fi，且防火牆未阻擋 8501 端口

### Q：OCR 辨識結果不準確？
A：請用清晰的直拍照片，避免角度歪斜或模糊

### Q：能否在外網使用？
A：可使用 ngrok 或部署到雲端平台（Streamlit Cloud / Render 等）

## 貢獻與問題回報

歡迎提交 Issue 與 Pull Request！

---

開發於 2026 年 4 月
