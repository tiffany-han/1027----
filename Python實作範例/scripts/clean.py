#!/usr/bin/env python3
"""
clean.py — 把 IsleMart 的 9 張表清理成「一列一筆訂單」的寬表（課程 M10）

用法：
    python scripts/clean.py --input 資料夾 --output wide_orders.csv

特色：
    - 每一步都記錄處理前後的列數（可稽核）
    - 內建檢查：任何一項不通過就以錯誤碼 1 結束，排程時會被發現
    - 同一份輸入一定得到同一份輸出（可重跑、可交接）
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import islemart_lib as L  # noqa: E402

log = logging.getLogger("clean")


def run_checks(tables, wide) -> list[str]:
    """回傳不通過的檢查項目；空清單代表全部通過。"""
    failures = []
    if len(wide) != len(tables["orders"]):
        failures.append(f"訂單數改變：{len(tables['orders'])} → {len(wide)}")
    if wide["order_id"].duplicated().any():
        failures.append("寬表的 order_id 有重複")
    if (wide["item_total"] < 0).any():
        failures.append("售價加總出現負值")
    if wide["customer_county"].str.contains("臺", na=False).any():
        failures.append("縣市名稱仍有「臺」")
    if (wide["delivery_days"] < 0).any():
        failures.append("配送天數出現負值")
    return failures


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="IsleMart 清理管線")
    ap.add_argument("--input", help="CSV 資料夾（預設自動尋找）")
    ap.add_argument("--output", default="wide_orders.csv", help="輸出的寬表 CSV")
    ap.add_argument("--quiet", action="store_true", help="只顯示警告與錯誤")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    data_dir = L.find_data_dir(args.input)
    log.info("讀取資料：%s", data_dir)
    tables = L.load_all(data_dir)
    for name, df in tables.items():
        log.info("  %-22s %8s 列", name, f"{len(df):,}")

    wide = L.build_orders_wide(tables)
    log.info("寬表：%s 列 × %s 欄", f"{len(wide):,}", wide.shape[1])
    for flag in [c for c in wide.columns if c.startswith("flag_")] + ["has_price_outlier"]:
        log.info("  %-32s %6s 筆", flag, f"{int(wide[flag].sum()):,}")

    failures = run_checks(tables, wide)
    if failures:
        for f in failures:
            log.error("檢查不通過：%s", f)
        return 1
    log.info("全部檢查通過")

    wide.to_csv(args.output, index=False, encoding="utf-8-sig")
    log.info("已輸出：%s", Path(args.output).resolve())
    log.info("營收 %s 元｜延遲率 %.2f%%｜平均評分 %.3f",
             f"{L.revenue(wide):,.0f}", L.late_rate(wide) * 100, L.avg_score(wide))
    return 0


if __name__ == "__main__":
    sys.exit(main())
