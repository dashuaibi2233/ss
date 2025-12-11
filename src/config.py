"""
系统配置模块

定义系统运行所需的全局参数和配置信息。
"""


class Config:
    """系统配置类"""
    
    # 生产线配置
    NUM_LINES = 3  # 生产线数量
    NUM_PRODUCTS = 3  # 产品种类数量
    SLOTS_PER_DAY = 6  # 每天的时间段数量（4小时/段）
    
    # GA 参数
    POPULATION_SIZE = 50  # 种群规模
    MAX_GENERATIONS = 100  # 最大迭代次数
    CROSSOVER_RATE = 0.8  # 交叉概率
    MUTATION_RATE = 0.1  # 变异概率
    ELITE_SIZE = 5  # 精英个体数量
    
    # 局部搜索参数
    MAX_LS_ITERATIONS = 50  # 局部搜索最大迭代次数
    
    # 成本参数
    LABOR_COSTS = []  # 各时间段人工成本，需根据实际情况配置
    PENALTY_RATE = 0.1  # 违约罚款比例
    
    # 产能参数
    CAPACITY = {}  # 各产品产能，格式: {product_id: capacity}
    
    def __init__(self):
        """初始化配置，设置默认参数"""
        # 设置默认产能参数
        self.CAPACITY = {
            1: 50,   # 产品1: 每slot产能50
            2: 60,   # 产品2: 每slot产能60
            3: 55,   # 产品3: 每slot产能55
        }
        
        # 设置默认人工成本（每个slot的成本）
        # 白班(8-20点): 100-115, 晚班(20-8点): 135-150
        labor_costs_per_day = [100, 100, 115, 135, 150, 140]  # 6个slot/天
        self.LABOR_COSTS = labor_costs_per_day * 10  # 10天
