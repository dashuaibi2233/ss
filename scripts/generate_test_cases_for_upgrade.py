import os
import csv
import random


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_csv(path, rows):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "product", "quantity", "release_slot", "due_slot", "unit_price"])
        writer.writerows(rows)


def case_high_penalty_cluster(n=24):
    rows = []
    oid = 1
    for _ in range(n // 3):
        product = random.choice([1, 2, 3])
        quantity = random.randint(180, 260)
        unit_price = random.choice([95.0, 100.0, 105.0])
        release_slot = 1
        due_slot = random.choice([7, 8, 9])
        rows.append([oid, product, quantity, release_slot, due_slot, unit_price])
        oid += 1
    for _ in range(n // 3):
        product = random.choice([1, 2, 3])
        quantity = random.randint(80, 140)
        unit_price = random.choice([85.0, 90.0, 95.0])
        release_slot = random.choice([1, 2, 3, 4, 5, 6])
        due_slot = random.choice([13, 14, 15])
        rows.append([oid, product, quantity, release_slot, due_slot, unit_price])
        oid += 1
    for _ in range(n - len(rows)):
        product = random.choice([1, 2, 3])
        quantity = random.randint(60, 120)
        unit_price = random.choice([80.0, 85.0, 90.0])
        release_slot = random.choice([1, 7, 13, 19])
        due_slot = random.choice([19, 25, 31])
        rows.append([oid, product, quantity, release_slot, due_slot, unit_price])
        oid += 1
    return rows


def case_uniform_deadlines(n=30):
    rows = []
    oid = 1
    for _ in range(n):
        product = random.choice([1, 2, 3])
        quantity = random.randint(80, 160)
        unit_price = random.choice([85.0, 90.0, 95.0, 100.0])
        release_slot = random.choice([1, 2, 7, 8, 13, 14])
        due_slot = random.choice([7, 13, 19, 25, 31])
        rows.append([oid, product, quantity, release_slot, due_slot, unit_price])
        oid += 1
    return rows


def case_staggered_arrivals(n=28):
    rows = []
    oid = 1
    for _ in range(n):
        product = random.choice([1, 2, 3])
        quantity = random.randint(90, 180)
        unit_price = random.choice([90.0, 95.0, 100.0])
        release_slot = random.choice([2, 3, 4, 5, 6, 8, 9, 10])
        due_slot = random.choice([13, 14, 15, 19, 20])
        rows.append([oid, product, quantity, release_slot, due_slot, unit_price])
        oid += 1
    return rows


def case_mixed_products_tight_capacity(n=32):
    rows = []
    oid = 1
    for _ in range(n):
        product = random.choice([1, 2, 3])
        quantity = random.choice([180, 200, 220])
        unit_price = random.choice([95.0, 100.0])
        release_slot = random.choice([1, 2, 7, 8])
        due_slot = random.choice([13, 14, 15, 19])
        rows.append([oid, product, quantity, release_slot, due_slot, unit_price])
        oid += 1
    return rows


def main():
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    paths = {
        "cases_high_penalty_cluster.csv": case_high_penalty_cluster(),
        "cases_uniform_deadlines.csv": case_uniform_deadlines(),
        "cases_staggered_arrivals.csv": case_staggered_arrivals(),
        "cases_mixed_products_tight_capacity.csv": case_mixed_products_tight_capacity(),
    }
    for name, rows in paths.items():
        write_csv(os.path.join(base, name), rows)
        print(f"Wrote {name} with {len(rows)} orders")


if __name__ == "__main__":
    main()
