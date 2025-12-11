# 系统架构文档

## 系统概述

智能制造生产调度系统采用模块化设计，基于《设计大纲.md》第4章的软件架构方案实现。

系统分为6个核心模块，各模块职责清晰，通过标准接口协作完成调度任务。

---

## 1. 模块结构

### 1.1 数据模型模块 (`models/`)

**职责**：定义系统核心数据结构

**主要类：**

#### `Order` (order.py)
订单数据类
- **属性**：
  - `order_id`: 订单编号
  - `product`: 产品类型 (1/2/3)
  - `quantity`: 需求数量
  - `remaining`: 剩余未完成数量
  - `due_slot`: 截止时间（slot索引）
  - `unit_price`: 单位售价
- **方法**：
  - `update_remaining()`: 更新剩余数量
  - `is_completed()`: 检查是否完成

#### `Chromosome` (chromosome.py)
染色体编码类
- **属性**：
  - `gene1`: 产线-时间-产品结构编码（长度 3×H）
  - `gene2`: 订单优先级排列（长度 N）
  - `fitness`: 适应度值
- **方法**：
  - `copy()`: 深拷贝染色体

#### `Schedule` (schedule.py)
调度方案类
- **属性**：
  - `allocation`: 订单分配方案 {(order_id, line, slot): quantity}
  - `order_completion`: 订单完成量统计
  - `revenue`, `cost`, `penalty`, `profit`: 各项指标
- **方法**：
  - `add_allocation()`: 添加订单分配
  - `calculate_metrics()`: 计算各项指标
  - `get_line_schedule()`: 获取指定生产线的调度

---

### 1.2 遗传算法模块 (`ga/`)

**职责**：实现遗传算法的核心功能

#### `GAEngine` (engine.py)
GA主引擎
- **职责**：种群管理、进化流程控制
- **主要方法**：
  - `initialize_population()`: 初始化种群
  - `evolve()`: 执行进化过程
  - `select_parents()`: 选择父代
  - `create_next_generation()`: 创建下一代
  - `get_best_solution()`: 获取最优解

#### `GeneticOperators` (operators.py)
遗传操作算子
- **职责**：提供选择、交叉、变异操作
- **主要方法**：
  - `tournament_selection()`: 锦标赛选择
  - `roulette_selection()`: 轮盘赌选择
  - `crossover_gene1()`: Gene1交叉
  - `crossover_gene2()`: Gene2交叉（OX/PMX）
  - `mutate_gene1()`: Gene1变异
  - `mutate_gene2()`: Gene2变异（Swap）

#### `Decoder` (decoder.py)
染色体解码器
- **职责**：将染色体转换为调度方案
- **主要方法**：
  - `decode()`: 解码染色体
  - `calculate_available_capacity()`: 计算可用产能
  - `allocate_orders()`: 按优先级分配订单

#### `FitnessEvaluator` (fitness.py)
适应度评估器
- **职责**：计算染色体适应度
- **主要方法**：
  - `evaluate()`: 评估适应度
  - `calculate_revenue()`: 计算收入
  - `calculate_cost()`: 计算成本
  - `calculate_penalty()`: 计算罚款

---

### 1.3 局部搜索模块 (`local_search/`)

**职责**：对GA解进行局部优化

#### `LocalSearch` (ils_vns.py)
局部搜索类
- **职责**：实现ILS/VNS算法
- **主要方法**：
  - `optimize()`: 执行局部搜索
  - `neighborhood_swap_slots()`: 邻域N1（交换时间段产品）
  - `neighborhood_adjust_allocation()`: 邻域N2（微调订单分配）
  - `accept_solution()`: 判断是否接受新解

---

### 1.4 调度器模块 (`scheduler/`)

**职责**：订单管理和滚动调度

#### `OrderManager` (order_manager.py)
订单管理器
- **职责**：订单池维护、订单CRUD操作
- **主要方法**：
  - `add_order()`: 添加订单
  - `remove_order()`: 移除订单
  - `get_pending_orders()`: 获取待处理订单
  - `update_order_status()`: 更新订单状态
  - `load_orders_from_csv()`: 从CSV加载订单
  - `time_to_slot()`: 时间戳转slot索引

#### `RollingScheduler` (rolling_scheduler.py)
滚动调度器
- **职责**：每日调度触发和执行
- **主要方法**：
  - `daily_schedule()`: 执行每日调度
  - `freeze_executed_slots()`: 冻结已执行时间段
  - `run_optimization()`: 运行优化算法
  - `update_schedule()`: 更新调度方案
  - `get_current_schedule()`: 获取当前方案

---

### 1.5 可视化模块 (`visualization/`)

**职责**：结果展示和性能分析

#### `GanttChart` (gantt.py)
甘特图生成器
- **职责**：生成生产调度甘特图
- **主要方法**：
  - `plot_schedule()`: 绘制完整甘特图
  - `plot_line_schedule()`: 绘制单条生产线甘特图
  - `customize_colors()`: 自定义颜色映射

#### `MetricsVisualizer` (metrics.py)
指标可视化器
- **职责**：生成性能指标图表
- **主要方法**：
  - `plot_profit_breakdown()`: 利润分解图
  - `plot_order_completion_rate()`: 订单完成率
  - `plot_line_utilization()`: 生产线利用率
  - `plot_ga_convergence()`: GA收敛曲线
  - `generate_report()`: 生成综合报告

---

### 1.6 配置模块 (`config.py`)

**职责**：系统参数集中管理

**主要配置项：**
- 生产线配置：生产线数量、产品种类、时间段划分
- GA参数：种群规模、迭代次数、交叉/变异概率、精英数量
- 局部搜索参数：最大迭代次数
- 成本参数：人工成本、罚款比例
- 产能参数：各产品产能上限

---

## 2. 模块调用关系

### 2.1 调用层次

```
main.py (主程序)
    ↓
RollingScheduler (滚动调度器)
    ↓
    ├─→ OrderManager (订单管理器)
    ├─→ GAEngine (GA引擎)
    │       ↓
    │       ├─→ GeneticOperators (遗传操作)
    │       ├─→ Decoder (解码器)
    │       └─→ FitnessEvaluator (适应度评估)
    ├─→ LocalSearch (局部搜索)
    └─→ Visualization (可视化)
            ├─→ GanttChart
            └─→ MetricsVisualizer
```

### 2.2 数据流向

```
CSV订单文件
    ↓
OrderManager.load_orders_from_csv()
    ↓
Order对象列表
    ↓
RollingScheduler.daily_schedule()
    ↓
GAEngine.evolve() → Chromosome种群
    ↓
Decoder.decode() → Schedule对象
    ↓
FitnessEvaluator.evaluate() → fitness值
    ↓
LocalSearch.optimize() → 优化后的Chromosome
    ↓
最终Schedule对象
    ↓
Visualization.plot_*() → 图表和报告
```

---

## 3. 主运行流程

### 3.1 系统初始化

```python
# main.py
1. 加载配置参数 (Config)
2. 创建订单管理器 (OrderManager)
3. 从CSV加载订单数据
4. 创建滚动调度器 (RollingScheduler)
5. 创建可视化器 (GanttChart, MetricsVisualizer)
```

### 3.2 每日调度流程

```python
for 每一天:
    if 当前时间 == 8:00:
        # 1. 订单管理
        order_manager.update_order_pool()
        pending_orders = order_manager.get_pending_orders()
        
        # 2. 滚动调度
        scheduler.freeze_executed_slots(current_slot)
        
        # 3. GA优化
        ga_engine = GAEngine(config, pending_orders)
        ga_engine.initialize_population()
        best_chromosome = ga_engine.evolve()
        
        # 4. 局部搜索
        local_search = LocalSearch(config)
        optimized_solution = local_search.optimize(best_chromosome, pending_orders)
        
        # 5. 生成调度方案
        decoder = Decoder(config)
        final_schedule = decoder.decode(optimized_solution, pending_orders)
        
        # 6. 更新和可视化
        scheduler.update_schedule(final_schedule)
        gantt.plot_schedule(final_schedule)
        metrics.generate_report(final_schedule, pending_orders)
    
    # 执行当前时间段的生产
    execute_production(current_slot)
```

### 3.3 GA进化流程（详细）

```python
# GAEngine.evolve()
population = initialize_population()

for generation in range(MAX_GENERATIONS):
    # 评估适应度
    for chromosome in population:
        schedule = decoder.decode(chromosome, orders)
        chromosome.fitness = fitness_evaluator.evaluate(schedule)
    
    # 选择
    parents = select_parents(population)
    
    # 交叉
    offspring = []
    for i in range(0, len(parents), 2):
        child1, child2 = operators.crossover(parents[i], parents[i+1])
        offspring.extend([child1, child2])
    
    # 变异
    for child in offspring:
        operators.mutate(child)
    
    # 精英保留
    population = elitism(population, offspring)
    
    # 检查终止条件
    if converged():
        break

return get_best_chromosome(population)
```

---

## 4. 关键设计模式

- **策略模式**：不同的选择、交叉、变异算子可互换
- **工厂模式**：染色体初始化支持多种策略
- **观察者模式**：GA进化过程可记录收敛历史
- **单例模式**：配置对象全局唯一

---

## 5. 扩展性设计

- **新增产品类型**：修改 `Config.NUM_PRODUCTS`
- **新增生产线**：修改 `Config.NUM_LINES`
- **新增邻域操作**：在 `LocalSearch` 中添加新方法
- **新增可视化**：在 `visualization/` 中添加新类
- **新增对比算法**：实现新的调度器类继承基类

---

## 6. 参考

详细模块说明请参考《设计大纲.md》第4章。
