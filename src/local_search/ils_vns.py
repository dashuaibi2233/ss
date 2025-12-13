"""
迭代局部搜索(ILS)和变邻域搜索(VNS)

在GA最优解基础上进行局部优化。
"""
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chromosome import Chromosome
from ga.fitness import evaluate_chromosome, FitnessEvaluator
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
    
    def optimize(self, initial_solution, orders, start_slot=1):
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
            start_slot: 当前规划窗口在全局时间轴上的起始 slot（1-based）
            
        Returns:
            Chromosome: 优化后的解
        """
        enable_risk_ls = bool(getattr(self.config, "ENABLE_RISK_GUIDED_LS", False))
        if enable_risk_ls:
            return self._optimize_risk_guided(initial_solution, orders, start_slot=start_slot)
        else:
            return self._optimize_greedy(initial_solution, orders, start_slot=start_slot)

    def _optimize_greedy(self, initial_solution, orders, start_slot=1):
        """旧版随机邻域 + 贪心接受的 ILS/VNS 实现"""
        current_best = initial_solution.copy()
        current_best.fitness = evaluate_chromosome(
            current_best, orders, self.config, start_slot=start_slot
        )

        max_iter = self.config.MAX_LS_ITERATIONS
        no_improvement_count = 0

        print(f"\n启动局部搜索 (ILS/VNS)...")
        print(f"初始适应度: {current_best.fitness:.2f}")

        for iteration in range(max_iter):
            # 随机选择邻域操作
            neighborhood_type = random.choice(["N1", "N2"])

            # 应用邻域操作生成新解
            if neighborhood_type == "N1":
                new_solution = self.neighborhood_swap_slots(current_best)
            else:  # N2
                new_solution = self.neighborhood_adjust_allocation(current_best, orders)

            # 计算新解的适应度
            new_solution.fitness = evaluate_chromosome(
                new_solution, orders, self.config, start_slot=start_slot
            )

            # 判断是否接受新解（贪心策略）
            if self.accept_solution(current_best.fitness, new_solution.fitness):
                current_best = new_solution
                no_improvement_count = 0
                print(
                    f"  第 {iteration + 1} 次迭代: 改善! 新适应度: {current_best.fitness:.2f} "
                    f"(使用 {neighborhood_type})"
                )
            else:
                no_improvement_count += 1

            # 早停：连续多次无改善（保持与旧实现一致）
            if no_improvement_count >= 10:
                print(f"  第 {iteration + 1} 次迭代提前终止 (连续10次无改善)")
                break

        print(f"局部搜索完成。最终适应度: {current_best.fitness:.2f}")
        print(f"改善程度: {current_best.fitness - initial_solution.fitness:.2f}\n")

        return current_best

    def _optimize_risk_guided(self, initial_solution, orders, start_slot=1):
        """风险驱动局部搜索 + 受控退火接受实现"""
        current_best = initial_solution.copy()
        current_best.fitness = evaluate_chromosome(
            current_best, orders, self.config, start_slot=start_slot
        )

        max_iter = int(getattr(self.config, "RISK_LS_MAX_ITER", self.config.MAX_LS_ITERATIONS))
        no_improvement_limit = int(
            getattr(
                self.config,
                "RISK_LS_NO_IMPROVEMENT_LIMIT",
                getattr(self.config, "LS_NO_IMPROVEMENT_LIMIT", 10),
            )
        )

        # 退火相关参数
        p_accept = float(getattr(self.config, "ANNEALING_INIT_ACCEPT_PROB", 0.3))
        decay = float(getattr(self.config, "ANNEALING_DECAY_RATE", 0.95))
        p_min = float(getattr(self.config, "ANNEALING_MIN_ACCEPT_PROB", 0.01))

        print(f"\n启动局部搜索 (ILS/VNS)...")
        print("使用风险驱动局部搜索 + 受控退火接受策略")
        print(f"初始适应度: {current_best.fitness:.2f}")

        evaluator = FitnessEvaluator(self.config)
        no_improvement_count = 0

        for iteration in range(max_iter):
            # 基于当前解构建调度方案与风险分数
            fitness_value, schedule = evaluator.evaluate_with_details(
                current_best, orders, start_slot=start_slot
            )
            current_best.fitness = fitness_value
            order_risks, high_risk_orders = self._compute_order_risks(
                schedule, orders, current_best, start_slot=start_slot
            )

            # 若没有明显高风险订单，则退化为随机邻域
            neighborhood_type = random.choice(["N1", "N2"])

            if neighborhood_type == "N1":
                new_solution = self._neighborhood_risk_N1(
                    current_best, high_risk_orders, start_slot=start_slot
                )
            else:
                new_solution = self._neighborhood_risk_N2(
                    current_best, orders, high_risk_orders
                )

            # 计算新解的适应度
            new_solution.fitness = evaluate_chromosome(
                new_solution, orders, self.config, start_slot=start_slot
            )

            # 使用退火式接受准则
            accepted, p_used = self._accept_with_annealing(
                current_best.fitness,
                new_solution.fitness,
                p_accept,
                p_min,
            )

            if accepted:
                delta = new_solution.fitness - current_best.fitness
                current_best = new_solution
                no_improvement_count = 0
                if delta >= 0:
                    print(
                        f"  第 {iteration + 1} 次迭代: 改善! 新适应度: {current_best.fitness:.2f} "
                        f"(使用 {neighborhood_type})"
                    )
                else:
                    if getattr(self.config, "DEBUG_RISK_LS", False):
                        print(
                            f"  第 {iteration + 1} 次迭代: 接受略差解 Δ={delta:.2f}, "
                            f"当前退火接受概率≈{p_used:.3f} (使用 {neighborhood_type})"
                        )
            else:
                no_improvement_count += 1

            # 调整退火概率
            p_accept = max(p_min, p_accept * decay)

            # 可选调试：打印高风险订单列表
            if getattr(self.config, "DEBUG_RISK_LS", False) and iteration == 0:
                # 仅在首轮打印一次，避免日志过多
                sorted_risks = sorted(
                    order_risks.items(), key=lambda kv: kv[1], reverse=True
                )
                top_k = sorted_risks[:5]
                if top_k:
                    print("  [RiskLS] 高风险订单Top列表 (order_id, risk):")
                    for order_id, risk in top_k:
                        print(f"    - {order_id}: {risk:.3f}")

            # 早停：连续多次未接受新解
            if no_improvement_count >= no_improvement_limit:
                print(
                    f"  第 {iteration + 1} 次迭代提前终止 "
                    f"(连续{no_improvement_count}次未接受新解)"
                )
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
    
    def _compute_order_risks(self, schedule, orders, chromosome, start_slot=1):
        """基于当前解对应的调度方案，计算每个订单的风险分数并筛选高风险订单。"""
        # 估算规划窗口长度（用于计算紧迫度）： 
        num_lines = self.config.NUM_LINES
        if num_lines <= 0:
            num_slots = len(chromosome.gene1)
        else:
            num_slots = len(chromosome.gene1) // num_lines
        planning_horizon = max(1, num_slots)

        # 计算潜在罚款最大值，用于归一化
        potential_penalties = []
        for order in orders:
            potential = (
                order.quantity * order.unit_price * self.config.PENALTY_RATE
            )
            potential_penalties.append(potential)
        max_potential = max(potential_penalties) if potential_penalties else 1.0
        if max_potential <= 0:
            max_potential = 1.0

        w_p = float(getattr(self.config, "RISK_WEIGHT_PENALTY_POTENTIAL", 1.0))
        w_gap = float(getattr(self.config, "RISK_WEIGHT_DEMAND_GAP", 1.0))
        w_u = float(getattr(self.config, "RISK_WEIGHT_URGENCY", 1.0))

        order_risks = {}
        high_risk_orders = []
        high_threshold = float(getattr(self.config, "RISK_THRESHOLD_HIGH", 0.7))

        for order in orders:
            completed_qty = schedule.order_completion.get(order.order_id, 0)
            remaining = max(0, order.quantity - completed_qty)

            if order.quantity > 0:
                gap_ratio = remaining / order.quantity
            else:
                gap_ratio = 0.0

            potential_penalty = (
                order.quantity * order.unit_price * self.config.PENALTY_RATE
            )
            penalty_norm = potential_penalty / max_potential if max_potential > 0 else 0.0

            # 截止紧迫度：剩余可用slot越少，紧迫度越高
            time_to_due = order.due_slot - start_slot
            time_to_due_clipped = min(max(time_to_due, 0), planning_horizon)
            urgency = 1.0 - (time_to_due_clipped / planning_horizon)

            if remaining <= 0:
                # 已完成订单风险记为0
                risk = 0.0
            else:
                risk = w_p * penalty_norm + w_gap * gap_ratio + w_u * urgency

            order_risks[order.order_id] = risk
            if risk >= high_threshold:
                high_risk_orders.append(order)

        # 若没有订单超过高风险阈值，则选择风险最高的若干订单作为候选
        if not high_risk_orders and order_risks:
            sorted_orders = sorted(
                orders, key=lambda o: order_risks.get(o.order_id, 0.0), reverse=True
            )
            top_k = min(3, len(sorted_orders))
            high_risk_orders = sorted_orders[:top_k]

        return order_risks, high_risk_orders

    def _neighborhood_risk_N1(self, chromosome, high_risk_orders, start_slot=1):
        """风险导向的 N1 邻域：优先调整与高风险订单产品相关的 (line, slot)。"""
        # 如果没有明显高风险订单，则退化为原始 N1
        if not high_risk_orders:
            return self.neighborhood_swap_slots(chromosome)

        neighbor = chromosome.copy()

        num_lines = self.config.NUM_LINES
        if num_lines <= 0 or len(neighbor.gene1) == 0:
            return neighbor

        num_slots = len(neighbor.gene1) // num_lines
        if num_slots <= 0:
            return neighbor

        # 收集所有与高风险订单产品相关且处于其时间窗口内的位置
        candidate_indices = []  # (gene_idx, line_idx, slot_idx)
        for order in high_risk_orders:
            product = order.product
            for line_idx in range(num_lines):
                for slot_idx in range(num_slots):
                    gene_idx = line_idx * num_slots + slot_idx
                    if neighbor.gene1[gene_idx] != product:
                        continue
                    global_slot = start_slot + slot_idx
                    if order.release_slot <= global_slot < order.due_slot:
                        candidate_indices.append((gene_idx, line_idx, slot_idx))

        if not candidate_indices:
            # 若找不到满足条件的位置，退化为原始 N1
            return self.neighborhood_swap_slots(chromosome)

        # 从候选中随机选择一个锚点，再在同一条产线上随机选择另一个slot与之交换
        gene_idx1, line_idx, _ = random.choice(candidate_indices)
        slot2_idx = random.randint(0, num_slots - 1)
        gene_idx2 = line_idx * num_slots + slot2_idx

        neighbor.gene1[gene_idx1], neighbor.gene1[gene_idx2] = (
            neighbor.gene1[gene_idx2],
            neighbor.gene1[gene_idx1],
        )

        return neighbor

    def _neighborhood_risk_N2(self, chromosome, orders, high_risk_orders):
        """风险导向的 N2 邻域：优先将高风险订单在优先级序列中前移。"""
        neighbor = chromosome.copy()

        if len(neighbor.gene2) < 2:
            return neighbor

        if not high_risk_orders:
            # 没有高风险订单时退化为原始 N2
            return self.neighborhood_adjust_allocation(chromosome, orders)

        # 构建 order_id -> index 映射，方便定位订单索引
        order_index_map = {order.order_id: idx for idx, order in enumerate(orders)}
        high_indices = set()
        for order in high_risk_orders:
            idx = order_index_map.get(order.order_id)
            if idx is not None:
                high_indices.add(idx)

        positions_high = [
            i for i, order_idx in enumerate(neighbor.gene2) if order_idx in high_indices
        ]

        if not positions_high:
            # 若当前编码中找不到高风险订单，退化为随机 N2
            return self.neighborhood_adjust_allocation(chromosome, orders)

        i_high = random.choice(positions_high)
        if i_high <= 0:
            return neighbor

        i_target = random.randint(0, i_high)
        neighbor.gene2[i_high], neighbor.gene2[i_target] = (
            neighbor.gene2[i_target],
            neighbor.gene2[i_high],
        )

        return neighbor

    def _accept_with_annealing(self, current_fitness, new_fitness, p_accept, p_min):
        """退火式接受准则：返回(是否接受, 实际使用的接受概率)。"""
        if new_fitness >= current_fitness:
            return True, 1.0

        # 对略差解使用当前退火接受概率（限制在 [p_min, 1.0]）
        p_used = max(p_min, min(1.0, p_accept))
        r = random.random()
        if r < p_used:
            return True, p_used
        return False, p_used

    def accept_solution(self, current_fitness, new_fitness):
        """
        判断是否接受新解
        
        局部搜索采用贪心策略：只接受更优的解.
        
        Args:
            current_fitness: 当前解适应度
            new_fitness: 新解适应度
            
        Returns:
            bool: 是否接受
        """
        # 贪心策略：只接受更优的解
        return new_fitness > current_fitness


# 便捷函数：供外部直接调用
def improve_solution(chromosome, orders, config, start_slot=1):
    """
    改进解（便捷函数）
    
    这是一个独立的函数，方便外部模块直接调用局部搜索。
    接受 GA 的最优解，基于 ILS/VNS 进行局部优化。
    
    Args:
        chromosome: 初始染色体（GA最优解）
        orders: 订单列表 (List[Order])
        config: 配置对象，包含局部搜索参数
        start_slot: 当前规划窗口在全局时间轴上的起始 slot（1-based）
        
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
    improved = local_search.optimize(chromosome, orders, start_slot=start_slot)
    return improved
