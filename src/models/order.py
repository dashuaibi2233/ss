"""
订单数据模型

定义订单的数据结构和相关操作。
"""


class Order:
    """
    订单类
    
    Attributes:
        order_id: 订单编号
        product: 产品类型 (1, 2, 3)
        quantity: 需求数量
        remaining: 剩余未完成数量
        due_slot: 截止时间（以slot为单位）
        unit_price: 单位售价
    """
    
    def __init__(self, order_id, product, quantity, due_slot, unit_price):
        """
        初始化订单
        
        Args:
            order_id: 订单编号
            product: 产品类型
            quantity: 需求数量
            due_slot: 截止时间
            unit_price: 单位售价
        """
        self.order_id = order_id
        self.product = product
        self.quantity = quantity
        self.remaining = quantity
        self.due_slot = due_slot
        self.unit_price = unit_price
        self.penalized = False  # 是否已被罚款
        self.completed_slot = None  # 完成时的时段（用于判断是否按期）
    
    def update_remaining(self, completed):
        """
        更新剩余数量
        
        Args:
            completed: 已完成数量
        """
        self.remaining = max(0, self.quantity - completed)
    
    def is_completed(self):
        """
        检查订单是否完成
        
        Returns:
            bool: 订单是否完成
        """
        return self.remaining <= 0
    
    def get_completed_quantity(self):
        """
        获取已完成数量
        
        Returns:
            int: 已完成数量
        """
        return self.quantity - self.remaining
    
    def calculate_value(self):
        """
        计算订单总价值（完成部分的收入）
        
        Returns:
            float: 订单价值 = 已完成数量 * 单价
        """
        completed = self.get_completed_quantity()
        return completed * self.unit_price
    
    def calculate_penalty(self, penalty_rate=0.1):
        """
        计算违约罚款
        
        罚款规则：如果订单未完全完成，罚款 = 订单总金额 × 罚款比例
        
        Args:
            penalty_rate: 罚款比例，默认为订单总金额的10%
        
        Returns:
            float: 罚款金额 = 订单总金额 * 罚款比例（如果未完成）
        """
        if self.remaining > 0:
            # 订单未完成，罚款 = 订单总金额 × 罚款比例
            return self.quantity * self.unit_price * penalty_rate
        return 0.0
    
    def reset(self):
        """
        重置订单状态（将剩余数量恢复为初始需求量）
        """
        self.remaining = self.quantity
    
    def __repr__(self):
        """订单的字符串表示"""
        return f"Order(id={self.order_id}, product={self.product}, qty={self.quantity}, due={self.due_slot})"
