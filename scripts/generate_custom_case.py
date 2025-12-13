import os
import csv
import random
import argparse


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_csv(path, rows):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "product", "quantity", "release_slot", "due_slot", "unit_price"])
        writer.writerows(rows)


def generate_orders(
    count=32,
    start_min=1,
    start_max=40,
    due_min=20,
    due_max=60,
    price_min=60,
    price_max=120,
    min_duration=6,
    quantity_min=150,
    quantity_max=250,
):
    rows = []
    for oid in range(1, count + 1):
        product = random.choice([1, 2, 3])
        release_slot = random.randint(start_min, start_max)
        # ensure due respects min_duration and bounds
        low_due = max(due_min, release_slot + min_duration)
        if low_due > due_max:
            # shift release earlier so that duration fits
            release_slot = max(start_min, due_max - min_duration)
            low_due = max(due_min, release_slot + min_duration)
        due_slot = random.randint(low_due, due_max)
        quantity = random.randint(quantity_min, quantity_max)
        unit_price = float(random.randint(price_min, price_max))
        rows.append([oid, product, quantity, release_slot, due_slot, unit_price])
    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate custom case CSV with constraints")
    parser.add_argument("--count", type=int, default=32)
    parser.add_argument("--start_min", type=int, default=1)
    parser.add_argument("--start_max", type=int, default=40)
    parser.add_argument("--due_min", type=int, default=20)
    parser.add_argument("--due_max", type=int, default=60)
    parser.add_argument("--price_min", type=int, default=60)
    parser.add_argument("--price_max", type=int, default=120)
    parser.add_argument("--min_duration", type=int, default=6)
    parser.add_argument("--quantity_min", type=int, default=150)
    parser.add_argument("--quantity_max", type=int, default=250)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    rows = generate_orders(
        count=args.count,
        start_min=args.start_min,
        start_max=args.start_max,
        due_min=args.due_min,
        due_max=args.due_max,
        price_min=args.price_min,
        price_max=args.price_max,
        min_duration=args.min_duration,
        quantity_min=args.quantity_min,
        quantity_max=args.quantity_max,
    )

    base = os.path.join(os.path.dirname(__file__), "..", "data")
    out_path = args.output or os.path.join(base, "custom_case.csv")
    write_csv(out_path, rows)
    print(f"Wrote {out_path} with {len(rows)} orders")


if __name__ == "__main__":
    main()
