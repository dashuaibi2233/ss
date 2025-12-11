"""
染色体解码模块

将染色体编码解码为具体的调度方案。
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule import Schedule


class Decoder:
    """
    解码器类
    
    将染色体的基因编码转换为具体的订单分配方案。
    """
    
    def __init__(self, config):
        """
        初始化解码器
        
        Args:
            config: 配置对象
        """
        self.config = config
    
    def decode(self, chromosome, orders, start_slot=1):
        """
        解码染色体
        
        根据Gene1和Gene2生成具体的调度方案。
        严格遵循设计大纲 3.2 节的伪代码逻辑，并允许通过 start_slot
        将解码后的 slot 对齐到全局时间轴，实现滚动调度窗口的平移。
        
        Args:
            chromosome: 染色体对象，包含 gene1 和 gene2
            orders: 订单列表 (List[Order])
            start_slot: 当前规划窗口在全局时间轴的起点（1-based）
            
        Returns:
            Schedule: 调度方案对象，包含 y_{o,l,t} 分配结果
        """
        # 步骤1: 初始化调度方案
        schedule = Schedule()
        
        # 步骤2: 根据 Gene1 计算每个 (l,t) 的可用产能
        available_capacity = self.calculate_available_capacity(
            chromosome.gene1, start_slot=start_slot
        )
        
        # 步骤3: 按 Gene2 中的订单优先级依次分配
        # Gene2 存储的是订单索引（0-based），需要转换为实际订单对象
        for order_idx in chromosome.gene2:
            # 检查索引是否有效
            if order_idx < 0 or order_idx >= len(orders):
                continue
            
            order = orders[order_idx]
            order_id = order.order_id
            target_product = order.product
            remaining_demand = order.quantity
            
            # 3.2: 在所有满足条件的 slot 中按时间升序遍历
            # 收集所有可用的 (line, slot) 并按 slot 排序
            available_slots = []
            for (line, slot, product), capacity in available_capacity.items():
                # 移除 slot <= order.due_slot 限制，允许继续生产延期订单
                if product == target_product and capacity > 0:
                    available_slots.append((slot, line, capacity))
            
            # 按时间升序排序
            available_slots.sort(key=lambda x: (x[0], x[1]))
            
            # 依次分配产能
            for slot, line, capacity in available_slots:
                if remaining_demand <= 0:
                    break
                
                # 可分配量 = min(可用产能, 订单剩余需求)
                allocate_qty = min(capacity, remaining_demand)
                
                # 更新分配方案
                schedule.add_allocation(order_id, line, slot, allocate_qty)
                
                # 更新可用产能和剩余需求
                key = (line, slot, target_product)
                available_capacity[key] -= allocate_qty
                remaining_demand -= allocate_qty
        
        return schedule
    
    def calculate_available_capacity(self, gene1, start_slot=1):
        """
        计算各时间段可用产能
        
        根据 Gene1 和产品产能配置，计算每个 (line, slot, product) 的可用产能。
        Gene1 编码格式：长度为 num_lines * num_slots 的数组
        索引 k = line_idx * num_slots + slot_idx 对应 (line_idx+1, slot_idx+1) 的产品类型
        
        Args:
            gene1: 产线-时间-产品结构编码 (List[int])
                   值含义: 0=空闲, 1/2/3=产品类型
            
        Returns:
            dict: 可用产能字典 {(line, slot, product): capacity}
        """
        available_capacity = {}
        
        num_lines = self.config.NUM_LINES
        num_slots = len(gene1) // num_lines
        
        # 遍历所有 (line, slot)
        for line_idx in range(num_lines):
            for slot_idx in range(num_slots):
                # 计算 gene1 中的索引
                gene_index = line_idx * num_slots + slot_idx
                product = gene1[gene_index]
                
                # 如果该 slot 有生产任务（非空闲）
                if product != 0:
                    # 获取该产品的产能
                    capacity = self.config.CAPACITY.get(product, 0)
                    
                    # 使用 1-based 索引
                    line = line_idx + 1
                    slot = start_slot + slot_idx
                    
                    # 记录可用产能
                    key = (line, slot, product)
                    available_capacity[key] = capacity
        
        return available_capacity
    
    def allocate_orders(self, gene2, orders, available_capacity):
        """
        按优先级分配订单（已整合到 decode 方法中）
        
        此方法保留用于可能的独立调用场景。
        
        Args:
            gene2: 订单优先级排列 (List[int])
            orders: 订单列表 (List[Order])
            available_capacity: 可用产能字典 {(line, slot, product): capacity}
            
        Returns:
            dict: 订单分配方案 {(order_id, line, slot): quantity}
        """
        allocation = {}
        
        # Gene2 存储的是订单索引（0-based），需要转换为实际订单对象
        for order_idx in gene2:
            if order_idx < 0 or order_idx >= len(orders):
                continue
            
            order = orders[order_idx]
            order_id = order.order_id
            target_product = order.product
            remaining_demand = order.quantity
            
            # 收集所有可用的 (line, slot) 并按 slot 排序
            available_slots = []
            for (line, slot, product), capacity in available_capacity.items():
                # 移除 slot <= order.due_slot 限制，允许继续生产延期订单
                if product == target_product and capacity > 0:
                    available_slots.append((slot, line, capacity))
            
            # 按时间升序排序
            available_slots.sort(key=lambda x: (x[0], x[1]))
            
            # 依次分配产能
            for slot, line, capacity in available_slots:
                if remaining_demand <= 0:
                    break
                
                allocate_qty = min(capacity, remaining_demand)
                
                # 记录分配
                key = (order_id, line, slot)
                allocation[key] = allocate_qty
                
                # 更新可用产能和剩余需求
                cap_key = (line, slot, target_product)
                available_capacity[cap_key] -= allocate_qty
                remaining_demand -= allocate_qty
        
        return allocation
