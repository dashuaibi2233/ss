"""
遗传算法操作算子

实现选择、交叉、变异等遗传操作。
"""
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chromosome import Chromosome


class GeneticOperators:
    """
    遗传操作算子类
    
    提供选择、交叉、变异等遗传算法基本操作。
    """
    
    @staticmethod
    def tournament_selection(population, tournament_size=3):
        """
        锦标赛选择
        
        从种群中随机选取 tournament_size 个个体，返回其中适应度最高的个体。
        
        Args:
            population: 种群 (List[Chromosome])
            tournament_size: 锦标赛规模，默认3
            
        Returns:
            Chromosome: 选中的个体
        """
        if not population:
            return None
        
        # 随机选取 tournament_size 个个体
        tournament_size = min(tournament_size, len(population))
        tournament = random.sample(population, tournament_size)
        
        # 返回适应度最高的个体
        return max(tournament, key=lambda x: x.fitness)
    
    @staticmethod
    def roulette_selection(population):
        """
        轮盘赌选择（适应度比例选择）
        
        根据个体的适应度比例进行选择，适应度越高被选中的概率越大。
        
        Args:
            population: 种群 (List[Chromosome])
            
        Returns:
            Chromosome: 选中的个体
        """
        if not population:
            return None
        
        # 计算总适应度（处理负值情况）
        min_fitness = min(ind.fitness for ind in population)
        if min_fitness < 0:
            # 如果有负值，将所有适应度平移到正值
            adjusted_fitness = [ind.fitness - min_fitness + 1 for ind in population]
        else:
            adjusted_fitness = [ind.fitness for ind in population]
        
        total_fitness = sum(adjusted_fitness)
        
        if total_fitness <= 0:
            # 如果总适应度为0，随机选择
            return random.choice(population)
        
        # 轮盘赌选择
        pick = random.uniform(0, total_fitness)
        current = 0
        for i, ind in enumerate(population):
            current += adjusted_fitness[i]
            if current >= pick:
                return ind
        
        # 容错处理
        return population[-1]
    
    @staticmethod
    def crossover_gene1(parent1, parent2):
        """
        Gene1的交叉操作（单点交叉）
        
        按时间轴切片，在随机位置进行单点交叉。
        
        Args:
            parent1: 父代1 (Chromosome)
            parent2: 父代2 (Chromosome)
            
        Returns:
            tuple: (子代1_gene1, 子代2_gene1) - 两个新的 gene1 列表
        """
        if not parent1.gene1 or not parent2.gene1:
            return parent1.gene1[:], parent2.gene1[:]
        
        length = len(parent1.gene1)
        if length != len(parent2.gene1):
            return parent1.gene1[:], parent2.gene1[:]
        
        # 随机选择交叉点
        crossover_point = random.randint(1, length - 1)
        
        # 生成子代
        child1_gene1 = parent1.gene1[:crossover_point] + parent2.gene1[crossover_point:]
        child2_gene1 = parent2.gene1[:crossover_point] + parent1.gene1[crossover_point:]
        
        return child1_gene1, child2_gene1
    
    @staticmethod
    def crossover_gene2_ox(parent1, parent2):
        """
        Gene2的OX（顺序交叉）操作
        
        保证子代仍为合法的订单排列。
        
        Args:
            parent1: 父代1 (Chromosome)
            parent2: 父代2 (Chromosome)
            
        Returns:
            tuple: (子代1_gene2, 子代2_gene2)
        """
        if not parent1.gene2 or not parent2.gene2:
            return parent1.gene2[:], parent2.gene2[:]
        
        length = len(parent1.gene2)
        if length != len(parent2.gene2) or length < 2:
            return parent1.gene2[:], parent2.gene2[:]
        
        # 随机选择两个交叉点
        point1 = random.randint(0, length - 1)
        point2 = random.randint(0, length - 1)
        if point1 > point2:
            point1, point2 = point2, point1
        
        # 创建子代1
        child1 = [-1] * length
        child1[point1:point2+1] = parent1.gene2[point1:point2+1]
        
        # 从 parent2 中按顺序填充剩余元素
        pos = (point2 + 1) % length
        for gene in parent2.gene2[point2+1:] + parent2.gene2[:point2+1]:
            if gene not in child1:
                child1[pos] = gene
                pos = (pos + 1) % length
        
        # 创建子代2
        child2 = [-1] * length
        child2[point1:point2+1] = parent2.gene2[point1:point2+1]
        
        pos = (point2 + 1) % length
        for gene in parent1.gene2[point2+1:] + parent1.gene2[:point2+1]:
            if gene not in child2:
                child2[pos] = gene
                pos = (pos + 1) % length
        
        return child1, child2
    
    @staticmethod
    def crossover_gene2(parent1, parent2):
        """
        Gene2的交叉操作（默认使用OX交叉）
        
        Args:
            parent1: 父代1
            parent2: 父代2
            
        Returns:
            tuple: (子代1_gene2, 子代2_gene2)
        """
        return GeneticOperators.crossover_gene2_ox(parent1, parent2)
    
    @staticmethod
    def mutate_gene1(chromosome, mutation_rate, num_products=3):
        """
        Gene1的变异操作
        
        随机选择若干基因位置，将产品类型改为其他合法值 {0,1,2,3}。
        
        Args:
            chromosome: 染色体 (Chromosome)
            mutation_rate: 变异概率
            num_products: 产品种类数，默认3
        """
        for i in range(len(chromosome.gene1)):
            if random.random() < mutation_rate:
                # 随机选择一个新的产品类型 (0=空闲, 1/2/3=产品)
                chromosome.gene1[i] = random.randint(0, num_products)
    
    @staticmethod
    def mutate_gene2(chromosome, mutation_rate):
        """
        Gene2的变异操作（swap 交换变异）
        
        随机交换两个订单编号的位置。
        
        Args:
            chromosome: 染色体 (Chromosome)
            mutation_rate: 变异概率
        """
        if len(chromosome.gene2) < 2:
            return
        
        if random.random() < mutation_rate:
            # 随机选择两个不同的位置
            idx1 = random.randint(0, len(chromosome.gene2) - 1)
            idx2 = random.randint(0, len(chromosome.gene2) - 1)
            
            # 交换
            chromosome.gene2[idx1], chromosome.gene2[idx2] = chromosome.gene2[idx2], chromosome.gene2[idx1]
