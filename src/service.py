"""
服务层模块 - 为GUI提供调用接口

本模块封装核心调度逻辑，供GUI层调用，保持核心算法不变。
"""
import os
import sys
from typing import Tuple, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from scheduler.order_manager import OrderManager
from scheduler.rolling_scheduler import RollingScheduler
from models.simulation_result import SimulationResult, DayResult


def load_default_config() -> Config:
    """
    加载默认配置
    
    Returns:
        Config: 配置对象
    """
    config = Config()
    
    # 配置产能参数（每个产品在每个slot的产能）
    config.CAPACITY = {
        1: 50,   # 产品1: 每slot产能50
        2: 60,   # 产品2: 每slot产能60
        3: 55,   # 产品3: 每slot产能55
    }
    
    # 配置人工成本（每个slot的成本，共60个slot = 10天）
    # 白班(8-20点): 100, 晚班(20-8点): 150
    labor_costs_per_day = [100, 100, 115, 135, 150, 140]  # 6个slot/天
    config.LABOR_COSTS = labor_costs_per_day * 10  # 10天
    
    # GA参数
    config.POPULATION_SIZE = 30
    config.MAX_GENERATIONS = 50
    config.CROSSOVER_RATE = 0.8
    config.MUTATION_RATE = 0.1
    config.ELITE_SIZE = 3
    
    # 局部搜索参数
    config.MAX_LS_ITERATIONS = 20
    
    return config


def load_orders(csv_path: str) -> OrderManager:
    """
    从CSV文件加载订单
    
    Args:
        csv_path: CSV文件路径
        
    Returns:
        OrderManager: 订单管理器对象
    """
    order_manager = OrderManager()
    order_manager.load_orders_from_csv(csv_path)
    return order_manager


def run_schedule(
    config: Config, 
    order_manager: OrderManager, 
    num_days: int
) -> Tuple[RollingScheduler, SimulationResult]:
    """
    运行完整调度周期，收集所有天的结果
    
    Args:
        config: 配置对象
        order_manager: 订单管理器
        num_days: 模拟天数
        
    Returns:
        Tuple[RollingScheduler, SimulationResult]: 调度器对象和完整模拟结果
    """
    # 重置所有订单状态（重要：避免多次运行时状态累积）
    for order in order_manager.get_all_orders():
        order.reset()
        order.penalized = False
        order.completed_slot = None  # 重置完成时间
    
    # 重新初始化待处理订单列表
    order_manager.pending_orders = [
        order for order in order_manager.get_all_orders() 
        if not order.is_completed()
    ]
    
    # 创建模拟结果对象
    simulation_result = SimulationResult(num_days)
    
    # 创建滚动调度器
    scheduler = RollingScheduler(config, order_manager)
    
    # 运行多天滚动调度，在每天执行后立即保存状态快照
    for day in range(num_days):
        # 执行当天调度
        schedule = scheduler.run_daily_schedule(current_day=day)
        
        # 立即创建当天结果对象并保存状态快照
        day_result = DayResult(day)
        day_result.schedule = schedule
        
        # 从daily_results获取当天的财务数据
        # 注意：run_daily_schedule执行后，daily_results已经添加了当天的数据
        if day < len(scheduler.cumulative_stats['daily_results']):
            daily_financial = scheduler.cumulative_stats['daily_results'][day]
            day_result.set_financial(
                revenue=daily_financial['revenue'],
                cost=daily_financial['cost'],
                penalty=daily_financial['penalty'],
                profit=daily_financial['profit']
            )
        
        # 收集当天结束时的订单进度快照
        all_orders = order_manager.get_all_orders()
        for order in all_orders:
            # 计算订单进度
            completed_qty = order.get_completed_quantity()
            progress = completed_qty / order.quantity if order.quantity > 0 else 0.0
            
            # 判断是否按期
            current_slot = order_manager.time_to_slot(day, hour=8)
            if order.is_completed():
                # 已完成订单：使用实际完成时间判断
                if order.completed_slot is not None:
                    is_on_time = order.completed_slot < order.due_slot
                else:
                    # 如果没有记录完成时间（旧数据），使用当前时间判断
                    is_on_time = current_slot < order.due_slot
            else:
                # 未完成订单：如果当前时间已超过截止时间，标记为延期风险
                is_on_time = current_slot < order.due_slot
            
            order_progress = {
                'order_id': order.order_id,
                'product': order.product,
                'quantity': order.quantity,
                'produced_today': 0,  # 需要从schedule中计算
                'cumulative_produced': completed_qty,
                'remaining': order.remaining,
                'progress': progress,
                'is_finished': order.is_completed(),
                'is_on_time': is_on_time,
                'due_slot': order.due_slot,
                'unit_price': order.unit_price
            }
            
            day_result.add_order_progress(order.order_id, order_progress)
        
        # 添加到模拟结果中
        simulation_result.add_day_result(day, day_result)
    
    # 设置累计统计数据
    cumulative_stats = scheduler.get_cumulative_statistics()
    simulation_result.set_cumulative_stats(cumulative_stats)
    
    return scheduler, simulation_result
