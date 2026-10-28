# 傳統 Python 實作範例｜改變未來知識工作的 ChatGPT

這個資料夾用**不靠 AI 的傳統 Python**（pandas、matplotlib、scipy、SQLite）重做課程的每一個實作單元。
每本 Notebook 都有逐步說明與可執行的程式碼，最後附上「AI 做法 vs 傳統做法」對照。

## 內容

| Notebook | 對應單元 | 學到什麼 |
| --- | --- | --- |
| `01_資料理解_M3.ipynb` | M3 理解陌生資料 | 資料概況、粒度與主鍵、表關聯、資料品質六面向、陷阱紀錄表 |
| `02_清理EDA與對帳_M4.ipynb` | M4 清理、EDA、對帳 | JOIN 膨脹、彙總後合併、營收定義、EDA 圖表、三種方法對帳 |
| `03_商業洞察_M5.ipynb` | M5 商業洞察 | RFM 分群、t 檢定與效果大小、「慢 vs 延遲」、分層比較與迴歸、賣家試算、評論分類 |
| `04_SQL與資料倉儲_M7.ipynb` | M7 SQL | SQLite 本機資料庫、先彙總再合併的 SQL、指標定義寫成 SQL、SQL 與 pandas 對帳、BigQuery 上傳檔 |
| `05_儀表板與報告_M8_M9.ipynb` | M8 儀表板、M9 報告 | 完整月份判斷、KPI、matplotlib 儀表板、自動產生 HTML 報告與 PPTX |
| `06_自動化與排程_M10.ipynb` | M10 自動化 | 清理腳本、自動化測試、週報腳本、cron／工作排程器、人工核准關卡 |

其他檔案：

| 檔案 | 用途 |
| --- | --- |
| `islemart_lib.py` | 共用函式：讀資料、中文字型、清理管線、指標定義 |
| `scripts/clean.py` | 可重跑的清理腳本（含內建檢查） |
| `scripts/weekly_report.py` | 每週一的週報草稿（只存草稿，不寄出） |
| `tests/test_pipeline.py` | 清理管線的自動化測試 |
| `講師版_含執行結果/` | 已執行過、含所有輸出的 Notebook，供講師備課與對答案（**內含答案，請勿發給學員**） |

## 開始之前

1. 安裝 Python 3.10 以上，再安裝套件：

   ```bash
   pip install -r requirements.txt
   ```

2. 資料位置：Notebook 會自動尋找 `../模擬資料_IsleMart/學員版/islemart_data`。
   如果資料放在別處，把 `islemart_data` 資料夾複製到本資料夾裡，或設定環境變數：

   ```bash
   export ISLEMART_DATA=/你的路徑/islemart_data        # macOS／Linux
   set ISLEMART_DATA=C:\你的路徑\islemart_data          # Windows
   ```

3. 啟動 Jupyter，依序打開 01 到 06：

   ```bash
   jupyter lab
   ```

   **請在本資料夾直接打開 Notebook 執行**（不要在 `講師版_含執行結果/` 裡執行，那裡找不到共用函式庫）。

## 中文字型

圖表會自動使用系統裡的繁體中文字型（Windows 微軟正黑體、macOS 蘋方、Linux Noto Sans CJK TC）。
如果圖上的中文變成方塊，請安裝 [Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC) 後重新啟動 Jupyter。

## 指標定義（全部 Notebook 共用）

| 指標 | 定義 |
| --- | --- |
| 營收 | 已送達訂單的商品售價加總；不含運費、不扣折價券、排除價格異常（單價 ≥ 同類別中位數 20 倍） |
| 延遲率 | 有效送達訂單中，送達日晚於預計到貨日的比例 |
| 平均評分 | 每筆訂單一則評論（刪除完全重複的列；同一訂單多則時取最後回覆的一則） |
| 回購率 | 以 `customer_unique_id` 計，期間內下單 2 次以上的人數占比 |

定義寫在 `islemart_lib.py`，改一處，所有 Notebook 與腳本一起更新。
