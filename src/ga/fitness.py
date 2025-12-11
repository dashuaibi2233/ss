"""
适应度评估模块

计算染色体的适应度值（总利润）。
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ga.decoder import Decoder


class FitnessEvaluator:
    """
    适应度评估器类
    
    根据调度方案计算总利润作为适应度值。
    """
    
    def __init__(self, config):
        """
        初始化适应度评估器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.decoder = Decoder(config)
    
    def evaluate(self, chromosome, orders):
        """
        评估染色体的适应度
        
        根据设计大纲3.3节，适应度 = Profit = Revenue - Cost - Penalty
        
        Args:
            chromosome: 染色体对象
            orders: 订单列表 (List[Order])
            
        Returns:
            float: 适应度值（总利润）
        """
        # 步骤1: 解码染色体，获取调度方案
        schedule = self.decoder.decode(chromosome, orders)
        
        # 步骤2: 计算指标（Revenue, Cost, Penalty, Profit）
        schedule.calculate_metrics(
            orders=orders,
            labor_costs=self.config.LABOR_COSTS,
            penalty_rate=self.config.PENALTY_RATE
        )
        
        # 步骤3: 返回总利润作为适应度
        return schedule.profit
    
    def evaluate_with_details(self, chromosome, orders):
        """
        评估染色体并返回详细信息
        
        Args:
            chromosome: 染色体对象
            orders: 订单列表
            
        Returns:
            tuple: (fitness, schedule) - 适应度值和调度方案对象
        """
        schedule = self.decoder.decode(chromosome, orders)
        schedule.calculate_metrics(
            orders=orders,
            labor_costs=self.config.LABOR_COSTS,
            penalty_rate=self.config.PENALTY_RATE
        )
        return schedule.profit, schedule
    
    def calculate_revenue(self, schedule, orders):
        """
        计算总收入（已集成到 Schedule.calculate_metrics 中）
        
        Args:
            schedule: 调度方案
            orders: 订单列表
            
        Returns:
            float: 总收入
        """
        revenue = 0.0
        order_dict = {order.order_id: order for order in orders}
        for order_id, completed_qty in schedule.order_completion.items():
            if order_id in order_dict:
                order = order_dict[order_id]
                revenue += completed_qty * order.unit_price
        return revenue
    
    def calculate_cost(self, schedule):
        """
        计算总成本（已集成到 Schedule.calculate_metrics 中）
        
        Args:
            schedule: 调度方案
            
        Returns:
            float: 总成本
        """
        cost = 0.0
        working_slots = set()
        for (order_id, line, slot), qty in schedule.allocation.items():
            if qty > 0:
                working_slots.add((line, slot))
        
        for (line, slot) in working_slots:
            if isinstance(self.config.LABOR_COSTS, dict):
                cost_per_slot = self.config.LABOR_COSTS.get(slot, 0)
            else:
                cost_per_slot = self.config.LABOR_COSTS[slot - 1] if slot - 1 < len(self.config.LABOR_COSTS) else 0
            cost += cost_per_slot
        
        return cost
    
    def calculate_penalty(self, schedule, orders):
        """
        计算总罚款（已集成到 Schedule.calculate_metrics 中）
        
        罚款规则：如果订单未完全完成，罚款 = 订单总金额 × 罚款比例
        
        Args:
            schedule: 调度方案
            orders: 订单列表
            
        Returns:
            float: 总罚款
        """
        penalty = 0.0
        for order in orders:
            completed_qty = schedule.order_completion.get(order.order_id, 0)
            # 如果订单未完全完成，罚款 = 订单总金额 × 罚款比例
            if completed_qty < order.quantity:
                penalty += order.quantity * order.unit_price * self.config.PENALTY_RATE
        return penalty


# 便捷函数：供 GAEngine 直接调用
def evaluate_chromosome(chromosome, orders, config):
    """
    评估染色体的适应度（便捷函数）
    
    这是一个独立的函数，方便 GAEngine 等模块直接调用，无需创建 FitnessEvaluator 实例。
    
    Args:
        chromosome: 染色体对象，包含 gene1 和 gene2
        orders: 订单列表 (List[Order])
        config: 配置对象，包含产能、成本等参数
        
    Returns:
        float: 适应度值（总利润 = Revenue - Cost - Penalty）
    
    Example:
        >>> fitness = evaluate_chromosome(chromosome, orders, config)
        >>> chromosome.fitness = fitness
    """
    evaluator = FitnessEvaluator(config)
    return evaluator.evaluate(chromosome, orders)
