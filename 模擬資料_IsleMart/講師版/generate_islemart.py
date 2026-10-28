#!/usr/bin/env python3
"""
島嶼市集 IsleMart 模擬電商資料產生器
--------------------------------------
* 結構參照 Olist 公開資料集的 9 張表（欄位命名邏輯相同），但所有內容皆為隨機產生的虛構資料，
  不含任何 Olist 原始資料。
* 只用 Python 標準函式庫，macOS / Windows / Linux 皆可直接執行：
      python3 generate_islemart.py            # 預設輸出到 ./islemart_data
      python3 generate_islemart.py --orders 20000 --seed 7 --out mydata
* 固定 seed 即可重現同一份資料（標準答案才能對得上）。

刻意埋入的「可分析規律」與「髒資料陷阱」列在 data_dictionary.md 與 instructor_answer_key.md。
"""
import argparse
import csv
import os
import random
from itertools import accumulate
from collections import defaultdict
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# 參考資料：縣市 / 區 / 郵遞區號 / 約略座標 / 人口權重 / 物流區域
# 座標為約略值，僅供地圖練習
# ---------------------------------------------------------------------------
DISTRICTS = [
    # county, city(district), zip, lat, lng, weight, zone
    ("台北市", "中正區", "100", 25.032, 121.519, 3, "north"),
    ("台北市", "大安區", "106", 25.026, 121.543, 5, "north"),
    ("台北市", "信義區", "110", 25.033, 121.567, 4, "north"),
    ("台北市", "內湖區", "114", 25.069, 121.589, 4, "north"),
    ("新北市", "板橋區", "220", 25.011, 121.459, 6, "north"),
    ("新北市", "新莊區", "242", 25.036, 121.450, 5, "north"),
    ("新北市", "中和區", "235", 24.999, 121.499, 5, "north"),
    ("新北市", "三重區", "241", 25.062, 121.487, 4, "north"),
    ("新北市", "淡水區", "251", 25.169, 121.441, 2, "north"),
    ("基隆市", "仁愛區", "200", 25.128, 121.740, 2, "north"),
    ("桃園市", "桃園區", "330", 24.993, 121.301, 5, "north"),
    ("桃園市", "中壢區", "320", 24.965, 121.225, 5, "north"),
    ("新竹市", "東區", "300", 24.801, 120.971, 3, "north"),
    ("新竹縣", "竹北市", "302", 24.839, 121.004, 3, "north"),
    ("宜蘭縣", "宜蘭市", "260", 24.757, 121.753, 2, "east"),
    ("苗栗縣", "苗栗市", "360", 24.560, 120.821, 2, "central"),
    ("台中市", "西屯區", "407", 24.181, 120.646, 5, "central"),
    ("台中市", "北屯區", "406", 24.182, 120.686, 5, "central"),
    ("台中市", "豐原區", "420", 24.252, 120.722, 3, "central"),
    ("彰化縣", "彰化市", "500", 24.081, 120.538, 4, "central"),
    ("南投縣", "南投市", "540", 23.910, 120.684, 2, "central"),
    ("雲林縣", "斗六市", "640", 23.709, 120.543, 2, "central"),
    ("嘉義市", "東區", "600", 23.480, 120.453, 2, "south"),
    ("嘉義縣", "太保市", "612", 23.459, 120.333, 2, "south"),
    ("台南市", "東區", "701", 22.981, 120.224, 4, "south"),
    ("台南市", "永康區", "710", 23.026, 120.257, 4, "south"),
    ("高雄市", "苓雅區", "802", 22.622, 120.312, 4, "south"),
    ("高雄市", "左營區", "813", 22.677, 120.294, 4, "south"),
    ("高雄市", "鳳山區", "830", 22.627, 120.357, 4, "south"),
    ("屏東縣", "屏東市", "900", 22.669, 120.486, 3, "south"),
    ("花蓮縣", "花蓮市", "970", 23.977, 121.604, 2, "east"),
    ("台東縣", "台東市", "950", 22.756, 121.150, 1, "east"),
    ("澎湖縣", "馬公市", "880", 23.566, 119.586, 1, "island"),
    ("金門縣", "金城鎮", "893", 24.434, 118.318, 1, "island"),
    ("連江縣", "南竿鄉", "209", 26.159, 119.951, 1, "island"),
]

# 賣家集中在北部與台中
SELLER_COUNTY_BOOST = {"台北市": 3, "新北市": 3, "桃園市": 2.5, "台中市": 2, "高雄市": 1.2}

# 類別：中文名, 英文名, 價格區間(TWD), 權重, 重量區間(g)
CATEGORIES = [
    ("3C配件", "electronics_accessories", (199, 2490), 12, (50, 800)),
    ("居家生活", "home_living", (149, 3990), 12, (200, 6000)),
    ("美妝保養", "beauty_care", (199, 2290), 11, (50, 900)),
    ("服飾配件", "fashion", (290, 2990), 10, (150, 1200)),
    ("運動戶外", "sports_outdoor", (299, 5990), 7, (200, 9000)),
    ("母嬰用品", "baby", (199, 3490), 6, (100, 5000)),
    ("寵物用品", "pet_supplies", (149, 2490), 6, (200, 12000)),
    ("食品飲料", "food_beverage", (99, 1290), 9, (200, 5000)),
    ("文具書籍", "books_stationery", (59, 990), 6, (50, 1500)),
    ("家電", "home_appliances", (990, 19990), 6, (800, 15000)),
    ("玩具", "toys", (199, 2990), 4, (100, 3000)),
    ("保健食品", "health_supplements", (390, 2990), 5, (100, 1200)),
    ("廚房用品", "kitchenware", (149, 3490), 5, (150, 5000)),
    ("汽機車用品", "auto_moto", (199, 4990), 3, (100, 6000)),
]
# 陷阱：翻譯表故意缺少這兩個類別
MISSING_TRANSLATION = {"保健食品", "汽機車用品"}

PAYMENT_TYPES = [("credit_card", 58), ("mobile_pay", 22), ("cod_store_pickup", 11), ("atm_transfer", 9)]

POS_TITLES = ["很滿意", "推薦", "超讚", "會回購", "物超所值", ""]
NEG_TITLES = ["很失望", "不推", "等太久", "有問題", ""]
POS_MSG = [
    "出貨很快，包裝完整，商品跟描述一樣。",
    "品質不錯，價格合理，下次還會再買。",
    "比預期早到，賣家回覆也很快，推薦！",
    "東西很好用，CP值高。",
    "包裝用心，收到很開心。",
]
NEU_MSG = [
    "商品還可以，跟照片有一點落差。",
    "普通，沒有特別驚艷。",
    "到貨時間還算正常，品質中規中矩。",
]
NEG_MSG = [
    "等了好久才到，已經過了預計到貨日。",
    "物流超慢，客服也沒有回應。",
    "收到時外盒破損，商品有刮傷。",
    "跟描述不符，想退貨。",
    "延遲到貨又沒通知，非常失望。",
    "只收到部分商品，其他的不知道在哪裡。",
]

START = date(2024, 1, 1)
END = date(2025, 12, 31)


def uid(rng):
    return "%032x" % rng.getrandbits(128)


def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def day_weight(d):
    """每日下單量的相對權重：成長趨勢 + 週期 + 檔期 + 春節低點"""
    months = (d.year - START.year) * 12 + d.month - 1
    w = 1.0 * (1.025 ** months)  # 每月約 2.5% 成長
    if d.weekday() >= 5:
        w *= 0.9
    md = (d.month, d.day)
    if md == (11, 11):
        w *= 5.0
    elif d.month == 11 and 1 <= d.day <= 12:
        w *= 1.8
    elif md == (12, 12):
        w *= 2.5
    elif md == (6, 18):
        w *= 3.0
    elif d.month == 6 and 10 <= d.day <= 18:
        w *= 1.4
    # 母親節前一週（五月第二個週日前）
    if d.month == 5:
        first = date(d.year, 5, 1)
        second_sun = first + timedelta(days=(6 - first.weekday()) % 7 + 7)
        if second_sun - timedelta(days=8) <= d < second_sun:
            w *= 1.6
    # 春節（物流停擺、下單低）
    cny = {2024: date(2024, 2, 8), 2025: date(2025, 1, 27)}[d.year]
    if cny <= d <= cny + timedelta(days=6):
        w *= 0.35
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orders", type=int, default=60000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="islemart_data")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    os.makedirs(args.out, exist_ok=True)

    d_weights = [x[5] for x in DISTRICTS]

    # ---------------- sellers ----------------
    n_sellers = max(60, args.orders // 200)
    sellers = []
    s_weights = [x[5] * SELLER_COUNTY_BOOST.get(x[0], 0.4) for x in DISTRICTS]
    for _ in range(n_sellers):
        dist = rng.choices(DISTRICTS, weights=s_weights)[0]
        sellers.append({
            "seller_id": uid(rng),
            "seller_zip_code_prefix": dist[2],
            "seller_city": dist[1],
            "seller_county": dist[0],
            "_zone": dist[6],
            # 規律：約 6% 的「問題賣家」出貨慢、延遲多
            "_bad": rng.random() < 0.06,
            # 賣家規模呈長尾
            "_size": rng.paretovariate(1.3),
        })
    seller_cw = list(accumulate(s["_size"] for s in sellers))

    # ---------------- products ----------------
    n_products = max(300, args.orders // 6)
    products = []
    cat_w = [c[3] for c in CATEGORIES]
    for _ in range(n_products):
        cat = rng.choices(CATEGORIES, weights=cat_w)[0]
        lo, hi = cat[2]
        base_price = round(rng.triangular(lo, hi, lo + (hi - lo) * 0.25))
        base_price = int(base_price // 10 * 10 + 9) if base_price > 100 else base_price
        wlo, whi = cat[4]
        cat_name = cat[0]
        if rng.random() < 0.02:  # 陷阱：缺類別
            cat_name = ""
        products.append({
            "product_id": uid(rng),
            "product_category_name": cat_name,
            "product_name_length": rng.randint(8, 60),
            "product_description_length": rng.randint(30, 3000) if rng.random() > 0.015 else "",
            "product_photos_qty": rng.randint(1, 10),
            "product_weight_g": rng.randint(wlo, whi),
            "product_length_cm": rng.randint(10, 80),
            "product_height_cm": rng.randint(2, 60),
            "product_width_cm": rng.randint(8, 60),
            "_price": base_price,
            "_seller": rng.choices(range(n_sellers), cum_weights=seller_cw)[0],
            "_pop": rng.paretovariate(1.6),
        })
    prod_cw = list(accumulate(p["_pop"] for p in products))

    # ---------------- customers (unique people) ----------------
    n_people = int(args.orders * 0.80)
    people = []
    for _ in range(n_people):
        dist = rng.choices(DISTRICTS, weights=d_weights)[0]
        county = dist[0]
        if county.startswith("台") and rng.random() < 0.12:  # 陷阱：台/臺 混用
            county = "臺" + county[1:]
        people.append({"uid": uid(rng), "dist": dist, "county": county,
                       "loyal": rng.random() < 0.12})

    # ---------------- dates ----------------
    all_days = [START + timedelta(days=i) for i in range((END - START).days + 1)]
    day_cw = list(accumulate(day_weight(d) for d in all_days))

    customers, orders, items, payments, reviews = [], [], [], [], []
    used_people = set()
    used_list, used_cw, next_new = [], [], 0

    for _ in range(args.orders):
        # 讓每位顧客至少下一單的機率高一點，再加上忠誠顧客回購
        # 規律：約 8 成訂單來自新顧客，其餘為回購（忠誠顧客回購機率較高）
        if next_new < n_people and (not used_list or rng.random() < 0.80):
            pi = next_new
            next_new += 1
            used_list.append(pi)
            used_cw.append((used_cw[-1] if used_cw else 0) + (6 if people[pi]["loyal"] else 1))
        else:
            pi = rng.choices(used_list, cum_weights=used_cw)[0]
        used_people.add(pi)
        person = people[pi]
        dist = person["dist"]

        # 陷阱：每筆訂單都產生新的 customer_id，要用 customer_unique_id 才能算回購
        cid = uid(rng)
        customers.append({
            "customer_id": cid,
            "customer_unique_id": person["uid"],
            "customer_zip_code_prefix": dist[2],
            "customer_city": dist[1],
            "customer_county": person["county"],
        })

        d = rng.choices(all_days, cum_weights=day_cw)[0]
        purchase = datetime(d.year, d.month, d.day) + timedelta(
            seconds=rng.randint(0, 86399))
        oid = uid(rng)

        # 品項
        n_items = rng.choices([1, 2, 3, 4], weights=[82, 12, 4, 2])[0]
        pidx = rng.choices(range(n_products), cum_weights=prod_cw)[0]
        chosen = [pidx]
        for _ in range(n_items - 1):
            if rng.random() < 0.6:
                chosen.append(pidx)  # 同商品多件
            else:
                chosen.append(rng.choices(range(n_products), cum_weights=prod_cw)[0])

        # 狀態
        status = rng.choices(
            ["delivered", "shipped", "canceled", "processing", "unavailable"],
            weights=[95.8, 1.2, 1.3, 0.9, 0.8])[0]
        # 最後兩週下的單多半還沒送達
        if (END - d).days < 10 and status == "delivered" and rng.random() < 0.5:
            status = "shipped"

        approved = purchase + timedelta(minutes=rng.randint(5, 600))
        is_island = dist[6] == "island"
        promise_days = 12 if is_island else (7 if dist[6] == "east" else 5)
        estimated = datetime(purchase.year, purchase.month, purchase.day) + timedelta(days=promise_days)

        main_seller = sellers[products[chosen[0]]["_seller"]]
        peak = (d.month == 11 and 9 <= d.day <= 15) or (d.month, d.day) in [(12, 12), (12, 13), (6, 18), (6, 19)]
        cny = d.year == 2024 and date(2024, 2, 5) <= d <= date(2024, 2, 14) or \
            d.year == 2025 and date(2025, 1, 24) <= d <= date(2025, 2, 2)

        handling = rng.uniform(0.3, 1.8)
        if main_seller["_bad"]:
            handling += rng.uniform(1.5, 5)
        if peak:
            handling += rng.uniform(0.5, 2.5)
        if cny:
            handling += rng.uniform(2, 5)
        carrier = approved + timedelta(days=handling)

        transit = {"north": 1.0, "central": 1.4, "south": 1.8, "east": 2.6, "island": 5.0}[dist[6]]
        if main_seller["_zone"] != dist[6]:
            transit += 0.8
        transit = rng.lognormvariate(0, 0.35) * transit
        if peak:
            transit += rng.uniform(0.5, 2)
        delivered = carrier + timedelta(days=transit, hours=rng.randint(0, 10))

        approved_s = fmt(approved)
        carrier_s = fmt(carrier)
        delivered_s = fmt(delivered)
        if status == "canceled":
            carrier_s = delivered_s = ""
            if rng.random() < 0.3:
                approved_s = ""
            if rng.random() < 0.005:  # 極少數：已取消卻有送達日（陷阱）
                delivered_s = fmt(delivered)
        elif status in ("processing", "unavailable"):
            carrier_s = delivered_s = ""
        elif status == "shipped":
            delivered_s = ""
        else:  # delivered
            if rng.random() < 0.003:  # 陷阱：送達早於出貨
                delivered_s = fmt(carrier - timedelta(days=rng.randint(1, 3)))
            if rng.random() < 0.002:  # 陷阱：已送達卻沒有送達日
                delivered_s = ""

        orders.append({
            "order_id": oid,
            "customer_id": cid,
            "order_status": status,
            "order_purchase_timestamp": fmt(purchase),
            "order_approved_at": approved_s,
            "order_delivered_carrier_date": carrier_s,
            "order_delivered_customer_date": delivered_s,
            "order_estimated_delivery_date": fmt(estimated),
        })

        # order_items
        total = 0.0
        for k, p_i in enumerate(chosen, start=1):
            p = products[p_i]
            price = p["_price"]
            if (d.month, d.day) in [(11, 11), (12, 12), (6, 18)]:
                price = round(price * rng.uniform(0.7, 0.9))
            if rng.random() < 0.0008:  # 陷阱：價格多打兩個 0
                price = price * 100
            w = p["product_weight_g"]
            freight = 0 if price >= 990 and not is_island else \
                round(60 + w / 1000 * 15 + (120 if is_island else 0))
            if n_items > 1 and k > 1:
                freight = 0  # 同一筆訂單只收一次運費（教學用：運費放在第一列）
            items.append({
                "order_id": oid,
                "order_item_id": k,
                "product_id": p["product_id"],
                "seller_id": sellers[p["_seller"]]["seller_id"],
                "shipping_limit_date": fmt(approved + timedelta(days=2)),
                "price": price,
                "freight_value": freight,
            })
            total += price + freight

        # payments（陷阱：一筆訂單可能多列；少數金額與明細不符）
        ptype = rng.choices([x[0] for x in PAYMENT_TYPES], weights=[x[1] for x in PAYMENT_TYPES])[0]
        pay_total = total
        if rng.random() < 0.006:
            pay_total = round(total * rng.uniform(0.85, 0.98))  # 折價券未入明細
        seq = 1
        if rng.random() < 0.04:
            voucher = min(pay_total, rng.choice([50, 100, 150, 200, 300]))
            payments.append({"order_id": oid, "payment_sequential": seq,
                             "payment_type": "voucher", "payment_installments": 1,
                             "payment_value": voucher})
            pay_total -= voucher
            seq += 1
        inst = 1
        if ptype == "credit_card" and pay_total >= 3000:
            inst = rng.choices([1, 3, 6, 12], weights=[45, 25, 20, 10])[0]
        if pay_total > 0 or seq == 1:
            payments.append({"order_id": oid, "payment_sequential": seq,
                             "payment_type": ptype, "payment_installments": inst,
                             "payment_value": round(pay_total)})

        # reviews
        if status in ("processing",) or (status == "shipped" and rng.random() < 0.7):
            continue
        if rng.random() < 0.02:
            continue  # 少數訂單沒有評論
        late_days = None
        if delivered_s and status == "delivered":
            late_days = (delivered - estimated).total_seconds() / 86400
        if status in ("canceled", "unavailable"):
            score = rng.choices([1, 2, 3], weights=[75, 15, 10])[0]
            base = None
        elif late_days is None:
            score = rng.choices([1, 2, 3, 4, 5], weights=[35, 10, 15, 15, 25])[0]
        elif late_days > 0:
            # 規律：延遲越久分數越低
            if late_days > 4:
                score = rng.choices([1, 2, 3, 4, 5], weights=[62, 14, 12, 6, 6])[0]
            else:
                score = rng.choices([1, 2, 3, 4, 5], weights=[30, 15, 22, 16, 17])[0]
        else:
            score = rng.choices([1, 2, 3, 4, 5], weights=[5, 3, 9, 21, 62])[0]
        # 品類的小差異：家電與 3C 配件較挑剔
        cat0 = products[chosen[0]]["product_category_name"]
        if cat0 in ("家電", "3C配件") and score >= 4 and rng.random() < 0.12:
            score -= 1

        ref_time = delivered if (delivered_s and status == "delivered") else purchase + timedelta(days=promise_days)
        created = datetime(ref_time.year, ref_time.month, ref_time.day) + timedelta(days=1)
        answered = created + timedelta(hours=rng.randint(3, 96))
        if rng.random() < 0.55:
            title, msg = "", ""
        else:
            if score >= 4:
                title, msg = rng.choice(POS_TITLES), rng.choice(POS_MSG)
            elif score == 3:
                title, msg = "", rng.choice(NEU_MSG)
            else:
                title, msg = rng.choice(NEG_TITLES), rng.choice(NEG_MSG)
        n_rev = 2 if rng.random() < 0.01 else 1  # 陷阱：同一訂單兩則評論
        for _ in range(n_rev):
            reviews.append({
                "review_id": uid(rng),
                "order_id": oid,
                "review_score": score,
                "review_comment_title": title,
                "review_comment_message": msg,
                "review_creation_date": fmt(created),
                "review_answer_timestamp": fmt(answered),
            })

    # 陷阱：一小撮完全重複的評論列
    for r in rng.sample(reviews, k=max(1, len(reviews) // 1500)):
        reviews.append(dict(r))
    rng.shuffle(reviews)

    # geolocation：每個郵遞區號多筆、座標有抖動（像 Olist）
    geo = []
    for dist in DISTRICTS:
        for _ in range(rng.randint(8, 25)):
            county = dist[0]
            if county.startswith("台") and rng.random() < 0.3:
                county = "臺" + county[1:]
            geo.append({
                "geolocation_zip_code_prefix": dist[2],
                "geolocation_lat": round(dist[3] + rng.uniform(-0.02, 0.02), 6),
                "geolocation_lng": round(dist[4] + rng.uniform(-0.02, 0.02), 6),
                "geolocation_city": dist[1],
                "geolocation_county": county,
            })

    translation = [{"product_category_name": c[0], "product_category_name_english": c[1]}
                   for c in CATEGORIES if c[0] not in MISSING_TRANSLATION]

    def write(name, rows, fields=None):
        fields = fields or [k for k in rows[0].keys() if not k.startswith("_")]
        path = os.path.join(args.out, name)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        return path

    write("islemart_customers_dataset.csv", customers)
    write("islemart_sellers_dataset.csv", sellers)
    write("islemart_products_dataset.csv", products)
    write("islemart_orders_dataset.csv", orders)
    write("islemart_order_items_dataset.csv", items)
    write("islemart_order_payments_dataset.csv", payments)
    write("islemart_order_reviews_dataset.csv", reviews)
    write("islemart_geolocation_dataset.csv", geo)
    write("product_category_name_translation.csv", translation)

    print("orders", len(orders), "items", len(items), "payments", len(payments),
          "reviews", len(reviews), "customers", len(customers),
          "unique people", len(used_people), "sellers", len(sellers),
          "products", len(products))


if __name__ == "__main__":
    main()
