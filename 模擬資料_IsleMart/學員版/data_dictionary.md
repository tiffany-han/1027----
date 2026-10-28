# IsleMart 資料字典

所有時間欄位格式為 `YYYY-MM-DD HH:MM:SS`（台灣時間），空白代表沒有值。

## islemart_orders_dataset.csv（一列 = 一筆訂單）

| 欄位 | 說明 |
| --- | --- |
| order_id | 訂單編號 |
| customer_id | 這筆訂單的顧客編號（連到 customers） |
| order_status | 訂單狀態：delivered、shipped、canceled、processing、unavailable |
| order_purchase_timestamp | 下單時間 |
| order_approved_at | 付款核准時間 |
| order_delivered_carrier_date | 賣家交給物流的時間 |
| order_delivered_customer_date | 顧客收到貨的時間 |
| order_estimated_delivery_date | 下單時承諾的預計到貨日 |

## islemart_order_items_dataset.csv（一列 = 訂單中的一件商品）

| 欄位 | 說明 |
| --- | --- |
| order_id | 訂單編號 |
| order_item_id | 該訂單中的品項序號（1, 2, 3…） |
| product_id | 商品編號 |
| seller_id | 賣家編號 |
| shipping_limit_date | 賣家最晚出貨期限 |
| price | 品項售價（TWD） |
| freight_value | 運費（TWD） |

## islemart_order_payments_dataset.csv（一列 = 一次付款）

| 欄位 | 說明 |
| --- | --- |
| order_id | 訂單編號 |
| payment_sequential | 同一訂單的付款序號 |
| payment_type | credit_card、mobile_pay、cod_store_pickup（超商取貨付款）、atm_transfer、voucher（折價券） |
| payment_installments | 分期期數 |
| payment_value | 付款金額（TWD） |

## islemart_order_reviews_dataset.csv（一列 = 一則評論）

| 欄位 | 說明 |
| --- | --- |
| review_id | 評論編號 |
| order_id | 訂單編號 |
| review_score | 評分 1–5 |
| review_comment_title | 評論標題（可空白） |
| review_comment_message | 評論內容（可空白） |
| review_creation_date | 系統寄出評論邀請的時間 |
| review_answer_timestamp | 顧客填寫評論的時間 |

## islemart_customers_dataset.csv

| 欄位 | 說明 |
| --- | --- |
| customer_id | 顧客編號（每筆訂單一個） |
| customer_unique_id | 顧客的唯一識別碼（同一個人） |
| customer_zip_code_prefix | 郵遞區號前三碼 |
| customer_city | 鄉鎮市區 |
| customer_county | 縣市 |

## islemart_sellers_dataset.csv

| 欄位 | 說明 |
| --- | --- |
| seller_id | 賣家編號 |
| seller_zip_code_prefix | 郵遞區號前三碼 |
| seller_city | 鄉鎮市區 |
| seller_county | 縣市 |

## islemart_products_dataset.csv

| 欄位 | 說明 |
| --- | --- |
| product_id | 商品編號 |
| product_category_name | 類別（中文） |
| product_name_length | 商品名稱字數 |
| product_description_length | 商品描述字數 |
| product_photos_qty | 商品照片數 |
| product_weight_g | 重量（公克） |
| product_length_cm / product_height_cm / product_width_cm | 包裝尺寸（公分） |

## islemart_geolocation_dataset.csv

| 欄位 | 說明 |
| --- | --- |
| geolocation_zip_code_prefix | 郵遞區號前三碼 |
| geolocation_lat / geolocation_lng | 約略緯度／經度 |
| geolocation_city | 鄉鎮市區 |
| geolocation_county | 縣市 |

## product_category_name_translation.csv

| 欄位 | 說明 |
| --- | --- |
| product_category_name | 類別中文名 |
| product_category_name_english | 類別英文名 |
