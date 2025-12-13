import os
import sys
import argparse
import random
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import Config
from scheduler.order_manager import OrderManager
from scheduler.rolling_scheduler import RollingScheduler

def _select_cn_font():
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "PingFang SC",
        "WenQuanYi Zen Hei",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None

_cn_font = _select_cn_font()
if _cn_font:
    plt.rcParams["font.sans-serif"] = [_cn_font]
    plt.rcParams["axes.unicode_minus"] = False

def build_config_ga():
    cfg = Config()
    cfg.LABOR_COSTS = [1000, 1000, 1000, 2000, 2000, 2000]
    cfg.POPULATION_SIZE = 30
    cfg.MAX_GENERATIONS = 50
    cfg.CROSSOVER_RATE = 0.8
    cfg.MUTATION_RATE = 0.1
    cfg.ELITE_SIZE = 3
    cfg.ENABLE_ISLAND_GA = False
    cfg.NUM_ISLANDS = 1
    cfg.ENABLE_RISK_GUIDED_LS = False
    cfg.MAX_LS_ITERATIONS = 0
    cfg.ENABLE_STOPLOSS = False
    return cfg

def build_config_ga_ils():
    cfg = build_config_ga()
    cfg.ENABLE_RISK_GUIDED_LS = False
    cfg.MAX_LS_ITERATIONS = 20
    return cfg

def build_config_island_ga():
    cfg = build_config_ga()
    cfg.ENABLE_ISLAND_GA = True
    cfg.NUM_ISLANDS = 3
    cfg.ENABLE_RISK_GUIDED_LS = False
    cfg.MAX_LS_ITERATIONS = 0
    return cfg

def build_config_island_ga_ils():
    cfg = build_config_island_ga()
    cfg.ENABLE_RISK_GUIDED_LS = True
    cfg.RISK_LS_MAX_ITER = 20
    return cfg

def run_once(cfg, csv_path, days):
    om = OrderManager()
    om.load_orders_from_csv(csv_path)
    sched = RollingScheduler(cfg, om)
    for d in range(days):
        sched.run_daily_schedule(current_day=d)
    stats = sched.get_cumulative_statistics()
    return {
        "total_revenue": stats.get("total_revenue", 0.0),
        "total_cost": stats.get("total_cost", 0.0),
        "total_penalty": stats.get("total_penalty", 0.0),
        "total_profit": stats.get("total_profit", 0.0),
        "total_orders": stats.get("total_orders", 0),
        "completed_orders": stats.get("completed_orders", 0),
        "on_time_rate": stats.get("on_time_rate", 0.0),
    }

def format_currency(x):
    return f"¥{x:,.2f}"

def build_table_df(m_ga, m_ga_ils, m_island_ga, m_island_ga_ils):
    rows = [
        ("总收入", format_currency(m_ga["total_revenue"]), format_currency(m_ga_ils["total_revenue"]), format_currency(m_island_ga["total_revenue"]), format_currency(m_island_ga_ils["total_revenue"])),
        ("总成本", format_currency(m_ga["total_cost"]), format_currency(m_ga_ils["total_cost"]), format_currency(m_island_ga["total_cost"]), format_currency(m_island_ga_ils["total_cost"])),
        ("总罚款", format_currency(m_ga["total_penalty"]), format_currency(m_ga_ils["total_penalty"]), format_currency(m_island_ga["total_penalty"]), format_currency(m_island_ga_ils["total_penalty"])),
        ("总利润", format_currency(m_ga["total_profit"]), format_currency(m_ga_ils["total_profit"]), format_currency(m_island_ga["total_profit"]), format_currency(m_island_ga_ils["total_profit"])),
        ("完成订单数", f'{m_ga["completed_orders"]}/{m_ga["total_orders"]}', f'{m_ga_ils["completed_orders"]}/{m_ga_ils["total_orders"]}', f'{m_island_ga["completed_orders"]}/{m_island_ga["total_orders"]}', f'{m_island_ga_ils["completed_orders"]}/{m_island_ga_ils["total_orders"]}'),
        ("按期率", f'{m_ga["on_time_rate"]*100:.1f}%', f'{m_ga_ils["on_time_rate"]*100:.1f}%', f'{m_island_ga["on_time_rate"]*100:.1f}%', f'{m_island_ga_ils["on_time_rate"]*100:.1f}%'),
    ]
    df = pd.DataFrame(rows, columns=["指标", "GA", "GA+ILS", "Island GA", "Island GA+ILS"])
    return df

def plot_triline_table(df, out_png):
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")
    table = ax.table(cellText=df.values, colLabels=df.columns, loc="center", cellLoc="center")
    table.scale(1, 1.4)
    for key, cell in table.get_celld().items():
        r, c = key
        cell.set_fontsize(10)
        if _cn_font:
            cell.get_text().set_fontproperties(fm.FontProperties(family=_cn_font))
        if r == 0:
            cell.set_facecolor("#f0f0f0")
    ax.plot([0.02, 0.98], [0.92, 0.92], color="black", linewidth=1.5)
    ax.plot([0.02, 0.98], [0.855, 0.855], color="black", linewidth=1.0)
    ax.plot([0.02, 0.98], [0.08, 0.08], color="black", linewidth=1.5)
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=str, required=True)
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--out", type=str, default=os.path.join("biao", "out"))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    cfg_ga = build_config_ga()
    cfg_ga_ils = build_config_ga_ils()
    cfg_island_ga = build_config_island_ga()
    cfg_island_ga_ils = build_config_island_ga_ils()
    m_ga = run_once(cfg_ga, args.csv, args.days)
    m_ga_ils = run_once(cfg_ga_ils, args.csv, args.days)
    m_island_ga = run_once(cfg_island_ga, args.csv, args.days)
    m_island_ga_ils = run_once(cfg_island_ga_ils, args.csv, args.days)
    df = build_table_df(m_ga, m_ga_ils, m_island_ga, m_island_ga_ils)
    csv_path = os.path.join(args.out, "tri_table_results.csv")
    png_path = os.path.join(args.out, "tri_table.png")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    plot_triline_table(df, png_path)
    print(csv_path)
    print(png_path)

if __name__ == "__main__":
    main()
