import os
import sys
import csv
import argparse
import statistics
from collections import Counter, defaultdict


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def summarize(path, outdir=None):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(
                {
                    "order_id": int(row["order_id"]),
                    "product": int(row["product"]),
                    "quantity": int(row["quantity"]),
                    "release_slot": int(row["release_slot"]),
                    "due_slot": int(row["due_slot"]),
                    "unit_price": float(row["unit_price"]),
                }
            )
    n = len(rows)
    prod_counts = Counter(x["product"] for x in rows)
    quantities = [x["quantity"] for x in rows]
    prices = [x["unit_price"] for x in rows]
    durations = [x["due_slot"] - x["release_slot"] for x in rows]
    release_min = min(x["release_slot"] for x in rows)
    release_max = max(x["release_slot"] for x in rows)
    due_min = min(x["due_slot"] for x in rows)
    due_max = max(x["due_slot"] for x in rows)
    prod_qty = defaultdict(int)
    prod_price = defaultdict(list)
    for x in rows:
        prod_qty[x["product"]] += x["quantity"]
        prod_price[x["product"]].append(x["unit_price"])
    potential_revenue = sum(x["quantity"] * x["unit_price"] for x in rows)
    violations = [x for x in rows if (x["due_slot"] - x["release_slot"]) < 6]

    print(f"文件: {path}")
    print(f"总订单数: {n}")
    print(f"产品分布: {dict(prod_counts)}")
    print(
        f"数量总计: {sum(quantities)} | 平均: {statistics.mean(quantities):.2f} | 范围: [{min(quantities)}, {max(quantities)}]"
    )
    print(
        f"价格均值: {statistics.mean(prices):.2f} | 范围: [{min(prices):.2f}, {max(prices):.2f}]"
    )
    print(
        f"开始slot范围: [{release_min}, {release_max}] | 结束slot范围: [{due_min}, {due_max}]"
    )
    print(
        f"持续时间均值: {statistics.mean(durations):.2f} | 范围: [{min(durations)}, {max(durations)}]"
    )
    print(f"不满足持续≥6的订单数量: {len(violations)}")
    for p in sorted(prod_qty):
        avg_price = statistics.mean(prod_price[p])
        print(f"产品{p}: 总数量={prod_qty[p]} | 平均单价={avg_price:.2f}")
    print(f"理论总收入（数量×单价）: {potential_revenue:.2f}")

    if outdir:
        ensure_dir(outdir)
        base = os.path.splitext(os.path.basename(path))[0]
        with open(os.path.join(outdir, f"{base}_summary.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["metric", "value"])
            w.writerow(["orders_count", n])
            w.writerow(["products_distribution", dict(prod_counts)])
            w.writerow(["quantity_total", sum(quantities)])
            w.writerow(["quantity_mean", f"{statistics.mean(quantities):.2f}"])
            w.writerow(["quantity_min", min(quantities)])
            w.writerow(["quantity_max", max(quantities)])
            w.writerow(["price_mean", f"{statistics.mean(prices):.2f}"])
            w.writerow(["price_min", f"{min(prices):.2f}"])
            w.writerow(["price_max", f"{max(prices):.2f}"])
            w.writerow(["release_range", f"[{release_min},{release_max}]"])
            w.writerow(["due_range", f"[{due_min},{due_max}]"])
            w.writerow(["duration_mean", f"{statistics.mean(durations):.2f}"])
            w.writerow(["duration_min", min(durations)])
            w.writerow(["duration_max", max(durations)])
            w.writerow(["violations_lt_6", len(violations)])
            w.writerow(["potential_revenue", f"{potential_revenue:.2f}"])
        with open(os.path.join(outdir, f"{base}_product_stats.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["product", "total_quantity", "avg_unit_price"])
            for p in sorted(prod_qty):
                w.writerow([p, prod_qty[p], f"{statistics.mean(prod_price[p]):.2f}"])
        bins = [(6, 10), (11, 20), (21, 30), (31, 40), (41, 60)]
        bin_counts = []
        for lo, hi in bins:
            bin_counts.append(sum(1 for d in durations if lo <= d <= hi))
        with open(os.path.join(outdir, f"{base}_duration_hist.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["range", "count"])
            for (lo, hi), c in zip(bins, bin_counts):
                w.writerow([f"{lo}-{hi}", c])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--outdir", default=os.path.join("exp", "output"))
    args = ap.parse_args()
    summarize(args.file, args.outdir)


if __name__ == "__main__":
    main()
