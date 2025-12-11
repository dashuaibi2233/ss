"""
调度方案数据模型

存储具体的调度方案和相关统计信息。
"""
from collections import defaultdict
from typing import Dict, List, Tuple


class Schedule:
    """
    调度方案类
    
    Attributes:
        allocation: 订单分配方案 y_{o,l,t}
                   格式: {(order_id, line, slot): quantity}
        order_completion: 订单完成量统计
                         格式: {order_id: completed_quantity}
        revenue: 总收入
        cost: 总成本
        penalty: 总罚款
        profit: 总利润
    """
    
    def __init__(self):
        """初始化调度方案"""
        self.allocation = {}
        self.order_completion = {}
        self.revenue = 0.0
        self.cost = 0.0
        self.penalty = 0.0
        self.profit = 0.0
    
    def add_allocation(self, order_id, line, slot, quantity):
        """
        添加订单分配
        
        Args:
            order_id: 订单编号
            line: 生产线编号 (1-based)
            slot: 时间段编号 (1-based)
            quantity: 分配数量
        """
        if quantity > 0:
            key = (order_id, line, slot)
            self.allocation[key] = quantity
            
            # 更新订单完成量统计
            if order_id not in self.order_completion:
                self.order_completion[order_id] = 0
            self.order_completion[order_id] += quantity
    
    def calculate_metrics(self, orders, labor_costs, penalty_rate=0.1):
        """
        计算调度方案的各项指标
        
        Args:
            orders: 订单列表 (List[Order])
            labor_costs: 人工成本列表 (Dict[int, float] 或 List[float])
                        key 为 slot 编号 (1-based)，value 为该时间段的单位人工成本
            penalty_rate: 罚款比例，默认0.1 (10%)
        """
        # 重置指标
        self.revenue = 0.0
        self.cost = 0.0
        self.penalty = 0.0
        
        # 计算收入：每个订单的完成量 * 单价
        order_dict = {order.order_id: order for order in orders}
        for order_id, completed_qty in self.order_completion.items():
            if order_id in order_dict:
                order = order_dict[order_id]
                self.revenue += completed_qty * order.unit_price
        
        # 计算罚款：未按期完成的订单
        # 罚款规则：如果订单未完全完成，罚款 = 订单总金额 × 罚款比例
        for order in orders:
            completed_qty = self.order_completion.get(order.order_id, 0)
            # 如果订单未完全完成，罚款 = 订单总金额 × 罚款比例
            if completed_qty < order.quantity:
                self.penalty += order.quantity * order.unit_price * penalty_rate
        
        # 计算人工成本：统计每个 (line, slot) 是否工作
        working_slots = set()
        for (order_id, line, slot), qty in self.allocation.items():
            if qty > 0:
                working_slots.add((line, slot))
        
        # 汇总成本
        for (line, slot) in working_slots:
            # labor_costs 可能是 dict 或 list
            if isinstance(labor_costs, dict):
                cost_per_slot = labor_costs.get(slot, 0)
            else:
                # 如果是 list，假设为 0-based 索引
                cost_per_slot = labor_costs[slot - 1] if slot - 1 < len(labor_costs) else 0
            self.cost += cost_per_slot
        
        # 计算总利润
        self.profit = self.revenue - self.cost - self.penalty
    
    def get_line_schedule(self, line) -> Dict[int, List[Tuple[int, int]]]:
        """
        获取指定生产线的调度安排
        
        Args:
            line: 生产线编号 (1-based)
            
        Returns:
            dict: {slot: [(order_id, quantity), ...]}
                  该生产线每个时间段的订单分配
        """
        line_schedule = defaultdict(list)
        for (order_id, l, slot), qty in self.allocation.items():
            if l == line and qty > 0:
                line_schedule[slot].append((order_id, qty))
        return dict(line_schedule)
    
    def get_slot_product(self, line, slot, orders) -> int:
        """
        获取指定 (line, slot) 的产品类型
        
        Args:
            line: 生产线编号
            slot: 时间段编号
            orders: 订单列表
        
        Returns:
            int: 产品类型 (0=空闲, 1/2/3=产品编号)
        """
        order_dict = {order.order_id: order for order in orders}
        for (order_id, l, s), qty in self.allocation.items():
            if l == line and s == slot and qty > 0:
                if order_id in order_dict:
                    return order_dict[order_id].product
        return 0  # 空闲
    
    def get_order_completion_status(self, order) -> Tuple[int, bool]:
        """
        获取订单的完成情况
        
        Args:
            order: Order 对象
        
        Returns:
            tuple: (completed_quantity, is_on_time)
                   completed_quantity: 完成数量
                   is_on_time: 是否按期完成
        """
        completed_qty = self.order_completion.get(order.order_id, 0)
        is_on_time = completed_qty >= order.quantity
        return completed_qty, is_on_time
    
    def get_statistics(self, orders) -> Dict:
        """
        获取调度方案的统计信息
        
        Args:
            orders: 订单列表
        
        Returns:
            dict: 包含各种统计指标的字典
        """
        total_orders = len(orders)
        completed_orders = 0
        total_completion_rate = 0.0
        
        for order in orders:
            completed_qty = self.order_completion.get(order.order_id, 0)
            if completed_qty >= order.quantity:
                completed_orders += 1
            if order.quantity > 0:
                total_completion_rate += completed_qty / order.quantity
        
        avg_completion_rate = total_completion_rate / total_orders if total_orders > 0 else 0
        on_time_rate = completed_orders / total_orders if total_orders > 0 else 0
        
        # 统计工作的 slot 数量
        working_slots = set()
        for (order_id, line, slot), qty in self.allocation.items():
            if qty > 0:
                working_slots.add((line, slot))
        
        return {
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'on_time_rate': on_time_rate,
            'avg_completion_rate': avg_completion_rate,
            'total_working_slots': len(working_slots),
            'revenue': self.revenue,
            'cost': self.cost,
            'penalty': self.penalty,
            'profit': self.profit
        }
    
    def __repr__(self):
        """调度方案的字符串表示"""
        return f"Schedule(profit={self.profit:.2f}, revenue={self.revenue:.2f}, cost={self.cost:.2f}, penalty={self.penalty:.2f})"
