#!/usr/bin/env python3
"""
weekly_report.py — 每週一自動產出 IsleMart 營運週報草稿（課程 M10）

用法：
    python scripts/weekly_report.py                         # 上一個完整週（週一到週日）
    python scripts/weekly_report.py --week-start 2025-12-15 # 指定週（IsleMart 是靜態資料，課堂用這個）

做的事（對應講義 M10 的排程提示）：
    1. 計算本週訂單數、營收、延遲率、平均評分，並與前四週平均比較
    2. 任何指標變動超過門檻（預設 10%），找出影響最大的縣市與類別
    3. 所有數字都用 islemart_lib 的指標定義
    4. 產出一頁式週報（Markdown 與 HTML），標題寫最重要的一個變化
    5. 不寄出：只存成草稿放在 drafts/，由人確認後再發送
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import islemart_lib as L  # noqa: E402

METRICS = {
    "訂單數": lambda df: float(len(df)),
    "營收": L.revenue,
    "延遲率": L.late_rate,
    "平均評分": L.avg_score,
}
# 指標變差的方向：營收、訂單數下降是壞事；延遲率上升是壞事
WORSE_IF_UP = {"延遲率"}
# 比率型指標：變化用百分點表示，避免「延遲率上升 500%」這種難懂的寫法
RATE_METRICS = {"延遲率"}


def fmt(name: str, v: float) -> str:
    if name == "營收":
        return f"{v:,.0f} 元"
    if name == "延遲率":
        return f"{v:.1%}"
    if name == "平均評分":
        return f"{v:.2f}"
    return f"{v:,.0f}"


def change_text(name: str, cur: dict, base: dict, absolute: bool = False) -> str:
    """比率型指標（延遲率）用「百分點」表示變化，其他指標用百分比。"""
    if name in RATE_METRICS:
        pp = (cur[name] - base[name]) * 100
        return f"{abs(pp):.1f} 個百分點" if absolute else f"{pp:+.1f} 個百分點"
    rel = cur[name] / base[name] - 1 if base[name] else 0.0
    return f"{abs(rel):.0%}" if absolute else f"{rel:+.1%}"


def last_complete_week(today: date) -> date:
    """今天之前最近一個完整週的週一。"""
    this_monday = today - timedelta(days=today.weekday())
    return this_monday - timedelta(days=7)


def weekly_metrics(wide: pd.DataFrame, start: pd.Timestamp) -> dict[str, float]:
    sel = wide[(wide["purchase_date"] >= start) & (wide["purchase_date"] < start + pd.Timedelta(days=7))]
    return {k: f(sel) for k, f in METRICS.items()}


def drilldown(wide: pd.DataFrame, start: pd.Timestamp, metric: str, by: str) -> pd.DataFrame:
    """比較本週與前四週，找出某指標變化最大的分組。"""
    end = start + pd.Timedelta(days=7)
    cur = wide[(wide["purchase_date"] >= start) & (wide["purchase_date"] < end)]
    base = wide[(wide["purchase_date"] >= start - pd.Timedelta(days=28)) & (wide["purchase_date"] < start)]
    f = METRICS[metric]
    rows = []
    for key in sorted(set(cur[by].dropna())):
        c, b = cur[cur[by] == key], base[base[by] == key]
        if len(c) >= 20 and len(b) >= 40:
            rows.append({by: key, "本週": f(c), "前四週": f(b) / (4 if metric in ("訂單數", "營收") else 1)})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["變化"] = out["本週"] - out["前四週"]
    return out.reindex(out["變化"].abs().sort_values(ascending=False).index).head(3)


def build_report(wide: pd.DataFrame, start: pd.Timestamp, threshold: float) -> tuple[str, str]:
    cur = weekly_metrics(wide, start)
    prev = [weekly_metrics(wide, start - pd.Timedelta(days=7 * i)) for i in range(1, 5)]
    base = {k: sum(p[k] for p in prev) / 4 for k in METRICS}
    change = {k: (cur[k] / base[k] - 1) if base[k] else 0.0 for k in METRICS}

    flagged = [k for k in METRICS if abs(change[k]) > threshold]
    headline_metric = max(METRICS, key=lambda k: abs(change[k]))
    direction = "上升" if change[headline_metric] > 0 else "下降"
    end = start + pd.Timedelta(days=6)
    title = (f"{start:%m/%d}–{end:%m/%d} {headline_metric}較前四週平均{direction} "
             f"{change_text(headline_metric, cur, base, absolute=True)}（{fmt(headline_metric, cur[headline_metric])}）")

    lines = [f"# {title}", "",
             f"週期：{start:%Y-%m-%d} 至 {end:%Y-%m-%d}｜比較基準：前四週平均｜門檻：±{threshold:.0%}", "",
             "## KPI", "", "| 指標 | 本週 | 前四週平均 | 變化 | 提醒 |", "| --- | --- | --- | --- | --- |"]
    for k in METRICS:
        worse = (change[k] > 0) == (k in WORSE_IF_UP)
        mark = ("需注意" if worse else "表現佳") if k in flagged else ""
        lines.append(f"| {k} | {fmt(k, cur[k])} | {fmt(k, base[k])} | {change_text(k, cur, base)} | {mark} |")

    for k in flagged:
        lines += ["", f"## {k}：影響最大的縣市與類別", ""]
        for by, label in (("customer_county", "縣市"), ("main_category", "類別")):
            dd = drilldown(wide, start, k, by)
            if dd.empty:
                continue
            items = "、".join(f"{r[by]}（{fmt(k, r['前四週'])} → {fmt(k, r['本週'])}）" for _, r in dd.iterrows())
            lines.append(f"- {label}：{items}")

    lines += ["", "---",
              "定義：營收＝已送達訂單商品售價，不含運費、排除價格異常；延遲率＝有效送達訂單中晚於預計到貨日的比例；"
              "平均評分＝每筆訂單一則評論。週別依下單日計算；最近一週的訂單可能尚未全部送達。",
              "", "**本檔為自動產生的草稿，請確認數字後再發送。**"]
    md = "\n".join(lines)
    return title, md


def md_to_html(md: str) -> str:
    """極簡的 Markdown → HTML（只處理本報告用到的語法，不需安裝額外套件）。"""
    html, in_table, in_list = [], False, False
    for line in md.splitlines():
        if line.startswith("| ---"):
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if not in_table else "td"
            if not in_table:
                html.append("<table>")
                in_table = True
            html.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            html.append("</table>")
            in_table = False
        if line.startswith("- "):
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{line[2:]}</li>")
            continue
        if in_list:
            html.append("</ul>")
            in_list = False
        if line.startswith("# "):
            html.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html.append(f"<h2>{line[3:]}</h2>")
        elif line == "---":
            html.append("<hr>")
        elif line.startswith("**") and line.endswith("**"):
            html.append(f"<p><b>{line.strip('*')}</b></p>")
        elif line:
            html.append(f"<p>{line}</p>")
    if in_table:
        html.append("</table>")
    if in_list:
        html.append("</ul>")
    style = ("body{font-family:'Noto Sans TC','Microsoft JhengHei','PingFang TC',sans-serif;max-width:860px;"
             "margin:32px auto;padding:0 16px;color:#3D4A55;line-height:1.6}h1{color:#172A3A;font-size:24px}"
             "table{border-collapse:collapse;width:100%}th,td{border:1px solid #E4DED2;padding:6px 10px;text-align:left}"
             "th{background:#172A3A;color:#F7F5EF}")
    return f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><style>{style}</style></head><body>{''.join(html)}</body></html>"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="IsleMart 週報草稿")
    ap.add_argument("--week-start", help="週一日期 YYYY-MM-DD（預設：上一個完整週）")
    ap.add_argument("--input", help="CSV 資料夾（預設自動尋找）")
    ap.add_argument("--outdir", default="drafts", help="草稿輸出資料夾")
    ap.add_argument("--threshold", type=float, default=0.10, help="提醒門檻，預設 0.10（10%%）")
    args = ap.parse_args(argv)

    start = pd.Timestamp(args.week_start) if args.week_start else pd.Timestamp(last_complete_week(date.today()))
    if start.weekday() != 0:
        print(f"錯誤：{start:%Y-%m-%d} 不是週一", file=sys.stderr)
        return 1

    wide = L.build_orders_wide(L.load_all(args.input))
    if start + pd.Timedelta(days=6) > wide["purchase_date"].max():
        print(f"錯誤：資料只到 {wide['purchase_date'].max():%Y-%m-%d}，這一週還不完整", file=sys.stderr)
        return 1

    title, md = build_report(wide, start, args.threshold)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"weekly_report_{start:%Y-%m-%d}"
    (out / f"{stem}.md").write_text(md, encoding="utf-8")
    (out / f"{stem}.html").write_text(md_to_html(md), encoding="utf-8")
    print(f"週報草稿已產生：{out / stem}.md／.html")
    print(f"標題：{title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
