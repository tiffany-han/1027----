# 島嶼市集 IsleMart 電商資料集（課程模擬資料）

> **這是模擬資料，不是真實交易。** 「島嶼市集 IsleMart」是虛構的台灣綜合電商，所有訂單、顧客、賣家與評論都由程式隨機產生，不涉及任何真實個人或企業。
> 資料表結構參照 Kaggle 上的 Olist 巴西電商公開資料集設計，但**未使用 Olist 的任何資料**。

本資料集供「改變未來知識工作的ChatGPT」課程實作使用。

## 概況

| 項目 | 數值 |
| --- | --- |
| 期間 | 2024-01-01 至 2025-12-31 |
| 訂單 | 60,000 筆 |
| 訂單明細 | 約 75,600 列 |
| 顧客（不重複） | 48,000 人 |
| 賣家 | 300 家 |
| 商品 | 10,000 項，14 個類別 |
| 幣別 | 新台幣（TWD） |
| 編碼 | UTF-8（含 BOM，可直接用 Excel 開啟） |

## 檔案

| 檔名 | 內容 | 主鍵 |
| --- | --- | --- |
| islemart_orders_dataset.csv | 訂單主檔與各階段時間戳記 | order_id |
| islemart_order_items_dataset.csv | 訂單明細（一筆訂單可有多列） | order_id + order_item_id |
| islemart_order_payments_dataset.csv | 付款紀錄（一筆訂單可有多列） | order_id + payment_sequential |
| islemart_order_reviews_dataset.csv | 顧客評論與評分 | review_id |
| islemart_customers_dataset.csv | 顧客與收件地區 | customer_id |
| islemart_sellers_dataset.csv | 賣家與所在地區 | seller_id |
| islemart_products_dataset.csv | 商品屬性 | product_id |
| islemart_geolocation_dataset.csv | 郵遞區號對應的約略座標 | （無唯一鍵） |
| product_category_name_translation.csv | 類別中英對照 | product_category_name |

欄位說明請看 `data_dictionary.md`。

## 表之間的關係

```
customers ──< orders >── order_items >── products
                │              └──────── sellers
                ├──< order_payments
                └──< order_reviews
customers / sellers 的 zip_code_prefix ── geolocation
products.product_category_name ── category_translation
```

## 使用提醒

真實世界的資料不會乾乾淨淨，這份也是。動手分析之前，先花時間了解每張表的粒度（一列代表什麼），以及表跟表之間是一對一還是一對多。
