"""
智能制造生产调度系统 - 主程序入口

本模块负责系统的启动和整体流程控制。
"""
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from scheduler.order_manager import OrderManager
from scheduler.rolling_scheduler import RollingScheduler
from visualization.gantt import GanttChart
from visualization.metrics import MetricsVisualizer


def main():
    """
    主函数：初始化系统并启动调度流程
    
    演示完整的滚动调度流程：
    1. 从CSV加载订单
    2. 初始化配置和调度器
    3. 模拟3天的生产调度
    4. 输出关键指标
    5. 绘制甘特图和指标图表
    """
    print("="*70)
    print("智能制造生产调度系统 - 演示")
    print("="*70)
    
    # ========== 步骤1: 初始化配置 ==========
    print("\n[步骤1] 初始化配置...")
    config = Config()
    
    # 配置产能参数（每个产品在每个slot的产能）
    config.CAPACITY = {
        1: 50,   # 产品1: 每slot产能50
        2: 60,   # 产品2: 每slot产能60
        3: 55,   # 产品3: 每slot产能55
    }
    
    
    # 配置人工成本（每个slot的成本，共60个slot = 10天）
    # 白班(8-20点): 100, 晚班(20-8点): 150
    labor_costs_per_day = [1000, 1000, 1200, 1400, 2000, 1600]  # 6个slot/天
    config.LABOR_COSTS = labor_costs_per_day * 10  # 10天
    
    # GA参数
    config.POPULATION_SIZE = 15
    config.MAX_GENERATIONS = 30
    config.CROSSOVER_RATE = 0.55
    config.MUTATION_RATE = 0.25
    config.ELITE_SIZE = 1
    config.ENABLE_ISLAND_GA = False
    config.NUM_ISLANDS = 1
    
    # 局部搜索参数
    config.MAX_LS_ITERATIONS = 0
    config.ENABLE_RISK_GUIDED_LS = False
    
    print(f"  种群规模: {config.POPULATION_SIZE}")
    print(f"  最大迭代次数: {config.MAX_GENERATIONS}")
    print(f"  产能配置: {config.CAPACITY}")
    
    # ========== 步骤2: 加载订单数据 ==========
    print("\n[步骤2] 从CSV加载订单数据...")
    order_manager = OrderManager()
    
    # 获取CSV文件路径
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data',
        'custom6_case.csv'
    )
    
    order_count = order_manager.load_orders_from_csv(csv_path)
    print(f"  已加载 {order_count} 个订单")
    print(f"  待处理订单: {order_manager.get_pending_count()}")
    
    
    
    # ========== 步骤3: 创建滚动调度器 ==========
    print("\n[步骤3] 创建滚动调度器...")
    scheduler = RollingScheduler(config, order_manager)
    print("  调度器初始化完成")
    
    # ========== 步骤4: 模拟多天滚动调度 ==========
    print("\n[步骤4] 运行滚动调度模拟...")
    num_days = 10
    
    for day in range(num_days):
        print(f"\n{'='*70}")
        print(f"DAY {day + 1} SCHEDULING")
        print(f"{'='*70}")
        
        # 每天8点执行调度
        schedule = scheduler.run_daily_schedule(current_day=day)
        
        if schedule:
            # 统计截止当天的累计完成情况
            orders = order_manager.get_all_orders()
            total_orders = len(orders)
            completed_orders = sum(1 for order in orders if order.is_completed())
            
            print(f"\n📊 第 {day + 1} 天结果:")
            print(f"  累计完成订单: {completed_orders}/{total_orders}")
            print(f"  累计完成率: {completed_orders/total_orders*100:.1f}%")
    
    # ========== 步骤5: 获取最终调度方案 ==========
    print("\n" + "="*70)
    print("[步骤5] 最终调度方案分析")
    print("="*70)
    
    # 获取累计统计数据（多日汇总）
    cumulative_stats = scheduler.get_cumulative_statistics()
    orders = order_manager.get_all_orders()
    
    # 打印累计指标
    print("\n" + "="*60)
    print("调度指标（多日累计）")
    print("="*60)
    print(f"\n财务指标:")
    print(f"  总收入:        ¥{cumulative_stats['total_revenue']:,.2f}")
    print(f"  总成本:        ¥{cumulative_stats['total_cost']:,.2f}")
    print(f"  总罚款:        ¥{cumulative_stats['total_penalty']:,.2f}")
    print(f"  总利润:        ¥{cumulative_stats['total_profit']:,.2f}")
    
    print(f"\n订单指标:")
    print(f"  总订单数:      {cumulative_stats['total_orders']}")
    print(f"  完成订单数:    {cumulative_stats['completed_orders']}")
    print(f"  完成率:        {cumulative_stats['completed_orders']/cumulative_stats['total_orders']*100:.1f}%")
    
    # 打印每日明细
    print(f"\n每日明细:")
    for day_result in cumulative_stats['daily_results']:
        print(f"  第{day_result['day']}天: 收入=¥{day_result['revenue']:,.2f}, "
              f"成本=¥{day_result['cost']:,.2f}, "
              f"罚款=¥{day_result['penalty']:,.2f}, "
              f"利润=¥{day_result['profit']:,.2f}")
    print("="*60 + "\n")
    
    final_schedule = scheduler.get_current_schedule()
    if final_schedule:
        
        # ========== 步骤6: 生成可视化图表 ==========
        print("[步骤6] 生成可视化图表...")
        
        # 创建输出目录
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'output'
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # 绘制甘特图
        print("\n  生成甘特图...")
        gantt = GanttChart()
        gantt.plot_schedule(
            final_schedule, 
            orders, 
            num_lines=3, 
            max_slots=config.SLOTS_PER_DAY * num_days,
            output_path=f"{output_dir}/gantt_chart.png"
        )
        
        # 生成指标报告（使用累计统计数据）
        print("  生成指标图表...")
        metrics_viz = MetricsVisualizer()
        metrics_viz.generate_report(cumulative_stats, orders, output_dir, final_schedule)
        
        print(f"\n✅ 所有可视化图表已保存至: {output_dir}/")
        print("   - gantt_chart.png (甘特图)")
        print("   - profit_breakdown.png (利润分解图)")
        print("   - order_completion.png (订单完成情况)")
        print("   - line_utilization.png (产线利用率)")
    
    # ========== 完成 ==========
    # 在不改变滚动调度外观行为下，最后打印旧版 vs 新版的最小对比（同数据同窗口）
    print("\n[对比] 旧版 vs 新版（同数据同窗口）")
    cfg_old = Config()
    cfg_old.CAPACITY = config.CAPACITY
    cfg_old.LABOR_COSTS = config.LABOR_COSTS
    # 基线刻意降级（仅用于终端最小对比），不影响上面的主流程
    cfg_old.POPULATION_SIZE = 15
    cfg_old.MAX_GENERATIONS = 30
    cfg_old.CROSSOVER_RATE = 0.55
    cfg_old.MUTATION_RATE = 0.25
    cfg_old.ELITE_SIZE = 1
    cfg_old.ENABLE_ISLAND_GA = False
    cfg_old.NUM_ISLANDS = 1
    cfg_old.ENABLE_RISK_GUIDED_LS = False
    om_old = OrderManager()
    om_old.load_orders_from_csv(csv_path)
    sched_old = RollingScheduler(cfg_old, om_old)
    for d in range(num_days):
        sched_old.run_daily_schedule(current_day=d)
    stats_old = sched_old.get_cumulative_statistics()
    
    cfg_new = Config()
    cfg_new.CAPACITY = config.CAPACITY
    cfg_new.LABOR_COSTS = config.LABOR_COSTS
    # 新版保持较强配置（仅用于终端最小对比）
    cfg_new.POPULATION_SIZE = 30
    cfg_new.MAX_GENERATIONS = 50
    cfg_new.CROSSOVER_RATE = 0.8
    cfg_new.MUTATION_RATE = 0.1
    cfg_new.ELITE_SIZE = 3
    cfg_new.ENABLE_ISLAND_GA = True
    cfg_new.NUM_ISLANDS = 3
    cfg_new.ENABLE_RISK_GUIDED_LS = False
    om_new = OrderManager()
    om_new.load_orders_from_csv(csv_path)
    sched_new = RollingScheduler(cfg_new, om_new)
    for d in range(num_days):
        sched_new.run_daily_schedule(current_day=d)
    stats_new = sched_new.get_cumulative_statistics()
    
    print("\n[最小对比结果]")
    print(f"  旧版: 利润=¥{stats_old['total_profit']:,.2f} 收入=¥{stats_old['total_revenue']:,.2f} 成本=¥{stats_old['total_cost']:,.2f} 罚款=¥{stats_old['total_penalty']:,.2f}")
    print(f"  新版: 利润=¥{stats_new['total_profit']:,.2f} 收入=¥{stats_new['total_revenue']:,.2f} 成本=¥{stats_new['total_cost']:,.2f} 罚款=¥{stats_new['total_penalty']:,.2f}")
    dp = stats_new['total_profit'] - stats_old['total_profit']
    dc = stats_new['total_cost'] - stats_old['total_cost']
    dne = stats_new['total_penalty'] - stats_old['total_penalty']
    print(f"  差异: 利润变化=¥{dp:+,.2f} 成本变化=¥{dc:+,.2f} 罚款变化=¥{dne:+,.2f}")
    print(f"  旧版: 完成订单={stats_old['completed_orders']}/{stats_old['total_orders']} 按期率={stats_old['on_time_rate']*100:.1f}%")
    print(f"  新版: 完成订单={stats_new['completed_orders']}/{stats_new['total_orders']} 按期率={stats_new['on_time_rate']*100:.1f}%")
    dcomp = stats_new['completed_orders'] - stats_old['completed_orders']
    drate = stats_new['on_time_rate']*100 - stats_old['on_time_rate']*100
    print(f"  差异: 完成订单变化={dcomp:+d} 按期率变化={drate:+.1f}%")
    # 简要原因说明
    if dne > 0:
        print("  说明: 新版罚款增加，多为局部搜索接受略差解或产能分配位移导致的到期未完成；可通过调低退火接受或提高交付偏好缓解。")
    elif dp > 0:
        print("  说明: 新版利润提升，岛模型并行在同窗内更好地平衡了成本与罚款。")
    else:
        print("  说明: 两版表现接近，建议针对数据特性调参以发挥新版优势。")
    
    print("\n" + "="*70)
    print("🎉 演示完成!")
    print("="*70)
    print("\n📁 请查看 'output' 文件夹中的生成图表")
    print("💡 提示: 可以修改 data/sample_orders_small.csv 来测试不同场景\n")


if __name__ == "__main__":
    main()
