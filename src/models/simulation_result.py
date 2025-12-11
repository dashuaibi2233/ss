"""
模拟结果数据模型

存储完整调度周期的所有天的结果，供GUI按天浏览。
"""
from typing import Dict, List, Any


class DayResult:
    """单日调度结果"""
    
    def __init__(self, day_index: int):
        """
        初始化单日结果
        
        Args:
            day_index: 天数索引（0-based）
        """
        self.day_index = day_index
        self.schedule = None  # Schedule对象
        self.slots = []  # 时间段排程列表
        self.orders = {}  # 订单进度字典 {order_id: order_progress}
        self.financial = {
            'revenue': 0.0,
            'cost': 0.0,
            'penalty': 0.0,
            'profit': 0.0
        }
    
    def add_order_progress(self, order_id: int, order_data: Dict[str, Any]):
        """
        添加订单进度信息
        
        Args:
            order_id: 订单ID
            order_data: 订单进度数据
        """
        self.orders[order_id] = order_data
    
    def set_financial(self, revenue: float, cost: float, penalty: float, profit: float):
        """设置财务指标"""
        self.financial = {
            'revenue': revenue,
            'cost': cost,
            'penalty': penalty,
            'profit': profit
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'day_index': self.day_index,
            'schedule': self.schedule,
            'slots': self.slots,
            'orders': self.orders,
            'financial': self.financial
        }


class SimulationResult:
    """
    完整模拟结果类
    
    存储整个调度周期的所有天的结果，支持按天查询。
    """
    
    def __init__(self, num_days: int):
        """
        初始化模拟结果
        
        Args:
            num_days: 模拟天数
        """
        self.num_days = num_days
        self.days: Dict[int, DayResult] = {}  # {day_index: DayResult}
        self.cumulative_stats = {
            'total_revenue': 0.0,
            'total_cost': 0.0,
            'total_penalty': 0.0,
            'total_profit': 0.0,
            'total_orders': 0,
            'completed_orders': 0,
            'daily_results': []
        }
    
    def add_day_result(self, day_index: int, day_result: DayResult):
        """
        添加某一天的结果
        
        Args:
            day_index: 天数索引（0-based）
            day_result: 单日结果对象
        """
        self.days[day_index] = day_result
    
    def get_day_result(self, day_index: int) -> DayResult:
        """
        获取某一天的结果
        
        Args:
            day_index: 天数索引（0-based）
            
        Returns:
            DayResult: 单日结果对象，如果不存在返回None
        """
        return self.days.get(day_index, None)
    
    def set_cumulative_stats(self, stats: Dict[str, Any]):
        """设置累计统计数据"""
        self.cumulative_stats = stats
    
    def get_order_progress_history(self, order_id: int) -> List[Dict[str, Any]]:
        """
        获取某个订单在所有天的进度历史
        
        Args:
            order_id: 订单ID
            
        Returns:
            List[Dict]: 订单在每天的进度列表
        """
        history = []
        for day_idx in sorted(self.days.keys()):
            day_result = self.days[day_idx]
            if order_id in day_result.orders:
                order_data = day_result.orders[order_id].copy()
                order_data['day'] = day_idx + 1
                history.append(order_data)
        return history
    
    def get_all_orders_at_day(self, day_index: int) -> Dict[int, Dict[str, Any]]:
        """
        获取某一天所有订单的状态
        
        Args:
            day_index: 天数索引（0-based）
            
        Returns:
            Dict: {order_id: order_progress}
        """
        day_result = self.get_day_result(day_index)
        if day_result:
            return day_result.orders
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'num_days': self.num_days,
            'days': {day_idx: day_result.to_dict() 
                    for day_idx, day_result in self.days.items()},
            'cumulative_stats': self.cumulative_stats
        }
