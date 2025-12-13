import os
import sys
import argparse
import random
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import Config
from scheduler.order_manager import OrderManager
from ga.engine import GAEngine
from ga.island_engine import IslandGAEngine
from ga.decoder import Decoder
from local_search.ils_vns import improve_solution

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def load_orders(path):
    om = OrderManager()
    om.load_orders_from_csv(path)
    return om

def build_cfg(islands):
    cfg = Config()
    cfg.ENABLE_ISLAND_GA = islands > 1
    cfg.NUM_ISLANDS = islands if islands > 1 else 1
    cfg.ENABLE_RISK_GUIDED_LS = False
    return cfg

def run_single_ga(orders, cfg, days, start_slot=1):
    engine = GAEngine(cfg, orders, planning_horizon=cfg.SLOTS_PER_DAY*days, start_slot=start_slot)
    engine.initialize_population()
    best = engine.evolve()
    history = engine.get_fitness_history()
    return best, history

def run_island_ga(orders, cfg, days, start_slot=1):
    engine = IslandGAEngine(cfg, orders, planning_horizon=cfg.SLOTS_PER_DAY*days, start_slot=start_slot)
    engine.initialize_islands()
    best = engine.evolve()
    history = engine.get_global_best_history()
    return best, history

def plot_convergence(single_hist, island_hist, out_path):
    plt.style.use('seaborn-whitegrid')
    plt.figure(figsize=(7,4))
    if single_hist:
        plt.plot(range(1, len(single_hist)+1), single_hist, label='Single GA', linewidth=2)
    if island_hist:
        plt.plot(range(1, len(island_hist)+1), island_hist, label='Island GA', linewidth=2)
    plt.xlabel('Generation')
    plt.ylabel('Best Fitness')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

def compare_algorithms(orders, cfg, days, start_slot, runs, out_dir, basename):
    def eval_schedule(ch):
        dec = Decoder(cfg)
        sch = dec.decode(ch, orders, start_slot=start_slot)
        sch.calculate_metrics(orders, cfg.LABOR_COSTS, cfg.PENALTY_RATE)
        return sch
    results = {'ga_only':[], 'ga_ils':[], 'island_ga_only':[], 'island_ga_ils':[]}
    for _ in range(runs):
        cfg.ENABLE_ISLAND_GA = False
        cfg.NUM_ISLANDS = 1
        best, _ = run_single_ga(orders, cfg, days, start_slot)
        sch = eval_schedule(best)
        results['ga_only'].append(sch.profit)
        imp = improve_solution(best, orders, cfg, start_slot=start_slot)
        sch2 = eval_schedule(imp)
        results['ga_ils'].append(sch2.profit)
        cfg.ENABLE_ISLAND_GA = True
        cfg.NUM_ISLANDS = 3
        best_i, _ = run_island_ga(orders, cfg, days, start_slot)
        schi = eval_schedule(best_i)
        results['island_ga_only'].append(schi.profit)
        impi = improve_solution(best_i, orders, cfg, start_slot=start_slot)
        schi2 = eval_schedule(impi)
        results['island_ga_ils'].append(schi2.profit)
    labels = ['GA', 'GA+ILS', 'Island GA', 'Island GA+ILS']
    data = [results['ga_only'], results['ga_ils'], results['island_ga_only'], results['island_ga_ils']]
    plt.style.use('seaborn-whitegrid')
    plt.figure(figsize=(7,4))
    bp = plt.boxplot(data, labels=labels, showmeans=True, notch=False)
    plt.ylabel('Profit')
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f'profit_box_{basename}.png'))
    plt.close()
    plt.figure(figsize=(7,4))
    means = [sum(d)/len(d) if d else 0 for d in data]
    bars = plt.bar(labels, means, color=['#4C78A8','#F58518','#54A24B','#E45756'])
    plt.ylabel('Profit (mean)')
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
    # 设置非零起点，突出差异
    if any(means):
        min_mean = min(means)
        max_mean = max(means)
        margin = max((max_mean - min_mean) * 0.15, 500.0)
        ax.set_ylim(min_mean - margin, max_mean + margin)
    for bar, val in zip(bars, means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val:,.0f}', ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f'profit_bar_{basename}.png'))
    plt.close()
    with open(os.path.join(out_dir, f'summary_{basename}.json'), 'w', encoding='utf-8') as f:
        json.dump({'means':dict(zip(labels, means)), 'runs':runs}, f, ensure_ascii=False, indent=2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', type=str, required=True)
    ap.add_argument('--days', type=int, default=6)
    ap.add_argument('--outdir', type=str, default=os.path.join('exp','output'))
    ap.add_argument('--runs', type=int, default=10)
    args = ap.parse_args()
    ensure_dir(args.outdir)
    om = load_orders(args.data)
    orders = om.get_all_orders()
    cfg = build_cfg(3)
    start_slot = om.time_to_slot(day=0, hour=8)
    best_s, hist_s = run_single_ga(orders, cfg, args.days, start_slot)
    best_i, hist_i = run_island_ga(orders, cfg, args.days, start_slot)
    base = os.path.splitext(os.path.basename(args.data))[0]
    plot_convergence(hist_s, hist_i, os.path.join(args.outdir, f'convergence_{base}.png'))
    compare_algorithms(orders, cfg, args.days, start_slot, args.runs, args.outdir, base)
    print('OK research plots ->', args.outdir)

if __name__ == '__main__':
    main()


#python exp\research_plots.py --data "C:\Users\Yuban\Desktop\computer_agent\smart-scheduling\data\custom6_case.csv" --days 6 --runs 8 --outdir exp\output
#exp\research_plots.py --data "C:\Users\Yuban\Desktop\computer_agent\smart-scheduling\data\delay_full.csv" --days 5 --runs 8 --outdir exp\output
