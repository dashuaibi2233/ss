"""
批量实验运行脚本

支持运行不同算法、不同数据集的对比实验，并保存结果。
"""
import sys
import os
import argparse
import time
import csv
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from models.order import Order
from scheduler.order_manager import OrderManager
from scheduler.rolling_scheduler import RollingScheduler
from visualization.gantt import GanttChart
from visualization.metrics import MetricsVisualizer
from ga.engine import run_ga
from ga.decoder import Decoder


def run_edd_baseline(orders, config):
    """
    运行EDD基准算法
    
    最早截止日期优先（Earliest Due Date）规则调度
    """
    print("\n" + "="*70)
    print("Running EDD Baseline Algorithm...")
    print("="*70)
    
    start_time = time.time()
    
    # 按截止日期排序订单
    sorted_orders = sorted(orders, key=lambda o: o.due_slot)
    
    # 创建简单的调度方案
    from models.schedule import Schedule
    schedule = Schedule()
    
    # 简单分配：按顺序为每个订单分配最早可用的产能
    num_lines = config.NUM_LINES
    num_slots = max(o.due_slot for o in orders) + 5
    
    # 记录每条产线每个slot的剩余产能
    available_capacity = {}
    for line in range(1, num_lines + 1):
        for slot in range(1, num_slots + 1):
            for product in [1, 2, 3]:
                available_capacity[(line, slot, product)] = config.CAPACITY.get(product, 0)
    
    # 按EDD顺序分配
    for order in sorted_orders:
        remaining = order.quantity
        product = order.product
        
        # 从slot 1开始，尽早分配
        for slot in range(1, order.due_slot + 1):
            if remaining <= 0:
                break
            
            for line in range(1, num_lines + 1):
                if remaining <= 0:
                    break
                
                avail = available_capacity.get((line, slot, product), 0)
                if avail > 0:
                    allocate = min(avail, remaining)
                    schedule.add_allocation(order.order_id, line, slot, allocate)
                    available_capacity[(line, slot, product)] -= allocate
                    remaining -= allocate
    
    # 计算指标
    schedule.calculate_metrics(orders, config.LABOR_COSTS, config.PENALTY_RATE)
    
    runtime = time.time() - start_time
    
    print(f"\nEDD Baseline completed in {runtime:.2f} seconds")
    print(f"Profit: ${schedule.profit:,.2f}")
    
    return schedule, runtime


def run_ga_only(orders, config):
    """
    运行仅GA算法（无局部搜索）
    """
    print("\n" + "="*70)
    print("Running GA Only (No Local Search)...")
    print("="*70)
    
    start_time = time.time()
    
    # 运行GA
    best_chromosome = run_ga(orders, config)
    
    # 解码为Schedule
    decoder = Decoder(config)
    schedule = decoder.decode(best_chromosome, orders)
    schedule.calculate_metrics(orders, config.LABOR_COSTS, config.PENALTY_RATE)
    
    runtime = time.time() - start_time
    
    print(f"\nGA Only completed in {runtime:.2f} seconds")
    print(f"Profit: ${schedule.profit:,.2f}")
    
    return schedule, runtime


def run_ga_ils(orders, config):
    """
    运行完整算法（GA + ILS/VNS）
    """
    print("\n" + "="*70)
    print("Running GA + ILS/VNS (Full Algorithm)...")
    print("="*70)
    
    start_time = time.time()
    
    # 运行GA
    ga_best = run_ga(orders, config)
    
    # 局部搜索改进
    from local_search.ils_vns import improve_solution
    improved = improve_solution(ga_best, orders, config)
    
    # 解码为Schedule
    decoder = Decoder(config)
    schedule = decoder.decode(improved, orders)
    schedule.calculate_metrics(orders, config.LABOR_COSTS, config.PENALTY_RATE)
    
    runtime = time.time() - start_time
    
    print(f"\nGA + ILS/VNS completed in {runtime:.2f} seconds")
    print(f"Profit: ${schedule.profit:,.2f}")
    
    return schedule, runtime


def save_metrics_to_csv(schedule, orders, runtime, filepath):
    """
    保存指标到CSV文件
    """
    stats = schedule.get_statistics(orders)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['total_profit', f'{schedule.profit:.2f}'])
        writer.writerow(['total_revenue', f'{schedule.revenue:.2f}'])
        writer.writerow(['total_cost', f'{schedule.cost:.2f}'])
        writer.writerow(['total_penalty', f'{schedule.penalty:.2f}'])
        writer.writerow(['on_time_rate', f'{stats["on_time_rate"]:.4f}'])
        writer.writerow(['avg_completion_rate', f'{stats["avg_completion_rate"]:.4f}'])
        writer.writerow(['total_orders', stats['total_orders']])
        writer.writerow(['completed_orders', stats['completed_orders']])
        writer.writerow(['working_slots', stats['total_working_slots']])
        writer.writerow(['runtime_seconds', f'{runtime:.2f}'])
    
    print(f"Metrics saved to {filepath}")


def run_single_experiment(args):
    """
    运行单个实验
    """
    # 加载配置
    config = Config()
    
    # 应用自定义参数
    if args.population:
        config.POPULATION_SIZE = args.population
    if args.generations:
        config.MAX_GENERATIONS = args.generations
    if args.crossover:
        config.CROSSOVER_RATE = args.crossover
    if args.mutation:
        config.MUTATION_RATE = args.mutation
    if args.ls_iterations:
        config.MAX_LS_ITERATIONS = args.ls_iterations
    
    # 设置产能
    config.CAPACITY = {1: 50, 2: 60, 3: 55}
    labor_costs_per_day = [100, 100, 100, 150, 150, 150]
    config.LABOR_COSTS = labor_costs_per_day * 10
    
    # 加载订单数据
    order_manager = OrderManager()
    
    if args.data == 'small':
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_orders_small.csv')
    elif args.data == 'medium':
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_orders_medium.csv')
    else:
        csv_path = args.data
    
    order_manager.load_orders_from_csv(csv_path)
    orders = order_manager.get_all_orders()
    
    print(f"\nLoaded {len(orders)} orders from {args.data}")
    
    # 运行算法
    if args.algorithm == 'edd':
        schedule, runtime = run_edd_baseline(orders, config)
    elif args.algorithm == 'ga_only':
        schedule, runtime = run_ga_only(orders, config)
    elif args.algorithm == 'ga_ils':
        schedule, runtime = run_ga_ils(orders, config)
    else:
        raise ValueError(f"Unknown algorithm: {args.algorithm}")
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 保存结果
    base_name = f"{args.algorithm}_{args.data}"
    
    if args.save_metrics:
        metrics_path = os.path.join(args.output_dir, f"metrics_{base_name}.csv")
        save_metrics_to_csv(schedule, orders, runtime, metrics_path)
    
    if args.save_charts:
        # 保存甘特图
        gantt = GanttChart()
        gantt_path = os.path.join(args.output_dir, f"gantt_{base_name}.png")
        gantt.plot_schedule(schedule, orders, output_path=gantt_path)
        
        # 保存指标图表
        metrics_viz = MetricsVisualizer()
        profit_path = os.path.join(args.output_dir, f"profit_{base_name}.png")
        metrics_viz.plot_profit_breakdown(schedule, output_path=profit_path)
        
        completion_path = os.path.join(args.output_dir, f"completion_{base_name}.png")
        metrics_viz.plot_order_completion_rate(orders, schedule, output_path=completion_path)
        
        utilization_path = os.path.join(args.output_dir, f"utilization_{base_name}.png")
        metrics_viz.plot_line_utilization(schedule, output_path=utilization_path)
    
    return schedule, runtime


def run_comparison_mode(args):
    """
    运行对比模式：比较所有算法
    """
    print("\n" + "="*70)
    print("COMPARISON MODE: Running all algorithms...")
    print("="*70)
    
    algorithms = ['edd', 'ga_only', 'ga_ils']
    results = {}
    
    for algo in algorithms:
        args.algorithm = algo
        schedule, runtime = run_single_experiment(args)
        results[algo] = (schedule, runtime)
    
    # 生成对比报告
    generate_comparison_report(results, args)


def generate_comparison_report(results, args):
    """
    生成对比报告
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(args.output_dir, f"comparison_report_{timestamp}.txt")
    
    # 加载订单以获取统计
    order_manager = OrderManager()
    if args.data == 'small':
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_orders_small.csv')
    else:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_orders_medium.csv')
    order_manager.load_orders_from_csv(csv_path)
    orders = order_manager.get_all_orders()
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("ALGORITHM COMPARISON REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Dataset: {args.data} ({len(orders)} orders)\n")
        f.write("="*70 + "\n\n")
        
        # 财务指标
        f.write("FINANCIAL METRICS:\n")
        f.write("-"*70 + "\n")
        f.write(f"{'Algorithm':<15} {'Profit':>12} {'Revenue':>12} {'Cost':>12} {'Penalty':>12}\n")
        f.write("-"*70 + "\n")
        
        for algo, (schedule, runtime) in results.items():
            f.write(f"{algo.upper():<15} "
                   f"{schedule.profit:>12,.2f} "
                   f"{schedule.revenue:>12,.2f} "
                   f"{schedule.cost:>12,.2f} "
                   f"{schedule.penalty:>12,.2f}\n")
        f.write("-"*70 + "\n\n")
        
        # 性能指标
        f.write("PERFORMANCE METRICS:\n")
        f.write("-"*70 + "\n")
        f.write(f"{'Algorithm':<15} {'On-time Rate':>15} {'Completion':>15} {'Runtime(s)':>12}\n")
        f.write("-"*70 + "\n")
        
        for algo, (schedule, runtime) in results.items():
            stats = schedule.get_statistics(orders)
            f.write(f"{algo.upper():<15} "
                   f"{stats['on_time_rate']*100:>14.1f}% "
                   f"{stats['avg_completion_rate']*100:>14.1f}% "
                   f"{runtime:>12.2f}\n")
        f.write("-"*70 + "\n\n")
        
        # 改进分析
        if 'edd' in results and 'ga_ils' in results:
            f.write("IMPROVEMENT ANALYSIS:\n")
            f.write("-"*70 + "\n")
            
            edd_profit = results['edd'][0].profit
            edd_stats = results['edd'][0].get_statistics(orders)
            
            if 'ga_only' in results:
                ga_only_profit = results['ga_only'][0].profit
                ga_only_stats = results['ga_only'][0].get_statistics(orders)
                profit_imp = (ga_only_profit - edd_profit) / edd_profit * 100
                rate_imp = (ga_only_stats['on_time_rate'] - edd_stats['on_time_rate']) * 100
                f.write(f"GA_ONLY vs EDD:     +{profit_imp:.1f}% profit, +{rate_imp:.1f}% on-time rate\n")
            
            ga_ils_profit = results['ga_ils'][0].profit
            ga_ils_stats = results['ga_ils'][0].get_statistics(orders)
            profit_imp = (ga_ils_profit - edd_profit) / edd_profit * 100
            rate_imp = (ga_ils_stats['on_time_rate'] - edd_stats['on_time_rate']) * 100
            f.write(f"GA_ILS vs EDD:      +{profit_imp:.1f}% profit, +{rate_imp:.1f}% on-time rate\n")
            
            if 'ga_only' in results:
                profit_imp = (ga_ils_profit - ga_only_profit) / ga_only_profit * 100
                rate_imp = (ga_ils_stats['on_time_rate'] - ga_only_stats['on_time_rate']) * 100
                f.write(f"GA_ILS vs GA_ONLY:  +{profit_imp:.1f}% profit, +{rate_imp:.1f}% on-time rate\n")
            
            f.write("-"*70 + "\n")
    
    print(f"\nComparison report saved to {report_path}")


def main():
    parser = argparse.ArgumentParser(description='Run scheduling experiments')
    
    # 基本参数
    parser.add_argument('--data', type=str, default='small',
                       help='Dataset: small, medium, or custom path')
    parser.add_argument('--algorithm', type=str, default='ga_ils',
                       choices=['edd', 'ga_only', 'ga_ils'],
                       help='Algorithm to run')
    parser.add_argument('--mode', type=str, default='single',
                       choices=['single', 'comparison', 'sensitivity', 'report'],
                       help='Running mode')
    
    # GA参数
    parser.add_argument('--population', type=int, default=None,
                       help='Population size')
    parser.add_argument('--generations', type=int, default=None,
                       help='Max generations')
    parser.add_argument('--crossover', type=float, default=None,
                       help='Crossover rate')
    parser.add_argument('--mutation', type=float, default=None,
                       help='Mutation rate')
    parser.add_argument('--ls_iterations', type=int, default=None,
                       help='Local search iterations')
    
    # 输出参数
    parser.add_argument('--output_dir', type=str, default='results',
                       help='Output directory')
    parser.add_argument('--save_metrics', action='store_true', default=True,
                       help='Save metrics to CSV')
    parser.add_argument('--save_charts', action='store_true', default=True,
                       help='Save charts')
    
    args = parser.parse_args()
    
    print("="*70)
    print("SCHEDULING EXPERIMENTS")
    print("="*70)
    print(f"Mode: {args.mode}")
    print(f"Dataset: {args.data}")
    print(f"Algorithm: {args.algorithm}")
    print("="*70)
    
    if args.mode == 'single':
        run_single_experiment(args)
    elif args.mode == 'comparison':
        run_comparison_mode(args)
    elif args.mode == 'report':
        print("Report mode: Generate report from existing results")
        # TODO: Implement report generation from existing results
    else:
        print(f"Mode {args.mode} not yet implemented")
    
    print("\n" + "="*70)
    print("EXPERIMENTS COMPLETED!")
    print("="*70)
    print(f"\nResults saved to: {args.output_dir}/")
    print("\nCheck the output directory for:")
    print("  - metrics_*.csv (numerical results)")
    print("  - gantt_*.png (Gantt charts)")
    print("  - profit_*.png (profit breakdown)")
    print("  - comparison_report_*.txt (comparison analysis)")


if __name__ == "__main__":
    main()
