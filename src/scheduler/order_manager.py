"""
订单管理模块

负责订单的增删改查和订单池维护。
"""
import csv
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.order import Order


class OrderManager:
    """
    订单管理器类
    
    管理订单池，处理订单的增删改查操作。
    """
    
    def __init__(self):
        """初始化订单管理器"""
        self.orders = {}  # {order_id: Order}
        self.pending_orders = []  # 待处理订单列表
    
    def add_order(self, order):
        """
        添加订单
        
        Args:
            order: 订单对象 (Order)
        """
        self.orders[order.order_id] = order
        # 如果订单未完成，加入待处理列表
        if not order.is_completed():
            if order not in self.pending_orders:
                self.pending_orders.append(order)
    
    def remove_order(self, order_id):
        """
        移除订单
        
        Args:
            order_id: 订单编号
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            # 从待处理列表中移除
            if order in self.pending_orders:
                self.pending_orders.remove(order)
            # 从订单字典中移除
            del self.orders[order_id]
    
    def get_order(self, order_id):
        """
        获取订单
        
        Args:
            order_id: 订单编号
            
        Returns:
            Order: 订单对象，如果不存在则返回 None
        """
        return self.orders.get(order_id, None)
    
    def get_pending_orders(self):
        """
        获取所有待处理订单（未完成的订单）
        
        按照滚动调度策略，返回所有未完成订单 + 新订单。
        
        Returns:
            list: 待处理订单列表 (List[Order])
        """
        # 更新待处理列表，移除已完成的订单
        self.pending_orders = [order for order in self.pending_orders if not order.is_completed()]
        return self.pending_orders
    
    def update_order_status(self, order_id, completed_quantity):
        """
        更新订单状态
        
        根据已完成数量更新订单的剩余需求。
        
        Args:
            order_id: 订单编号
            completed_quantity: 已完成数量
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            order.update_remaining(completed_quantity)
            
            # 如果订单已完成，从待处理列表中移除
            if order.is_completed() and order in self.pending_orders:
                self.pending_orders.remove(order)
    
    def load_orders_from_csv(self, filepath):
        """
        从 CSV 文件加载订单
        
        CSV 格式：order_id, product, quantity, due_slot, unit_price
        
        Args:
            filepath: CSV文件路径
            
        Returns:
            int: 加载的订单数量
        """
        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    order = Order(
                        order_id=int(row['order_id']),
                        product=int(row['product']),
                        quantity=int(row['quantity']),
                        due_slot=int(row['due_slot']),
                        unit_price=float(row['unit_price'])
                    )
                    self.add_order(order)
                    count += 1
            print(f"从 {filepath} 加载了 {count} 个订单")
        except FileNotFoundError:
            print(f"错误: 文件 {filepath} 未找到")
        except Exception as e:
            print(f"加载订单错误: {e}")
        
        return count
    
    def time_to_slot(self, day, hour=8):
        """
        将日期和小时转换为 slot 索引
        
        假设每天 6 个 slot，每个 slot 4 小时：
        - slot 1: 8:00-12:00
        - slot 2: 12:00-16:00
        - slot 3: 16:00-20:00
        - slot 4: 20:00-24:00
        - slot 5: 0:00-4:00
        - slot 6: 4:00-8:00
        
        Args:
            day: 天数（0-based）
            hour: 小时（0-23），默认8点
            
        Returns:
            int: slot 索引 (1-based)
        """
        # 每天 6 个 slot
        slots_per_day = 6
        # 以早上 8 点作为每天的起始 slot=1
        # 使用模运算处理跨天时间，例如 0 点应映射到 slot5
        slot_in_day = ((hour - 8) % 24) // 4 + 1
        # 计算总 slot
        total_slot = day * slots_per_day + slot_in_day
        return total_slot
    
    def get_all_orders(self):
        """
        获取所有订单
        
        Returns:
            list: 所有订单列表
        """
        return list(self.orders.values())
    
    def get_order_count(self):
        """
        获取订单总数
        
        Returns:
            int: 订单数量
        """
        return len(self.orders)
    
    def get_pending_count(self):
        """
        获取待处理订单数量
        
        Returns:
            int: 待处理订单数量
        """
        return len(self.get_pending_orders())
