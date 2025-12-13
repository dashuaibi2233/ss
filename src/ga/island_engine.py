"""
岛模型遗传算法引擎

在现有单种群遗传算法的基础上，引入多岛并行进化与精英迁移机制，
用于增强全局搜索的多样性与解的稳定性。

说明：
- 本模块仅在配置显式启用岛模型 GA 时生效；
- 当岛数量退化为 1 或未开启岛模型开关时，系统仍使用原单种群 GA 引擎。
"""

import os
import sys
import random

# 将 src 目录加入路径，保持与其他 GA 模块一致的导入方式
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chromosome import Chromosome
from ga.operators import GeneticOperators
from ga.fitness import evaluate_chromosome


class IslandGAEngine:
    """岛模型遗传算法引擎"""

    def __init__(self, config, orders, planning_horizon=None, start_slot=1):
        """初始化岛模型 GA 引擎

        Args:
            config: 配置对象
            orders: 订单列表
            planning_horizon: 规划时域（slot 数量），用于确定 Gene1 的长度；
            start_slot: 当前优化窗口在全局时间轴上的起始 slot（1-based）
        """
        self.config = config
        self.orders = orders
        self.planning_horizon = planning_horizon
        self.start_slot = start_slot

        self.islands = []  # List[List[Chromosome]]
        self.best_chromosome = None
        self.global_best_history = []

    # ---------------------- 初始化相关 ----------------------

    def _get_island_type(self, island_index: int) -> str:
        """根据岛索引获取岛类型（profit/delivery/explore 等）"""
        types = getattr(self.config, "ISLAND_TYPES", ["profit", "delivery", "explore"])
        if not types:
            return "profit"
        return types[island_index % len(types)]

    def _get_num_slots(self) -> int:
        """确定规划窗口内的 slot 数量（与单种群 GA 保持一致的推断逻辑）"""
        if self.planning_horizon is not None:
            return self.planning_horizon
        # 与 GAEngine 中的估算方式保持一致
        return self.config.SLOTS_PER_DAY * (len(self.orders) // 10 + 1)

    def initialize_islands(self):
        """初始化所有岛的种群"""
        self.islands = []

        num_islands = max(1, int(getattr(self.config, "NUM_ISLANDS", 1)))
        num_lines = self.config.NUM_LINES
        num_slots = self._get_num_slots()
        num_orders = len(self.orders)
        gene1_length = num_lines * num_slots

        for island_index in range(num_islands):
            island_type = self._get_island_type(island_index)
            population = []
            pop_size = self.config.POPULATION_SIZE

            # 不同岛的随机 / 启发式比例
            if island_type == "delivery":
                random_ratio = 0.5
            elif island_type == "explore":
                random_ratio = 0.9
            else:  # profit 及其他
                random_ratio = 0.8

            num_random = max(0, min(pop_size, int(pop_size * random_ratio)))
            num_heuristic = max(0, pop_size - num_random)

            # 随机个体：Gene1/Gene2 完全随机
            for _ in range(num_random):
                gene1 = [
                    random.randint(0, self.config.NUM_PRODUCTS)
                    for _ in range(gene1_length)
                ]
                gene2 = list(range(num_orders))
                random.shuffle(gene2)
                population.append(Chromosome(gene1=gene1, gene2=gene2))

            # 启发式个体：Gene2 按截止时间排序（EDD），Gene1 仍随机
            if num_heuristic > 0:
                order_indices = list(range(num_orders))
                order_indices.sort(key=lambda i: self.orders[i].due_slot)
                for _ in range(num_heuristic):
                    gene1 = [
                        random.randint(0, self.config.NUM_PRODUCTS)
                        for _ in range(gene1_length)
                    ]
                    gene2 = order_indices.copy()
                    population.append(Chromosome(gene1=gene1, gene2=gene2))

            # 计算初始适应度
            for chrom in population:
                chrom.fitness = evaluate_chromosome(
                    chrom, self.orders, self.config, start_slot=self.start_slot
                )

            self.islands.append(population)

        # 初始化全局最优解
        for island in self.islands:
            for chrom in island:
                if self.best_chromosome is None or chrom.fitness > self.best_chromosome.fitness:
                    self.best_chromosome = chrom.copy()

    # ---------------------- 岛内操作辅助函数 ----------------------

    def _get_mutation_rate_for_island(self, island_type: str) -> float:
        base_rate = self.config.MUTATION_RATE
        if island_type == "explore":
            scale = float(getattr(self.config, "ISLAND_EXPLORATION_MUTATION_SCALE", 1.0))
            return min(1.0, max(0.0, base_rate * scale))
        return base_rate

    def _select_parents_for_island(self, population, island_type: str):
        parents = []
        base_tournament = 3
        if island_type == "profit":
            pressure = float(getattr(self.config, "ISLAND_PROFIT_SELECTION_PRESSURE", 1.0))
            tournament_size = max(2, int(round(base_tournament * pressure)))
        else:
            tournament_size = base_tournament

        for _ in range(len(population)):
            parent = GeneticOperators.tournament_selection(
                population, tournament_size=tournament_size
            )
            parents.append(parent)
        return parents

    def _create_offspring_for_island(self, parents, island_type: str):
        offspring = []
        mutation_rate = self._get_mutation_rate_for_island(island_type)

        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]

            # 交叉
            if random.random() < self.config.CROSSOVER_RATE:
                child1_gene1, child2_gene1 = GeneticOperators.crossover_gene1(
                    parent1, parent2
                )
                child1_gene2, child2_gene2 = GeneticOperators.crossover_gene2(
                    parent1, parent2
                )
                child1 = Chromosome(gene1=child1_gene1, gene2=child1_gene2)
                child2 = Chromosome(gene1=child2_gene1, gene2=child2_gene2)
            else:
                child1 = parent1.copy()
                child2 = parent2.copy()

            # 变异
            GeneticOperators.mutate_gene1(
                child1, mutation_rate, self.config.NUM_PRODUCTS
            )
            GeneticOperators.mutate_gene2(child1, mutation_rate)

            GeneticOperators.mutate_gene1(
                child2, mutation_rate, self.config.NUM_PRODUCTS
            )
            GeneticOperators.mutate_gene2(child2, mutation_rate)

            offspring.append(child1)
            offspring.append(child2)

        return offspring

    # ---------------------- 精英迁移 ----------------------

    def _migrate_elite(self):
        """在岛之间执行一次精英迁移（环形拓扑）。"""
        num_islands = len(self.islands)
        if num_islands <= 1:
            return

        elite_count_cfg = max(
            1, int(getattr(self.config, "ISLAND_MIGRATION_ELITE_COUNT", 1))
        )

        # 预先提取各岛精英
        elites_per_island = []
        for population in self.islands:
            if not population:
                elites_per_island.append([])
                continue
            sorted_pop = sorted(population, key=lambda c: c.fitness, reverse=True)
            k = min(elite_count_cfg, len(sorted_pop))
            elites_per_island.append([sorted_pop[i].copy() for i in range(k)])

        # 环形迁移：岛 i -> 岛 (i+1)
        for src_index in range(num_islands):
            elite_to_send = elites_per_island[src_index]
            if not elite_to_send:
                continue

            dst_index = (src_index + 1) % num_islands
            dst_population = self.islands[dst_index]
            if not dst_population:
                continue

            dst_sorted = sorted(dst_population, key=lambda c: c.fitness, reverse=True)
            k = min(len(elite_to_send), len(dst_sorted))
            if k == 0:
                continue

            # 保留较优个体，替换若干尾部个体为迁入精英
            keep = dst_sorted[:-k]
            new_pop = keep + [elite_to_send[i].copy() for i in range(k)]
            self.islands[dst_index] = new_pop

        if getattr(self.config, "DEBUG_ISLAND_GA", False):
            print("[IslandGA] 执行一次精英迁移")

    # ---------------------- 进化主过程 ----------------------

    def evolve(self):
        """执行多岛并行进化，返回全局最优解。"""
        max_generations = self.config.MAX_GENERATIONS
        no_improvement_count = 0

        num_islands = len(self.islands)
        if num_islands == 0:
            return None

        for generation in range(max_generations):
            # 岛内独立进化
            for island_index in range(num_islands):
                population = self.islands[island_index]
                if not population:
                    continue

                island_type = self._get_island_type(island_index)
                parents = self._select_parents_for_island(population, island_type)
                offspring = self._create_offspring_for_island(parents, island_type)

                # 计算后代适应度
                for child in offspring:
                    child.fitness = evaluate_chromosome(
                        child, self.orders, self.config, start_slot=self.start_slot
                    )

                # 精英保留 + 重新选择
                population.sort(key=lambda c: c.fitness, reverse=True)
                elite_size = getattr(self.config, "ELITE_SIZE", 5)
                elite = population[:elite_size]

                combined = elite + offspring
                combined.sort(key=lambda c: c.fitness, reverse=True)
                self.islands[island_index] = combined[: self.config.POPULATION_SIZE]

            # 精英迁移
            interval = int(getattr(self.config, "ISLAND_MIGRATION_INTERVAL", 20))
            if interval > 0 and (generation + 1) % interval == 0:
                self._migrate_elite()

            # 更新全局最优解
            generation_best = None
            for population in self.islands:
                for chrom in population:
                    if generation_best is None or chrom.fitness > generation_best.fitness:
                        generation_best = chrom

            if generation_best is not None:
                if self.best_chromosome is None or generation_best.fitness > self.best_chromosome.fitness:
                    self.best_chromosome = generation_best.copy()
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
            if self.best_chromosome is not None:
                self.global_best_history.append(self.best_chromosome.fitness)

            if getattr(self.config, "DEBUG_ISLAND_GA", False) and (generation + 1) % 10 == 0:
                print(
                    f"[IslandGA] 第 {generation + 1}/{max_generations} 代, "
                    f"全局最优适应度: {self.best_chromosome.fitness:.2f}"
                )

            # 提前终止条件：连续多代无改善（与单种群 GA 对齐，使用 20 代）
            if no_improvement_count >= 20:
                if getattr(self.config, "DEBUG_ISLAND_GA", False):
                    print(
                        f"[IslandGA] 第 {generation + 1} 代提前终止 (连续20代无改善)"
                    )
                break

        return self.best_chromosome
    
    def get_global_best_history(self):
        return getattr(self, "global_best_history", [])


def run_island_ga(orders, config, planning_horizon=None, start_slot=1):
    """便捷函数：运行岛模型并行遗传算法

    Args:
        orders: 订单列表
        config: 配置对象
        planning_horizon: 规划时域（slot 数量）
        start_slot: 当前规划窗口的起始 slot（1-based）

    Returns:
        Chromosome: 全局最优染色体
    """
    print("=" * 60)
    print("启动岛模型并行遗传算法...")
    print(f"岛数量: {getattr(config, 'NUM_ISLANDS', 1)}")
    print(f"种群规模: {config.POPULATION_SIZE}")
    print(f"最大迭代次数: {config.MAX_GENERATIONS}")
    print(f"交叉率: {config.CROSSOVER_RATE}")
    print(f"变异率: {config.MUTATION_RATE}")
    print(f"精英个体数: {config.ELITE_SIZE}")
    print(f"订单数量: {len(orders)}")
    print(f"规划窗口: 从 slot {start_slot} 开始，长度 {planning_horizon or '自动估算'}")
    print("=" * 60)

    engine = IslandGAEngine(
        config, orders, planning_horizon=planning_horizon, start_slot=start_slot
    )

    print("\n初始化各岛种群...")
    engine.initialize_islands()

    # 打印初始全局最优
    if engine.best_chromosome is not None:
        print(
            f"初始全局最优适应度: {engine.best_chromosome.fitness:.2f}"
        )

    print("\n开始多岛并行进化...\n")
    best_chromosome = engine.evolve()

    print("\n" + "=" * 60)
    print("岛模型遗传算法完成!")
    if best_chromosome is not None:
        print(f"最优适应度: {best_chromosome.fitness:.2f}")
    else:
        print("警告: 未获得有效解")
    print("=" * 60)

    return best_chromosome
