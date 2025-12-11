"""
迭代局部搜索(ILS)和变邻域搜索(VNS)

在GA最优解基础上进行局部优化。
"""
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chromosome import Chromosome
from ga.fitness import evaluate_chromosome
from ga.decoder import Decoder


class LocalSearch:
    """
    局部搜索类
    
    实现ILS/VNS算法，对GA得到的解进行精化。
    """
    
    def __init__(self, config):
        """
        初始化局部搜索
        
        Args:
            config: 配置对象
        """
        self.config = config
    
    def optimize(self, initial_solution, orders):
        """
        执行局部搜索优化
        
        按照设计大纷3.5节ILS/VNS伪代码：
        1. 随机选择一个邻域结构 Nk
        2. 在 c_best 上应用 Nk 生成邻域解 c_new
        3. 解码 c_new，计算 Fitness(c_new)
        4. 如果 Fitness(c_new) > Fitness(c_best)，接受改进解
        
        Args:
            initial_solution: 初始解（GA最优解）
            orders: 订单列表
            
        Returns:
            Chromosome: 优化后的解
        """
        # 复制初始解
        current_best = initial_solution.copy()
        current_best.fitness = evaluate_chromosome(current_best, orders, self.config)
        
        max_iter = self.config.MAX_LS_ITERATIONS
        no_improvement_count = 0
        
        print(f"\n启动局部搜索 (ILS/VNS)...")
        print(f"初始适应度: {current_best.fitness:.2f}")
        
        for iteration in range(max_iter):
            # 随机选择邻域操作
            neighborhood_type = random.choice(['N1', 'N2'])
            
            # 应用邻域操作生成新解
            if neighborhood_type == 'N1':
                new_solution = self.neighborhood_swap_slots(current_best)
            else:  # N2
                new_solution = self.neighborhood_adjust_allocation(current_best, orders)
            
            # 计算新解的适应度
            new_solution.fitness = evaluate_chromosome(new_solution, orders, self.config)
            
            # 判断是否接受新解
            if self.accept_solution(current_best.fitness, new_solution.fitness):
                current_best = new_solution
                no_improvement_count = 0
                print(f"  第 {iteration + 1} 次迭代: 改善! 新适应度: {current_best.fitness:.2f} (使用 {neighborhood_type})")
            else:
                no_improvement_count += 1
            
            # 早停：连续多次无改善
            if no_improvement_count >= 10:
                print(f"  第 {iteration + 1} 次迭代提前终止 (连续10次无改善)")
                break
        
        print(f"局部搜索完成。最终适应度: {current_best.fitness:.2f}")
        print(f"改善程度: {current_best.fitness - initial_solution.fitness:.2f}\n")
        
        return current_best
    
    def neighborhood_swap_slots(self, chromosome):
        """
        邻域操作N1：交换时间段产品
        
        随机选定一条生产线 l 和两个时间段 t1, t2，
        交换 Gene1 中对应位置的产品类型。
        
        Args:
            chromosome: 当前染色体
            
        Returns:
            Chromosome: 邻域解
        """
        # 复制染色体
        neighbor = chromosome.copy()
        
        if len(neighbor.gene1) < 2:
            return neighbor
        
        # 计算生产线和时间段数量
        num_lines = self.config.NUM_LINES
        num_slots = len(neighbor.gene1) // num_lines
        
        # 随机选择一条生产线
        line_idx = random.randint(0, num_lines - 1)
        
        # 随机选择该生产线上的两个不同时间段
        slot1_idx = random.randint(0, num_slots - 1)
        slot2_idx = random.randint(0, num_slots - 1)
        
        # 计算在 gene1 中的索引
        gene_idx1 = line_idx * num_slots + slot1_idx
        gene_idx2 = line_idx * num_slots + slot2_idx
        
        # 交换产品类型
        neighbor.gene1[gene_idx1], neighbor.gene1[gene_idx2] = \
            neighbor.gene1[gene_idx2], neighbor.gene1[gene_idx1]
        
        return neighbor
    
    def neighborhood_adjust_allocation(self, chromosome, orders):
        """
        邻域操作N2：微调订单分配
        
        在固定 Gene1 不变的前提下，选择某一订单，
        在其可用 slot 内尝试将部分产量从某个 slot 移到另一个 slot。
        通过调整 Gene2 中订单的优先级来实现。
        
        Args:
            chromosome: 当前染色体
            orders: 订单列表
            
        Returns:
            Chromosome: 邻域解
        """
        # 复制染色体
        neighbor = chromosome.copy()
        
        if len(neighbor.gene2) < 2:
            return neighbor
        
        # 随机选择两个订单位置进行交换（改变优先级）
        # 这会导致解码时订单分配的顺序发生变化，从而微调分配
        idx1 = random.randint(0, len(neighbor.gene2) - 1)
        idx2 = random.randint(0, len(neighbor.gene2) - 1)
        
        # 交换订单优先级
        neighbor.gene2[idx1], neighbor.gene2[idx2] = neighbor.gene2[idx2], neighbor.gene2[idx1]
        
        return neighbor
    
    def accept_solution(self, current_fitness, new_fitness):
        """
        判断是否接受新解
        
        局部搜索采用贪心策略：只接受更优的解。
        可扩展：引入模拟退火策略，以一定概率接受较差解。
        
        Args:
            current_fitness: 当前解适应度
            new_fitness: 新解适应度
            
        Returns:
            bool: 是否接受
        """
        # 贪心策略：只接受更优的解
        return new_fitness > current_fitness


# 便捷函数：供外部直接调用
def improve_solution(chromosome, orders, config):
    """
    改进解（便捷函数）
    
    这是一个独立的函数，方便外部模块直接调用局部搜索。
    接受 GA 的最优解，基于 ILS/VNS 进行局部优化。
    
    Args:
        chromosome: 初始染色体（GA最优解）
        orders: 订单列表 (List[Order])
        config: 配置对象，包含局部搜索参数
        
    Returns:
        Chromosome: 改进后的染色体
    
    Example:
        >>> from local_search.ils_vns import improve_solution
        >>> from ga.engine import run_ga
        >>> ga_best = run_ga(orders, config)
        >>> improved_solution = improve_solution(ga_best, orders, config)
        >>> print(f"Improvement: {improved_solution.fitness - ga_best.fitness:.2f}")
    """
    local_search = LocalSearch(config)
    improved = local_search.optimize(chromosome, orders)
    return improved
