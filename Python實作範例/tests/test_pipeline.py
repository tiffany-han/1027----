"""
清理管線的自動化測試（課程 M10）

執行方式（兩種都可以）：
    python -m pytest tests/        # 有安裝 pytest 時
    python tests/test_pipeline.py  # 沒有 pytest 也能跑
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import islemart_lib as L  # noqa: E402

_T = L.load_all()
_W = L.build_orders_wide(_T)


def test_one_row_per_order():
    assert len(_W) == len(_T["orders"])
    assert not _W["order_id"].duplicated().any()


def test_no_join_bloat_in_revenue():
    # 寬表算的營收，必須等於直接從明細表算的營收
    it = _T["order_items"].copy()
    it["outlier"] = L.flag_price_outliers(it, _T["products"])
    ids = set(_T["orders"].loc[_T["orders"]["order_status"] == "delivered", "order_id"])
    expected = it.loc[it["order_id"].isin(ids) & ~it["outlier"], "price"].sum()
    assert abs(L.revenue(_W) - expected) < 1


def test_price_outlier_rule_catches_100x():
    items = pd.DataFrame({"product_id": ["a"] * 5, "price": [100, 120, 110, 105, 11000]})
    products = pd.DataFrame({"product_id": ["a"], "product_category_name": ["文具書籍"]})
    assert L.flag_price_outliers(items, products).tolist() == [False, False, False, False, True]


def test_county_normalized():
    assert not _W["customer_county"].str.contains("臺", na=False).any()


def test_delivery_metrics_are_sane():
    assert (_W["delivery_days"].dropna() >= 0).all()
    assert 0 <= L.late_rate(_W) <= 1
    assert 1 <= L.avg_score(_W) <= 5


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("通過", t.__name__)
    print(f"全部 {len(tests)} 項測試通過")
