import os
import sys
import argparse
import time
import csv
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import Config
from scheduler.order_manager import OrderManager
from ga.engine import run_ga
from local_search.ils_vns import improve_solution
from ga.decoder import Decoder
from visualization.gantt import GanttChart
from visualization.metrics import MetricsVisualizer

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def load_orders_by_arg(arg):
    om = OrderManager()
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if arg == 'small':
        csv_path = os.path.abspath(os.path.join(base, 'data', 'sample_orders_small.csv'))
    elif arg == 'medium':
        csv_path = os.path.abspath(os.path.join(base, 'data', 'sample_orders_medium.csv'))
    else:
        csv_path = os.path.abspath(arg)
    om.load_orders_from_csv(csv_path)
    return om, csv_path

def run_ga_only(orders, config, planning_horizon=None, start_slot=1):
    t0 = time.time()
    best = run_ga(orders, config, planning_horizon=planning_horizon, start_slot=start_slot)
    dec = Decoder(config)
    sch = dec.decode(best, orders, start_slot=start_slot)
    sch.calculate_metrics(orders, config.LABOR_COSTS, config.PENALTY_RATE)
    return sch, time.time() - t0

def run_ga_ils(orders, config, planning_horizon=None, start_slot=1):
    t0 = time.time()
    best = run_ga(orders, config, planning_horizon=planning_horizon, start_slot=start_slot)
    imp = improve_solution(best, orders, config, start_slot=start_slot)
    dec = Decoder(config)
    sch = dec.decode(imp, orders, start_slot=start_slot)
    sch.calculate_metrics(orders, config.LABOR_COSTS, config.PENALTY_RATE)
    return sch, time.time() - t0

def save_metrics(schedule, orders, runtime, out_csv):
    stats = schedule.get_statistics(orders)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'value'])
        w.writerow(['total_profit', f'{schedule.profit:.2f}'])
        w.writerow(['total_revenue', f'{schedule.revenue:.2f}'])
        w.writerow(['total_cost', f'{schedule.cost:.2f}'])
        w.writerow(['total_penalty', f'{schedule.penalty:.2f}'])
        w.writerow(['on_time_rate', f'{stats["on_time_rate"]:.4f}'])
        w.writerow(['avg_completion_rate', f'{stats["avg_completion_rate"]:.4f}'])
        w.writerow(['total_orders', stats['total_orders']])
        w.writerow(['completed_orders', stats['completed_orders']])
        w.writerow(['working_slots', stats['total_working_slots']])
        w.writerow(['runtime_seconds', f'{runtime:.2f}'])

def plot_all(schedule, orders, out_dir, base_name):
    ensure_dir(out_dir)
    gantt = GanttChart()
    gantt.plot_schedule(schedule, orders, output_path=os.path.join(out_dir, f"gantt_{base_name}.png"))
    mv = MetricsVisualizer()
    mv.plot_profit_breakdown(schedule, output_path=os.path.join(out_dir, f"profit_{base_name}.png"))
    mv.plot_order_completion_rate(orders, schedule, output_path=os.path.join(out_dir, f"completion_{base_name}.png"))
    mv.plot_line_utilization(schedule, output_path=os.path.join(out_dir, f"utilization_{base_name}.png"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', type=str, default='small')
    ap.add_argument('--days', type=int, default=6)
    ap.add_argument('--islands', type=int, default=3)
    ap.add_argument('--enable_ils', action='store_true', default=False)
    ap.add_argument('--output_dir', type=str, default=os.path.join('exp', 'output'))
    args = ap.parse_args()
    ensure_dir(args.output_dir)

    om, csv_path = load_orders_by_arg(args.data)
    orders = om.get_all_orders()
    cfg = Config()
    cfg.CAPACITY = cfg.CAPACITY
    cfg.LABOR_COSTS = cfg.LABOR_COSTS
    cfg.POPULATION_SIZE = cfg.POPULATION_SIZE
    cfg.MAX_GENERATIONS = cfg.MAX_GENERATIONS
    cfg.CROSSOVER_RATE = cfg.CROSSOVER_RATE
    cfg.MUTATION_RATE = cfg.MUTATION_RATE
    cfg.ELITE_SIZE = cfg.ELITE_SIZE
    cfg.ENABLE_ISLAND_GA = args.islands > 1
    cfg.NUM_ISLANDS = args.islands if args.islands > 1 else 1
    cfg.ENABLE_RISK_GUIDED_LS = False

    start_slot = om.time_to_slot(day=0, hour=8)
    planning_horizon = cfg.SLOTS_PER_DAY * args.days

    if args.enable_ils:
        sch, rt = run_ga_ils(orders, cfg, planning_horizon=planning_horizon, start_slot=start_slot)
        tag = f"ga_ils_islands{cfg.NUM_ISLANDS}_{os.path.basename(csv_path).split('.')[0]}"
    else:
        sch, rt = run_ga_only(orders, cfg, planning_horizon=planning_horizon, start_slot=start_slot)
        tag = f"ga_only_islands{cfg.NUM_ISLANDS}_{os.path.basename(csv_path).split('.')[0]}"

    save_metrics(sch, orders, rt, os.path.join(args.output_dir, f"metrics_{tag}.csv"))
    plot_all(sch, orders, args.output_dir, tag)
    print(f"OK: {tag} -> {args.output_dir}")

if __name__ == '__main__':
    main()
