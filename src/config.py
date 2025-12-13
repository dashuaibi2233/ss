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
    
    # 岛模型 GA 参数（默认关闭，保持与单种群 GA 等价的行为）
    ENABLE_ISLAND_GA = False  # 是否启用岛模型并行 GA
    NUM_ISLANDS = 1  # 岛数量，=1 时退化为单种群
    ISLAND_MIGRATION_INTERVAL = 20  # 精英迁移周期（单位：GA 代数）
    ISLAND_MIGRATION_ELITE_COUNT = 2  # 每个岛在一次迁移中输出的精英个体数
    ISLAND_TYPES = ["profit", "delivery", "explore"]  # 岛类型轮换列表
    ISLAND_PROFIT_SELECTION_PRESSURE = 1.0  # 利润导向岛选择压力放大系数
    ISLAND_EXPLORATION_MUTATION_SCALE = 1.5  # 探索导向岛变异率放大系数
    # 交付导向岛在当前阶段主要通过初始化与排序体现偏好，预留权重参数便于后续扩展
    ISLAND_DELIVERY_PENALTY_SCALE = 1.0
    
    # 风险驱动局部搜索与受控退火（Step 3 使用，这里仅预留默认值）
    ENABLE_RISK_GUIDED_LS = False
    RISK_WEIGHT_PENALTY_POTENTIAL = 1.0
    RISK_WEIGHT_DEMAND_GAP = 1.0
    RISK_WEIGHT_URGENCY = 1.0
    RISK_THRESHOLD_HIGH = 0.7
    RISK_THRESHOLD_MEDIUM = 0.4
    RISK_LS_MAX_ITER = 50
    RISK_LS_NO_IMPROVEMENT_LIMIT = 10
    ANNEALING_INIT_ACCEPT_PROB = 0.3
    ANNEALING_DECAY_RATE = 0.95
    ANNEALING_MIN_ACCEPT_PROB = 0.01
    LS_NO_IMPROVEMENT_LIMIT = 10
    
    # 调试开关（默认关闭）
    DEBUG_ISLAND_GA = False
    DEBUG_RISK_LS = False
    
    # 策略开关
    ENABLE_STOPLOSS = False

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
