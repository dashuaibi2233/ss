"""
染色体数据模型

定义遗传算法中染色体的编码结构。
"""
import copy


class Chromosome:
    """
    染色体类
    
    Attributes:
        gene1: 产线-时间-产品结构编码 (长度为 3*H 的整数数组)
               值含义: 0=空闲, 1/2/3=产品类型
        gene2: 订单优先级排列 (订单编号的排列)
        fitness: 适应度值（总利润）
    """
    
    def __init__(self, gene1=None, gene2=None):
        """
        初始化染色体
        
        Args:
            gene1: 产线-时间-产品结构编码
            gene2: 订单优先级排列
        """
        self.gene1 = gene1 if gene1 is not None else []
        self.gene2 = gene2 if gene2 is not None else []
        self.fitness = 0.0
    
    def copy(self):
        """
        复制染色体
        
        Returns:
            Chromosome: 染色体的深拷贝
        """
        new_chromosome = Chromosome(
            gene1=copy.deepcopy(self.gene1),
            gene2=copy.deepcopy(self.gene2)
        )
        new_chromosome.fitness = self.fitness
        return new_chromosome
    
    def validate(self, num_lines=3, num_slots=None, num_orders=None):
        """
        校验染色体的合法性
        
        Args:
            num_lines: 生产线数量，默认3
            num_slots: 时间段数量（如果为None则不检查）
            num_orders: 订单数量（如果为None则不检查）
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # 检查 gene1
        if num_slots is not None:
            expected_length = num_lines * num_slots
            if len(self.gene1) != expected_length:
                return False, f"gene1 长度错误: 期望 {expected_length}, 实际 {len(self.gene1)}"
        
        # 检查 gene1 中的值是否合法 (0=空闲, 1/2/3=产品类型)
        for i, val in enumerate(self.gene1):
            if val not in [0, 1, 2, 3]:
                return False, f"gene1[{i}] 值非法: {val}, 应为 0-3"
        
        # 检查 gene2
        if num_orders is not None:
            if len(self.gene2) != num_orders:
                return False, f"gene2 长度错误: 期望 {num_orders}, 实际 {len(self.gene2)}"
            
            # 检查 gene2 是否为合法的排列
            if set(self.gene2) != set(range(num_orders)):
                return False, f"gene2 不是合法的订单排列"
        
        return True, ""
    
    def display(self, num_lines=3, num_slots=None):
        """
        打印染色体信息（用于调试）
        
        Args:
            num_lines: 生产线数量
            num_slots: 时间段数量
        
        Returns:
            str: 格式化的染色体信息
        """
        lines = []
        lines.append(f"Chromosome (fitness={self.fitness:.2f})")
        lines.append("="*50)
        
        # 显示 Gene1 (产线-时间-产品结构)
        lines.append("Gene1 (产线-时间-产品结构):")
        if num_slots is not None and len(self.gene1) == num_lines * num_slots:
            for line_idx in range(num_lines):
                line_schedule = self.gene1[line_idx * num_slots:(line_idx + 1) * num_slots]
                product_map = {0: '-', 1: 'P1', 2: 'P2', 3: 'P3'}
                schedule_str = ' '.join([product_map.get(p, '?') for p in line_schedule])
                lines.append(f"  Line {line_idx + 1}: {schedule_str}")
        else:
            lines.append(f"  {self.gene1}")
        
        # 显示 Gene2 (订单优先级)
        lines.append("\nGene2 (订单优先级):")
        if len(self.gene2) <= 20:
            lines.append(f"  {self.gene2}")
        else:
            lines.append(f"  {self.gene2[:10]} ... {self.gene2[-10:]} (total: {len(self.gene2)})")
        
        return '\n'.join(lines)
    
    def __repr__(self):
        """染色体的字符串表示"""
        return f"Chromosome(fitness={self.fitness:.2f}, gene1_len={len(self.gene1)}, gene2_len={len(self.gene2)})"
