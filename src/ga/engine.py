"""
遗传算法引擎

实现遗传算法的主流程控制。
"""
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chromosome import Chromosome
from ga.operators import GeneticOperators
from ga.fitness import evaluate_chromosome
from ga.island_engine import run_island_ga


class GAEngine:
    """
    遗传算法引擎类
    
    负责种群初始化、迭代进化、精英保留等核心流程。
    """
    
    def __init__(self, config, orders, planning_horizon=None, start_slot=1):
        """
        初始化GA引擎
        
        Args:
            config: 配置对象
            orders: 订单列表
            planning_horizon: 规划时域（slot 数量），用于确定 Gene1 的长度；
                               若为空则根据订单数量估算。
            start_slot: 当前优化窗口的起始 slot（1-based），用于解码时对齐全局时间轴。
        """
        self.config = config
        self.orders = orders
        self.planning_horizon = planning_horizon
        self.start_slot = start_slot
        self.population = []
        self.best_chromosome = None
    
    def initialize_population(self):
        """
        初始化种群
        
        生成初始种群，包括随机个体和启发式个体。
        按照设计大纷3.4节：
        - Gene1 随机生成（随机指定每个 slot 的产品或空闲）
        - Gene2 生成随机订单排列
        - 可加入启发式个体（如最早截止日期优先）
        """
        self.population = []
        
        num_lines = self.config.NUM_LINES
        # 优先使用外部指定的规划时域，否则根据订单数量估算
        if self.planning_horizon is not None:
            num_slots = self.planning_horizon
        else:
            num_slots = self.config.SLOTS_PER_DAY * (len(self.orders) // 10 + 1)
        num_orders = len(self.orders)
        gene1_length = num_lines * num_slots
        
        # 生成随机个体
        num_random = int(self.config.POPULATION_SIZE * 0.8)  # 80% 随机个体
        for _ in range(num_random):
            # 随机生成 Gene1 (0=空闲, 1/2/3=产品)
            gene1 = [random.randint(0, self.config.NUM_PRODUCTS) for _ in range(gene1_length)]
            
            # 随机生成 Gene2 (订单排列)
            gene2 = list(range(num_orders))
            random.shuffle(gene2)
            
            chromosome = Chromosome(gene1=gene1, gene2=gene2)
            self.population.append(chromosome)
        
        # 生成启发式个体（EDD - 最早截止日期优先）
        num_heuristic = self.config.POPULATION_SIZE - num_random
        for _ in range(num_heuristic):
            # Gene1 随机生成
            gene1 = [random.randint(0, self.config.NUM_PRODUCTS) for _ in range(gene1_length)]
            
            # Gene2 按截止日期排序
            order_indices = list(range(num_orders))
            order_indices.sort(key=lambda i: self.orders[i].due_slot)
            gene2 = order_indices
            
            chromosome = Chromosome(gene1=gene1, gene2=gene2)
            self.population.append(chromosome)
        
        # 计算初始种群的适应度
        for chromosome in self.population:
            chromosome.fitness = evaluate_chromosome(
                chromosome, self.orders, self.config, start_slot=self.start_slot
            )
    
    def evolve(self):
        """
        执行遗传算法进化过程
        
        按照设计大纷3.4节流程：
        1. 选择
        2. 交叉
        3. 变异
        4. 解码 & 计算适应度
        5. 精英保留
        6. 终止条件检查
        
        Returns:
            Chromosome: 最优染色体
        """
        best_fitness_history = []
        no_improvement_count = 0
        
        for generation in range(self.config.MAX_GENERATIONS):
            # 选择父代
            parents = self.select_parents()
            
            # 生成下一代
            offspring = self.create_next_generation(parents)
            
            # 计算后代适应度
            for child in offspring:
                child.fitness = evaluate_chromosome(
                    child, self.orders, self.config, start_slot=self.start_slot
                )
            
            # 精英保留：按适应度排序，保留最优个体
            self.population.sort(key=lambda x: x.fitness, reverse=True)
            elite = self.population[:self.config.ELITE_SIZE]
            
            # 组合精英和后代，选择最优的个体进入下一代
            combined = elite + offspring
            combined.sort(key=lambda x: x.fitness, reverse=True)
            self.population = combined[:self.config.POPULATION_SIZE]
            
            # 记录当前最优解
            current_best = self.population[0]
            if self.best_chromosome is None or current_best.fitness > self.best_chromosome.fitness:
                self.best_chromosome = current_best.copy()
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            best_fitness_history.append(self.best_chromosome.fitness)
            
            # 打印进度（每10代）
            if (generation + 1) % 10 == 0:
                print(f"第 {generation + 1}/{self.config.MAX_GENERATIONS} 代, "
                      f"最优适应度: {self.best_chromosome.fitness:.2f}, "
                      f"平均适应度: {sum(ind.fitness for ind in self.population) / len(self.population):.2f}")
            
            # 终止条件：连续多代无改善
            if no_improvement_count >= 20:
                print(f"第 {generation + 1} 代提前终止，因为没有改善")
                break
        
        self.fitness_history = best_fitness_history
        return self.best_chromosome
    
    def get_fitness_history(self):
        return getattr(self, "fitness_history", [])
    
    def select_parents(self):
        """
        选择父代个体
        
        使用锦标赛选择，选择与种群规模相同数量的父代。
        
        Returns:
            list: 选中的父代个体列表
        """
        parents = []
        for _ in range(self.config.POPULATION_SIZE):
            parent = GeneticOperators.tournament_selection(self.population, tournament_size=3)
            parents.append(parent)
        return parents
    
    def create_next_generation(self, parents):
        """
        创建下一代种群
        
        通过交叉和变异操作生成后代。
        
        Args:
            parents: 父代个体列表
            
        Returns:
            list: 新一代种群
        """
        offspring = []
        
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]
            
            # 交叉操作
            if random.random() < self.config.CROSSOVER_RATE:
                # Gene1 交叉
                child1_gene1, child2_gene1 = GeneticOperators.crossover_gene1(parent1, parent2)
                # Gene2 交叉
                child1_gene2, child2_gene2 = GeneticOperators.crossover_gene2(parent1, parent2)
                
                child1 = Chromosome(gene1=child1_gene1, gene2=child1_gene2)
                child2 = Chromosome(gene1=child2_gene1, gene2=child2_gene2)
            else:
                # 不交叉，直接复制父代
                child1 = parent1.copy()
                child2 = parent2.copy()
            
            # 变异操作
            GeneticOperators.mutate_gene1(child1, self.config.MUTATION_RATE, self.config.NUM_PRODUCTS)
            GeneticOperators.mutate_gene2(child1, self.config.MUTATION_RATE)
            
            GeneticOperators.mutate_gene1(child2, self.config.MUTATION_RATE, self.config.NUM_PRODUCTS)
            GeneticOperators.mutate_gene2(child2, self.config.MUTATION_RATE)
            
            offspring.append(child1)
            offspring.append(child2)
        
        return offspring
    
    def get_best_solution(self):
        """
        获取当前最优解
        
        Returns:
            Chromosome: 最优染色体
        """
        if self.best_chromosome is None and self.population:
            self.best_chromosome = max(self.population, key=lambda x: x.fitness)
        return self.best_chromosome


# 便捷函数：供外部直接调用
def run_ga(orders, config, planning_horizon=None, start_slot=1):
    """
    运行遗传算法（便捷函数）
    
    这是一个独立的函数，方便外部模块直接调用遗传算法。
    
    Args:
        orders: 订单列表 (List[Order])
        config: 配置对象，包含 GA 参数
        planning_horizon: 规划时域（slot 数量），控制 Gene1 长度；
                          若为 None 则由 GAEngine 自动估算。
        start_slot: 规划窗口的起始 slot（1-based），保证解码后的 slot 与全局时间线对齐。
        
    Returns:
        Chromosome: 最优染色体
    
    Example:
        >>> from ga.engine import run_ga
        >>> from config import Config
        >>> config = Config()
        >>> best_solution = run_ga(orders, config)
        >>> print(f"Best fitness: {best_solution.fitness}")
    """
    # 判断是否启用岛模型 GA（NUM_ISLANDS > 1 时才真正走多岛路径）
    enable_island = bool(getattr(config, "ENABLE_ISLAND_GA", False))
    num_islands = int(getattr(config, "NUM_ISLANDS", 1))
    if enable_island and num_islands > 1:
        # 将调用委托给岛模型 GA 引擎
        return run_island_ga(
            orders,
            config,
            planning_horizon=planning_horizon,
            start_slot=start_slot,
        )

    print("="*60)
    print("启动遗传算法...")
    print(f"种群规模: {config.POPULATION_SIZE}")
    print(f"最大迭代次数: {config.MAX_GENERATIONS}")
    print(f"交叉率: {config.CROSSOVER_RATE}")
    print(f"变异率: {config.MUTATION_RATE}")
    print(f"精英个体数: {config.ELITE_SIZE}")
    print(f"订单数量: {len(orders)}")
    print(f"规划窗口: 从 slot {start_slot} 开始，长度 {planning_horizon or '自动估算'}")
    print("="*60)
    
    # 创建 GA 引擎（单种群模式）
    ga_engine = GAEngine(
        config, orders, planning_horizon=planning_horizon, start_slot=start_slot
    )
    
    # 初始化种群
    print("\n初始化种群...")
    ga_engine.initialize_population()
    print(f"初始种群已创建，共 {len(ga_engine.population)} 个个体")
    print(f"初始最优适应度: {max(ind.fitness for ind in ga_engine.population):.2f}")
    
    # 执行进化
    print("\n开始进化...\n")
    best_chromosome = ga_engine.evolve()
    
    # 输出结果
    print("\n" + "="*60)
    print("遗传算法完成!")
    print(f"最优适应度: {best_chromosome.fitness:.2f}")
    print("="*60)
    
    return best_chromosome
