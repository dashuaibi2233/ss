import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from config import Config
from scheduler.order_manager import OrderManager
from ga.engine import run_ga
from local_search.ils_vns import improve_solution
from ga.decoder import Decoder


def _to_bool_env(val, default=True):
    if val is None:
        return default
    s = str(val).strip().lower()
    return s in ("1", "true", "yes", "y", "on")


def load_orders(csv_path):
    om = OrderManager()
    adjust_env = os.environ.get("MIN_COMPARE_ADJUST", None)
    adjust = _to_bool_env(adjust_env, default=True)
    om.load_orders_from_csv(csv_path, adjust_due_slot=adjust, verbose=False)
    return om


def run_once(orders, config, planning_horizon, start_slot):
    ga_best = run_ga(orders, config, planning_horizon=planning_horizon, start_slot=start_slot)
    improved = improve_solution(ga_best, orders, config, start_slot=start_slot)
    decoder = Decoder(config)
    schedule = decoder.decode(improved, orders, start_slot=start_slot)
    schedule.calculate_metrics(orders, config.LABOR_COSTS, config.PENALTY_RATE)
    return schedule


def format_stats(schedule, orders):
    stats = schedule.get_statistics(orders)
    return {
        "profit": schedule.profit,
        "revenue": schedule.revenue,
        "cost": schedule.cost,
        "penalty": schedule.penalty,
        "on_time_rate": stats["on_time_rate"],
        "avg_completion_rate": stats["avg_completion_rate"],
    }


def main():
    csv_default = os.path.join(os.path.dirname(__file__), "..", "data", "sample_orders_small.csv")
    csv_path = os.environ.get("MIN_COMPARE_CSV", csv_default)

    om = load_orders(csv_path)
    orders = om.get_all_orders()

    cfg_old = Config()
    cfg_old.ENABLE_ISLAND_GA = False
    cfg_old.NUM_ISLANDS = 1
    cfg_old.ENABLE_RISK_GUIDED_LS = False

    cfg_new = Config()
    cfg_new.ENABLE_ISLAND_GA = True
    cfg_new.NUM_ISLANDS = 3
    cfg_new.ISLAND_MIGRATION_INTERVAL = 20
    cfg_new.ISLAND_MIGRATION_ELITE_COUNT = 2
    cfg_new.ENABLE_RISK_GUIDED_LS = True
    cfg_new.ANNEALING_INIT_ACCEPT_PROB = 0.3
    cfg_new.ANNEALING_DECAY_RATE = 0.95
    cfg_new.ANNEALING_MIN_ACCEPT_PROB = 0.01

    start_slot = om.time_to_slot(day=0, hour=8)
    planning_horizon = cfg_old.SLOTS_PER_DAY * 10

    t0 = time.time()
    sch_old = run_once(orders, cfg_old, planning_horizon, start_slot)
    t1 = time.time()
    sch_new = run_once(orders, cfg_new, planning_horizon, start_slot)
    t2 = time.time()

    s_old = format_stats(sch_old, orders)
    s_new = format_stats(sch_new, orders)

    print("\n" + "=" * 70)
    print("MIN COMPARISON: OLD VS NEW")
    print("=" * 70)
    print(f"Dataset: {os.path.basename(csv_path)} ({len(orders)} orders)")
    print(f"Window: start_slot={start_slot}, horizon={planning_horizon}")
    print("-" * 70)
    print(f"OLD  Profit: {s_old['profit']:.2f}  Revenue: {s_old['revenue']:.2f}  Cost: {s_old['cost']:.2f}  Penalty: {s_old['penalty']:.2f}")
    print(f"OLD  On-time: {s_old['on_time_rate']*100:.1f}%  AvgCompletion: {s_old['avg_completion_rate']*100:.1f}%  Runtime: {t1-t0:.2f}s")
    print("-" * 70)
    print(f"NEW  Profit: {s_new['profit']:.2f}  Revenue: {s_new['revenue']:.2f}  Cost: {s_new['cost']:.2f}  Penalty: {s_new['penalty']:.2f}")
    print(f"NEW  On-time: {s_new['on_time_rate']*100:.1f}%  AvgCompletion: {s_new['avg_completion_rate']*100:.1f}%  Runtime: {t2-t1:.2f}s")
    print("-" * 70)
    delta_profit = s_new["profit"] - s_old["profit"]
    delta_penalty = s_new["penalty"] - s_old["penalty"]
    delta_cost = s_new["cost"] - s_old["cost"]
    print(f"Δ Profit: {delta_profit:+.2f}  Δ Penalty: {delta_penalty:+.2f}  Δ Cost: {delta_cost:+.2f}")
    print("=" * 70 + "\n")

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "output"), exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(os.path.dirname(__file__), "..", "output", f"min_compare_{ts}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Dataset: {os.path.basename(csv_path)} ({len(orders)} orders)\n")
        f.write(f"Window: start_slot={start_slot}, horizon={planning_horizon}\n")
        f.write("OLD:\n")
        f.write(f"  Profit={s_old['profit']:.2f} Revenue={s_old['revenue']:.2f} Cost={s_old['cost']:.2f} Penalty={s_old['penalty']:.2f}\n")
        f.write(f"  OnTime={s_old['on_time_rate']:.4f} AvgCompletion={s_old['avg_completion_rate']:.4f} Runtime={t1-t0:.2f}s\n")
        f.write("NEW:\n")
        f.write(f"  Profit={s_new['profit']:.2f} Revenue={s_new['revenue']:.2f} Cost={s_new['cost']:.2f} Penalty={s_new['penalty']:.2f}\n")
        f.write(f"  OnTime={s_new['on_time_rate']:.4f} AvgCompletion={s_new['avg_completion_rate']:.4f} Runtime={t2-t1:.2f}s\n")
        f.write(f"Delta: Profit={delta_profit:+.2f} Penalty={delta_penalty:+.2f} Cost={delta_cost:+.2f}\n")


if __name__ == "__main__":
    main()
