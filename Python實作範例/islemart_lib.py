"""
islemart_lib.py — IsleMart 課程的共用函式庫（傳統 Python 版）

放在這裡的是「每本 Notebook 都會用到」的程式：
    1. 找到資料夾、讀取 9 張表（含正確的資料型態）
    2. 設定 matplotlib 的繁體中文字型
    3. 資料清理管線：把 9 張表整理成「一列一筆訂單」的寬表

Notebook 02 會一步一步拆解第 3 點的每個動作；之後的 Notebook 直接呼叫
build_orders_wide()，確保大家用的是同一套清理邏輯（也就是同一套「指標口徑」）。

需要的套件：pandas、numpy、matplotlib
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. 讀取資料
# ---------------------------------------------------------------------------
TABLE_FILES = {
    "orders": "islemart_orders_dataset.csv",
    "order_items": "islemart_order_items_dataset.csv",
    "order_payments": "islemart_order_payments_dataset.csv",
    "order_reviews": "islemart_order_reviews_dataset.csv",
    "customers": "islemart_customers_dataset.csv",
    "sellers": "islemart_sellers_dataset.csv",
    "products": "islemart_products_dataset.csv",
    "geolocation": "islemart_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# 需要轉成日期時間的欄位
DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
}

# 郵遞區號要當文字讀，否則 "100" 會變成數字 100，"0xx" 開頭的區號會掉 0
STRING_COLUMNS = {
    "customer_zip_code_prefix": str,
    "seller_zip_code_prefix": str,
    "geolocation_zip_code_prefix": str,
}

# 依序尋找資料夾的位置（可用環境變數 ISLEMART_DATA 指定）
_CANDIDATE_DIRS = [
    "islemart_data",
    "../模擬資料_IsleMart/學員版/islemart_data",
    "../../模擬資料_IsleMart/學員版/islemart_data",
    "../islemart_data",
]


def find_data_dir(data_dir: str | os.PathLike | None = None) -> Path:
    """找出 IsleMart CSV 所在的資料夾。"""
    candidates = []
    if data_dir:
        candidates.append(Path(data_dir))
    if os.environ.get("ISLEMART_DATA"):
        candidates.append(Path(os.environ["ISLEMART_DATA"]))
    here = Path(__file__).resolve().parent
    for c in _CANDIDATE_DIRS:
        candidates += [Path.cwd() / c, here / c]
    for c in candidates:
        if (c / TABLE_FILES["orders"]).exists():
            return c.resolve()
    raise FileNotFoundError(
        "找不到 IsleMart 資料。請把 islemart_data 資料夾放在 Notebook 旁邊，"
        "或設定環境變數 ISLEMART_DATA 指向它。"
    )


def load_table(name: str, data_dir=None) -> pd.DataFrame:
    """讀取單一張表，並轉好日期欄位。"""
    path = find_data_dir(data_dir) / TABLE_FILES[name]
    # utf-8-sig：自動去掉檔案開頭的 BOM
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=STRING_COLUMNS)
    for col in DATE_COLUMNS.get(name, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_all(data_dir=None) -> dict[str, pd.DataFrame]:
    """一次讀取 9 張表，回傳 {表名: DataFrame}。"""
    return {name: load_table(name, data_dir) for name in TABLE_FILES}


# ---------------------------------------------------------------------------
# 2. 中文字型
# ---------------------------------------------------------------------------
_FONT_CANDIDATES = [
    "Microsoft JhengHei",   # Windows 微軟正黑體
    "PingFang TC",          # macOS 蘋方
    "Heiti TC",             # macOS 黑體
    "Noto Sans CJK TC",     # Linux / Google Noto
    "Noto Sans TC",
    "Arial Unicode MS",
]


def setup_chinese_font() -> str | None:
    """讓 matplotlib 能顯示繁體中文，回傳實際使用的字型名稱。"""
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in _FONT_CANDIDATES:
        if name in installed:
            plt.rcParams["font.sans-serif"] = [name] + plt.rcParams["font.sans-serif"]
            plt.rcParams["axes.unicode_minus"] = False  # 負號正常顯示
            return name
    print("提醒：找不到中文字型，圖上的中文可能變成方塊。請安裝 Noto Sans TC。")
    return None


# ---------------------------------------------------------------------------
# 3. 清理管線：9 張表 → 一列一筆訂單的寬表
# ---------------------------------------------------------------------------
# 價格異常的判斷：單價 >= 同類別中位數的 20 倍（例如多打了兩個 0）
PRICE_OUTLIER_FACTOR = 20


def normalize_county(s: pd.Series) -> pd.Series:
    """「臺」「台」統一成「台」。"""
    return s.str.replace("臺", "台", regex=False)


def flag_price_outliers(items: pd.DataFrame, products: pd.DataFrame,
                        factor: float = PRICE_OUTLIER_FACTOR) -> pd.Series:
    """回傳布林序列：True 表示這一列的單價異常。"""
    cat = items["product_id"].map(products.set_index("product_id")["product_category_name"])
    cat = cat.fillna("（未分類）")
    category_median = items.groupby(cat)["price"].transform("median")
    return items["price"] >= factor * category_median


def aggregate_items(items: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """明細表 → 一列一筆訂單。"""
    items = items.copy()
    items["is_price_outlier"] = flag_price_outliers(items, products)
    items["price_clean"] = items["price"].where(~items["is_price_outlier"], 0)
    first = items.sort_values("order_item_id").drop_duplicates("order_id")
    agg = items.groupby("order_id").agg(
        item_count=("order_item_id", "count"),
        item_total_raw=("price", "sum"),
        item_total=("price_clean", "sum"),
        freight_total=("freight_value", "sum"),
        has_price_outlier=("is_price_outlier", "any"),
    )
    agg["main_product_id"] = first.set_index("order_id")["product_id"]
    agg["main_seller_id"] = first.set_index("order_id")["seller_id"]
    return agg.reset_index()


def aggregate_payments(payments: pd.DataFrame) -> pd.DataFrame:
    """付款表 → 一列一筆訂單。"""
    p = payments.copy()
    p["voucher_value"] = p["payment_value"].where(p["payment_type"] == "voucher", 0)
    main = (p[p["payment_type"] != "voucher"]
            .sort_values("payment_sequential")
            .drop_duplicates("order_id")
            .set_index("order_id"))
    agg = p.groupby("order_id").agg(
        pay_total=("payment_value", "sum"),
        pay_rows=("payment_sequential", "count"),
        voucher_amount=("voucher_value", "sum"),
    )
    agg["main_payment_type"] = main["payment_type"]
    agg["main_payment_type"] = agg["main_payment_type"].fillna("voucher")
    agg["installments"] = main["payment_installments"]
    return agg.reset_index()


def aggregate_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    """評論表 → 一列一筆訂單：先刪完全重複的列，同一訂單多則評論時取最後回覆的一則。"""
    r = reviews.drop_duplicates()
    r = r.sort_values("review_answer_timestamp").drop_duplicates("order_id", keep="last")
    return r[["order_id", "review_score", "review_comment_message"]].rename(
        columns={"review_comment_message": "review_text"})


def build_orders_wide(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """把 9 張表整理成一列一筆訂單的寬表，並加上分析常用的衍生欄位。"""
    orders = tables["orders"]
    customers = tables["customers"].copy()
    products = tables["products"]

    customers["customer_county"] = normalize_county(customers["customer_county"])

    wide = (orders
            .merge(customers, on="customer_id", how="left", validate="one_to_one")
            .merge(aggregate_items(tables["order_items"], products), on="order_id",
                   how="left", validate="one_to_one")
            .merge(aggregate_payments(tables["order_payments"]), on="order_id",
                   how="left", validate="one_to_one")
            .merge(aggregate_reviews(tables["order_reviews"]), on="order_id",
                   how="left", validate="one_to_one"))
    assert len(wide) == len(orders), "合併後訂單數改變了，檢查 JOIN！"

    # 主要商品的類別
    cat = products.set_index("product_id")["product_category_name"]
    wide["main_category"] = wide["main_product_id"].map(cat).fillna("（未分類）")

    # 時間相關衍生欄位
    wide["purchase_date"] = wide["order_purchase_timestamp"].dt.normalize()
    wide["purchase_month"] = wide["order_purchase_timestamp"].dt.strftime("%Y-%m")
    delivered_day = wide["order_delivered_customer_date"].dt.normalize()

    # 資料品質旗標
    wide["flag_delivered_before_carrier"] = (
        wide["order_delivered_customer_date"] < wide["order_delivered_carrier_date"])
    wide["flag_delivered_missing_date"] = (
        (wide["order_status"] == "delivered") & wide["order_delivered_customer_date"].isna())
    wide["flag_canceled_with_delivery"] = (
        (wide["order_status"] == "canceled") & wide["order_delivered_customer_date"].notna())
    wide["flag_pay_mismatch"] = (
        (wide["pay_total"] - (wide["item_total_raw"] + wide["freight_total"])).abs() > 1)

    # 配送指標：只對「已送達、時間合理」的訂單計算
    valid = ((wide["order_status"] == "delivered")
             & wide["order_delivered_customer_date"].notna()
             & ~wide["flag_delivered_before_carrier"])
    wide["is_valid_delivery"] = valid
    wide["delivery_days"] = ((wide["order_delivered_customer_date"]
                              - wide["order_purchase_timestamp"]).dt.total_seconds() / 86400
                             ).where(valid)
    wide["late_days"] = (delivered_day - wide["order_estimated_delivery_date"]).dt.days.where(valid)
    wide["is_late"] = (wide["late_days"] > 0).where(valid)
    return wide


# ---------------------------------------------------------------------------
# 指標定義（指標定義表的程式版本）
# ---------------------------------------------------------------------------
def revenue(wide: pd.DataFrame) -> float:
    """營收：已送達訂單的商品售價加總；不含運費、不扣折價券、排除價格異常。"""
    return float(wide.loc[wide["order_status"] == "delivered", "item_total"].sum())


def late_rate(wide: pd.DataFrame) -> float:
    """延遲率：有效送達訂單中，送達日晚於預計到貨日的比例。"""
    return float(wide.loc[wide["is_valid_delivery"], "is_late"].astype(float).mean())


def avg_score(wide: pd.DataFrame) -> float:
    """平均評分：每筆訂單一則評論（已去重）。"""
    return float(wide["review_score"].mean())
