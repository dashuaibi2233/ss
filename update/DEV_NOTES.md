# DEV NOTES：岛模型 GA + 风险驱动局部搜索实现对齐

> 本文档面向开发者，记录“岛模型并行 GA + 风险驱动局部搜索”在现有代码结构上的落地方案与变更点。
> 所有说明均以 **不改变滚动调度主流程与对外接口** 为前提。

---

## 1. 现状盘点：模块职责与调用链

### 1.1 调度入口与整体流程

- **命令行入口**：`src/main.py`
  - 创建配置对象和 `OrderManager`，从 CSV 加载订单。
  - 构造滚动调度器，循环调用“每日 8:00 调度”，模拟多天生产。
  - 使用可视化模块输出甘特图与各类指标图表。

- **GUI 入口**：`gui_app.py`
  - 通过 `src/service.py` 暴露的接口加载默认配置与订单数据，运行多天滚动调度。
  - 在 Streamlit 界面中展示配置、运行状态与结果可视化，并提供导出功能。

- **服务层**：`src/service.py`
  - `load_default_config()`：构造并初始化配置对象（产能、成本、GA 参数、局部搜索参数）。
  - `load_orders()`：从 CSV 加载订单，返回 `OrderManager`。
  - `run_schedule(config, order_manager, num_days)`：
    - 重置订单状态；
    - 创建 `RollingScheduler`；
    - 循环调用 `run_daily_schedule(current_day)` 执行滚动调度；
    - 汇总生成 `SimulationResult`（按天记录财务与订单进度快照）。

### 1.2 滚动调度层

- **订单管理**：`src/scheduler/order_manager.py`
  - 维护订单集合与待处理列表；
  - 负责从 CSV 加载订单、根据当前时间生成可调度订单池（已到达且未完成）；
  - 提供 `time_to_slot(day, hour)` 辅助函数，将日期与时间映射到全局 slot。

- **调度器**：`src/scheduler/rolling_scheduler.py`
  - `run_daily_schedule(current_day)`：
    - 计算当前起始 slot（每天 8:00）；
    - 收集订单池（已到达且未完成）；
    - 冻结当前时间之前的 slot；
    - 调用 `run_optimization(orders, planning_horizon, start_slot)` 获取未来窗口内的优化方案；
    - 更新当前调度方案并执行当天生产，更新累计统计。
  - `run_optimization(...)`：
    - 阶段 1：调用 GA 引擎，获得一个最优染色体（单种群 GA）。
    - 阶段 2：使用 ILS/VNS 局部搜索，对 GA 结果做进一步改进。
    - 阶段 3：使用解码器生成 `Schedule`，并计算规划期内的收入、成本、罚款与利润。

- **调度结果模型**：`src/models/schedule.py`
  - 保存具体的分配方案 `allocation` 以及订单完成量与各类指标（收入、成本、罚款、利润）。
  - 提供按生产线/时间段的视图和统计方法。

### 1.3 GA 子系统

- **核心引擎**：`src/ga/engine.py`
  - `GAEngine`：实现单种群遗传算法的完整流程。
    - `initialize_population()`：
      - 按配置生成固定规模的染色体种群；
      - `Gene1` 表示产线-时间-产品结构；
      - `Gene2` 为订单优先级排列；
      - 使用适应度评估模块计算初始适应度。
    - `evolve()`：
      - 多代循环执行选择、交叉、变异、精英保留；
      - 通过“连续多代无改善”提前终止；
      - 最终返回单个“最优染色体”。
  - 便捷函数 `run_ga(...)`：
    - 封装 GA 引擎创建、初始化和进化过程；
    - 对外暴露为“输入订单集合 + 配置 → 输出一个最优染色体”的统一入口。

- **解码与适应度评估**：
  - `src/ga/decoder.py`：将染色体编码解码为具体调度方案（`Schedule`），考虑产能、订单窗口等约束。
  - `src/ga/fitness.py`：
    - 基于解码后的 `Schedule` 计算收入、成本、罚款与利润；
    - 暴露 `evaluate_chromosome(...)` 供 GA 引擎和局部搜索调用。

- **编码结构**：`src/models/chromosome.py`
  - `Chromosome`：包含 `gene1` / `gene2` 与 `fitness`，提供复制与校验方法。

### 1.4 局部搜索子系统

- **局部搜索实现**：`src/local_search/ils_vns.py`
  - `LocalSearch.optimize(...)`：在 GA 最优解附近执行 ILS/VNS：
    - 随机在两个邻域 `N1` / `N2` 间选择；
    - `N1`：随机选一条产线与两个时间段，交换 `Gene1` 中的产品类型；
    - `N2`：随机选两个订单位置，交换 `Gene2` 中的优先级；
    - 使用适应度评估模块重新评价；
    - 采用严格贪心接受策略（仅接受更优解），并基于“连续多次无改善”提前停止。
  - 便捷函数 `improve_solution(...)`：对 GA 最优解执行局部搜索，返回改进后的染色体。

### 1.5 配置对象与关键参数

- **配置类**：`src/config.py`
  - 生产线与时间维度：`NUM_LINES`、`NUM_PRODUCTS`、`SLOTS_PER_DAY`。
  - GA 参数：`POPULATION_SIZE`、`MAX_GENERATIONS`、`CROSSOVER_RATE`、`MUTATION_RATE`、`ELITE_SIZE`。
  - 局部搜索参数：`MAX_LS_ITERATIONS`。
  - 成本与罚款：`LABOR_COSTS`（slot 级人工成本）、`PENALTY_RATE`（违约罚款比例，当前为 10%）。
  - 产能：`CAPACITY`（产品到产能的映射）。

---

## 2. 升级点总览：需要新增/改造的模块

本次升级在不改变 **滚动调度触发方式 / 订单池构造 / 输出计划消费方式** 的前提下，集中改造：

- GA 层：从单种群扩展为 **岛模型并行 GA**，支持多岛异质进化与精英迁移，同时保留原单种群行为（可退化）。
- 局部搜索层：从“随机邻域 + 贪心接受”的通用 ILS/VNS，升级为 **风险驱动的定向局部搜索 + 受控退火接受**。

### 2.1 预计新增/改造的核心模块

> 以下为后续 Step 2 / Step 3 / Step 4 中将落地的改动规划，当前 Step 1 仅做设计与对齐，不做代码修改。

- **GA 模块相关**：
  - 在 GA 子系统中引入“多岛调度层”：
    - 方案 A：在 `src/ga/engine.py` 内新增一个面向多岛的控制类（暂定名为“岛模型 GA 引擎”），内部管理多个现有 GA 引擎实例，每个实例代表一个子种群（岛）。
    - 方案 B：在 `src/ga/island_engine.py` 新增独立模块，封装多岛逻辑；`run_ga(...)` 根据配置选择调用单种群 GA 或岛模型 GA。
  - 暂定采用 **方案 B**，以保持现有单种群 GA 引擎逻辑清晰、便于对比回归：
    - 原有 `GAEngine` 保持单种群实现不变；
    - 新增 `IslandGAEngine`（命名仅在实现文档中使用），负责：
      - 初始化多个岛的种群；
      - 轮询执行各岛的进化；
      - 在可配置的代数间隔执行精英迁移；
      - 输出跨岛选出的全局最优解。
    - `run_ga(...)` 内根据配置选择：
      - 关闭岛模型时：沿用原单种群 `GAEngine` 行为；
      - 开启岛模型时：使用 `IslandGAEngine` 内部运行多岛 GA。

- **局部搜索模块相关**：
  - 在现有 `LocalSearch` 类中：
    - 保留原有随机邻域实现作为“旧版局部搜索”路径，便于对比；
    - 新增“风险驱动局部搜索”路径：
      - 基于当前解与订单信息计算每个订单的风险分数；
      - 在高风险订单与高成本时段周围构造目标导向邻域；
      - 使用受控退火式接受策略替换纯贪心接受。
  - 滚动调度层通过配置开关选择：
    - 继续使用旧 ILS/VNS；
    - 或切换到“风险驱动局部搜索”实现。

- **滚动调度模块相关**：
  - `RollingScheduler.run_optimization(...)`：
    - 仍保持“先 GA → 再局部搜索 → 再解码”的整体流程与签名；
    - 内部改造为按配置选择：
      - 单种群 GA vs 岛模型 GA；
      - 传统局部搜索 vs 风险驱动局部搜索。

- **配置模块相关**：
  - 在 `Config` 中新增一组参数，用于：
    - 控制岛模型开关与岛结构；
    - 控制风险驱动局部搜索与退火接受策略；
    - 调整停止条件中的“无改进次数阈值”。

---

## 3. 新增配置项清单（设计阶段）

> 本节仅列出设计层面的配置项，具体默认值与放置位置将在 Step 2 / Step 3 实现时细化。命名以实际代码实现为准。

### 3.1 岛模型 GA 相关配置

- **基础开关与规模**：
  - `ENABLE_ISLAND_GA`：是否启用岛模型并行 GA（布尔）。
  - `NUM_ISLANDS`：岛的数量（整数，≥1）。
    - 约定：当 `ENABLE_ISLAND_GA=True` 且 `NUM_ISLANDS=1` 时，行为应与单种群 GA 等价（可视为退化模式）。

- **迁移机制**：
  - `ISLAND_MIGRATION_INTERVAL`：迁移周期（单位：GA 代数）。
  - `ISLAND_MIGRATION_ELITE_COUNT`：每个岛在单次迁移中输出的精英个体数量。
  - `ISLAND_MIGRATION_STRATEGY`：迁移拓扑与整合方式（例如："ring" / "all_to_all"），用于控制精英在岛之间的流动路径与注入策略。

- **异质岛类型与偏好**（三类核心岛）：
  - `ISLAND_TYPES`：岛类型列表，例如 `['profit', 'delivery', 'explore']`，用于映射到不同的参数偏好。
  - 针对各类型的参数调整因子：
    - 利润导向岛：
      - `ISLAND_PROFIT_SELECTION_PRESSURE`：选择压力放大系数（调节精英保留与高适应度个体的比例）。
    - 交付导向岛：
      - `ISLAND_DELIVERY_PENALTY_SCALE`：内部排序时对“未完成高金额订单”的惩罚放大因子，用于鼓励低违约率策略。
    - 探索导向岛：
      - `ISLAND_EXPLORATION_MUTATION_SCALE`：变异率放大因子，用于增加结构多样性。

> 说明：上述“*_SCALE” 参数不改变全局适应度定义（仍然是利润 = 收入 - 成本 - 罚款），只在各岛内部影响初始化/选择/变异等细节偏好，用于实现“利润/交付/探索”三类异质搜索风格。

### 3.2 风险驱动局部搜索相关配置

- **路径选择**：
  - `ENABLE_RISK_GUIDED_LS`：是否启用“风险驱动局部搜索 + 受控退火接受”路径。

- **风险评分相关参数**：
  - `RISK_WEIGHT_PENALTY_POTENTIAL`：潜在罚款金额在风险分数中的权重。
  - `RISK_WEIGHT_DEMAND_GAP`：需求缺口程度（已分配产能与总需求之差）在风险分数中的权重。
  - `RISK_WEIGHT_URGENCY`：截止紧迫度（距离截止时间的剩余窗口）在风险分数中的权重。
  - `RISK_THRESHOLD_HIGH`：高风险阈值（用于筛选需要优先处理的订单）。
  - `RISK_THRESHOLD_MEDIUM`：中风险阈值（用于区分一般订单与可适度关注的订单）。

> 计划中的风险分数结构（Step 3 中会给出正式定义）：
> - 潜在罚款：基于“订单数量 × 单价 × 罚款比例”；
> - 缺口程度：基于“需求量 - 已分配产能”的相对缺口；
> - 截止紧迫度：基于“剩余可用 slot 数与窗口长度”的函数。

- **邻域与搜索策略控制**：
  - `RISK_LS_MAX_ITER`：风险驱动局部搜索的最大迭代次数（可与现有 `MAX_LS_ITERATIONS` 对齐或替代）。
  - `RISK_LS_NO_IMPROVEMENT_LIMIT`：连续无改进次数阈值，超过后提前终止局部搜索。

- **受控退火接受相关参数**：
  - `ANNEALING_INIT_ACCEPT_PROB`：初始接受略差解的概率上限（例如 0.3）。
  - `ANNEALING_DECAY_RATE`：接受概率衰减系数（每次迭代或每若干次迭代后乘以一个小于 1 的系数）。
  - `ANNEALING_MIN_ACCEPT_PROB`：接受略差解的最小概率下限（例如 0.01），用于防止过早完全变为贪心。

> 上述参数仅作用在“局部搜索阶段的邻域解接受判定”中，不改变 GA 主过程的适应度评价逻辑。

### 3.3 停止条件与诊断相关参数

- **局部搜索停止条件微调**：
  - 在现有“连续 10 次无改善提前停止”的基础上，改用配置：
    - `LS_NO_IMPROVEMENT_LIMIT`：早停阈值，默认为旧值 10，以便保持旧行为可复现。

- **诊断与调试开关**（可选）：
  - 为后续调试留有空间，如：
    - `DEBUG_ISLAND_GA`：打印各岛最优值与迁移详情；
    - `DEBUG_RISK_LS`：输出高风险订单列表与局部搜索接受情况。

---

## 4. Step 1 小结（设计完成状态）

- 已梳理现有 GA / 局部搜索 / 滚动调度的调用链与关键数据结构：
  - 调度主入口 → 服务层 → 滚动调度器 → GA 引擎 → 局部搜索 → 解码与指标计算。
- 已明确后续升级中会涉及的新增/改造模块：
  - GA 子系统：增加“岛模型 GA 引擎”并在现有入口处挂接；
  - 局部搜索子系统：在现有类内部引入“风险驱动路径”；
  - 滚动调度与配置层：仅做最小改动以支持新路径与开关.
- 已给出岛模型 GA 与风险驱动局部搜索的**配置项清单草案**，后续 Step 2 / Step 3 将在实现时细化默认值并验证可退化与开关行为.

> 说明：本节完成后，下一步将在 `/update/ALGORITHM.md` 中以抽象语言补充“算法升级概述”，然后才进入实际代码实现.

## 5. Step 2：岛模型并行 GA 实现方案

本节在 Step 1 的设计基础上，给出岛模型并行 GA 的具体落地方案，明确：

- 新增/改造的模块与文件位置；
- 岛内进化与跨岛迁移的数据流和控制流；
- 三类异质岛（利润导向 / 交付导向 / 探索导向）的参数偏好；
- 与原单种群 GA 的兼容与可退化行为.

### 5.1 模块与入口改造

- 新增模块：`src/ga/island_engine.py`
  - 定义 `IslandGAEngine` 类：负责多岛种群的初始化、迭代进化与精英迁移；
  - 定义便捷函数 `run_island_ga(orders, config, planning_horizon, start_slot)`：
    - 对外接口与 `engine.run_ga(...)` 保持一致（输入订单集合 + 配置 + 规划窗口，输出最优染色体）。

- 入口选择逻辑（仍在 `src/ga/engine.py` 中实现）：
  - 保留原有 `GAEngine` 及 `run_ga(...)` 的签名和默认行为；
  - 在 `run_ga(...)` 内，根据配置选择执行路径：
    - 当 `config.ENABLE_ISLAND_GA` 为 `True` 且 `config.NUM_ISLANDS > 1` 时：
      - 调用 `run_island_ga(...)`，运行岛模型 GA；
    - 其他情况（包括 `ENABLE_ISLAND_GA=False` 或 `NUM_ISLANDS <= 1`）：
      - 走原有单种群 GAEngine 路径，行为与旧版本完全一致.

> 这样可保证：
> - 旧配置文件和调用代码在不修改任何参数的情况下行为不变；
> - 当仅将 `NUM_ISLANDS` 设为 1 时，即便开启岛模型开关，也会自动退化为与单种群等价的行为（由 `run_ga` 回落到原路径实现）。

### 5.2 岛内种群结构与初始化策略

- 岛列表：
  - `IslandGAEngine` 内部维护 `islands = List[List[Chromosome]]`，每个内层列表代表一个子种群（一个“岛”）。
  - 岛数量由 `config.NUM_ISLANDS` 控制，实际类型通过 `config.ISLAND_TYPES` 循环映射，例如 `["profit", "delivery", "explore"]` 周期性分配到各岛.

- 种群规模：
  - 每个岛使用与原 GA 相同的种群规模 `config.POPULATION_SIZE`；
  - 总体候选解数量为 `NUM_ISLANDS × POPULATION_SIZE`，通过参数控制在可接受范围内.

- 岛内初始化：
  - 时间与产线维度：
    - 与原 GA 一致，根据生产线数量与规划窗口长度确定编码长度；
  - 不同岛采用不同的启发式比例：
    - 利润导向岛：
      - 使用“随机个体 + 截止时间启发式个体”的混合方式，启发式比例与基线保持接近（偏向 EDD 但不过度集中）；
    - 交付导向岛：
      - 提高按照截止时间排序的个体比例，使更多初始个体天然倾向“早到期先生产”；
    - 探索导向岛：
      - 在保证可行性的前提下，增加随机性，例如更丰富的产品组合与订单排列，以刻意维持更大的结构多样性.

> 初始化阶段的差异主要体现在“种群起点”的多样性上，为后续岛内进化与跨岛迁移提供风格各异的候选解.

### 5.3 岛内进化流程与异质参数

在每一代进化中，`IslandGAEngine` 对每个岛独立执行与原 GA 相同的基本流程：

1. 选择：根据当前岛内种群适应度，使用锦标赛选择生成父代集合；
2. 交叉：对父代两两配对，按交叉概率产生子代；
3. 变异：对每个子代按变异概率在编码空间中做小扰动；
4. 精英保留：将岛内最优若干个体直接保留到下一代；
5. 适应度评估：使用统一的利润定义重新计算新一代个体的适应度.

为体现三类异质岛的参数偏好，在上述流程中引入轻量级差异：

  - 在父代选择时使用略高的选择压力：
    - 通过放大内部选择强度，使高适应度个体更容易被选为父代；
  - 目标：加速向高利润区域收敛，适合作为“短期利润极大化”的代表岛.

- **交付导向岛（delivery）**：
  - 在初始化阶段提高截止时间驱动的启发式比例，使更多个体天然倾向“早到期订单优先”；
  - 在后续可扩展为在父代选择时对违约风险较高的解施加额外惩罚（当前实现阶段先以初始化偏好为主，避免过度复杂）.

- **探索导向岛（explore）**：
  - 使用放大后的变异强度：在同等代数内探索更广的编码邻域；
  - 目标：牺牲部分收敛速度换取结构多样性，为其他岛提供新模式来源.

上述异质性均通过配置中的放大系数量化（如选择压力放大因子、变异放大因子），具体数值在配置文件中给出默认值，可按实验调优.

### 5.4 精英迁移策略与数据流

- 迁移触发：
  - 使用 `config.ISLAND_MIGRATION_INTERVAL` 控制迁移周期，例如每若干代执行一次迁移操作；
  - 当总代数尚未达到迁移周期时，各岛完全独立进化，不发生信息交换.

- 迁移内容：
  - 每个岛在当前代结束后选取若干最优个体作为本岛精英，数量由 `config.ISLAND_MIGRATION_ELITE_COUNT` 控制；
  - 为避免破坏岛内多样性，迁移数量通常远小于种群规模.

- 迁移拓扑（环形示意）：
  - 采用简单环形拓扑：
    - 岛 0 的精英迁入岛 1，岛 1 迁入岛 2，...，最后一个岛迁回岛 0；
  - 这样可以保证：
    - 每个岛既是“经验输出方”又是“经验接收方”；
    - 不同风格的策略在环上缓慢扩散，避免单次迁移导致全局同质化.

- 迁入方式：
  - 对于每个岛：
    - 在保留自身最优个体的前提下，将若干劣势个体替换为来自上游岛的精英副本；
  - 这样可以：
    - 避免直接覆盖本岛最优解，保护已有成果；
    - 同时为本岛引入新的候选结构，打破早熟收敛趋势.

### 5.5 全局最优解跟踪与可退化行为

- 全局最优跟踪：
  - `IslandGAEngine` 在每一代结束后，对所有岛的当前最优个体进行比较，更新一个全局最优解副本；
  - 终止条件与原 GA 保持一致（包括最大代数与连续若干代无改进提前终止），最终返回全局最优副本.

- 可退化行为：
  - 当 `ENABLE_ISLAND_GA=False` 时：
    - `run_ga(...)` 始终使用单种群 GAEngine，行为与原始版本完全一致；
  - 当 `ENABLE_ISLAND_GA=True` 但 `NUM_ISLANDS <= 1` 时：
    - 视作“未实际启用多岛结构”，`run_ga(...)` 仍然走单种群路径；
  - 因此：
    - 现有脚本与配置在不显式开启岛模型的情况下不会受到任何影响；
    - 将来若需要对比“单群体 vs 多岛”效果，只需在配置里调整一个布尔开关与岛数量即可.

### 5.6 Step 2 实现范围小结

- 本 Step 在实现上将完成：
  - 新增 `src/ga/island_engine.py` 并实现多岛初始化、进化与精英迁移；
  - 在 `src/ga/engine.py` 中扩展 `run_ga(...)`，根据配置路由到岛模型或单种群实现；
  - 在 `Config` 中增加岛模型相关参数，并设置合理默认值以保证旧行为不变；
  - 不改动滚动调度层的调用方式和对外接口.
- 与 `/update/ALGORITHM.md` 的对齐：
  - 本节对应算法说明中的“岛模型并行遗传算法”部分，负责将其中的机制描述具体映射到模块、配置与调用链层面.

## 6. Step 3：风险驱动局部搜索实现方案

本节在现有 ILS/VNS 实现基础上，给出“风险驱动局部搜索 + 受控退火接受”的具体落地方案，确保：

- 不改变滚动调度主流程（仍然是 GA → 局部搜索 → 解码）；
- 通过配置开关在“旧版随机邻域 + 贪心接受”和“新版风险驱动 + 退火接受”之间切换；
- 局部搜索只影响 GA 输出解附近的微调，不改变全局适应度定义（仍为利润）。

### 6.1 模块与入口改造

- 仍然在 `src/local_search/ils_vns.py` 中实现：
  - 保留现有 `LocalSearch` 类与便捷函数 `improve_solution(...)`：
    - 对外接口签名保持不变：`(chromosome, orders, config, start_slot)`；
    - 滚动调度层 `RollingScheduler.run_optimization(...)` 的调用方式不需改动。
  - 在 `LocalSearch.optimize(...)` 内新增路径分支：
    - 当 `config.ENABLE_RISK_GUIDED_LS` 为 `True` 时：
      - 调用“风险驱动局部搜索”内部实现；
    - 否则：
      - 调用原有“随机邻域 + 贪心接受”的 ILS/VNS 实现（提取为私有方法 `_optimize_greedy(...)`）。

> 这样可保证：
> - 旧配置文件和调用代码在不打开 `ENABLE_RISK_GUIDED_LS` 时，行为与旧版本 100% 一致；
> - 通过一个布尔开关即可在同一代码基础上对比“旧版局部搜索”和“风险驱动局部搜索”。

### 6.2 风险评分与高风险订单筛选

- 依托已有适应度评估模块 `ga.fitness.FitnessEvaluator`：
  - 在风险驱动路径中，不再仅调用 `evaluate_chromosome(...)`，而是调用 `evaluate_with_details(...)`：
    - 一次性获得当前解的利润值和对应的 `Schedule`（包含 `order_completion` 等信息）；
    - 在此基础上为每个订单计算风险分数。

- 风险分数计算逻辑（与 `/update/ALGORITHM.md` 中抽象描述对齐）：
  - 对每个订单，先计算：
    - `potential_penalty`：潜在罚款金额 = `quantity × unit_price × PENALTY_RATE`；
    - `completed_qty`：当前解下该订单在 `Schedule.order_completion` 中的完成量；
    - `remaining_demand`：`max(0, quantity - completed_qty)`；
    - `demand_gap_ratio`：若 `quantity > 0`，则为 `remaining_demand / quantity`，否则为 0；
    - `time_to_due`：`order.due_slot - start_slot`（当前滚动窗口起点到截止时间的剩余 slot 数）；
    - `urgency`：根据剩余时间归一化，越接近截止时间或已超期，值越大（例如：`urgency = 1 - clamp(time_to_due / planning_window, 0, 1)`）。
  - 归一化潜在罚款：
    - 在所有订单上取 `potential_penalty` 最大值 `max_p`，若为 0 则取 1；
    - `penalty_norm = potential_penalty / max_p`。
  - 综合风险分数：
    - `risk = w_p * penalty_norm + w_gap * demand_gap_ratio + w_u * urgency`；
    - 权重 `w_p` / `w_gap` / `w_u` 分别由 `RISK_WEIGHT_PENALTY_POTENTIAL`、`RISK_WEIGHT_DEMAND_GAP`、`RISK_WEIGHT_URGENCY` 提供，默认均为 1.0，可通过实验调整。
  - 对于已完全完成的订单（`remaining_demand <= 0`），直接将风险分数置为 0，避免被误判为高风险。

- 根据风险分数与阈值从订单集合中筛选：
  - `RISK_THRESHOLD_HIGH`：高风险阈值，用于构造高风险订单集合 `high_risk_orders`；
  - `RISK_THRESHOLD_MEDIUM`：中风险阈值，目前主要用于后续扩展，当前实现以高风险集合为主。

> 说明：
> - 风险分数仅用于指导局部搜索“优先调整哪些订单、哪些时间段”，不会直接修改适应度计算逻辑；
> - 通过 `DEBUG_RISK_LS` 开关，可以在控制台打印出排序后的高风险订单列表，辅助调试。

### 6.3 目标导向邻域：围绕高风险订单与时间段

在风险驱动路径下，仍沿用两个基本邻域类型（N1/N2），但内部选择策略从“完全随机”改为“围绕高风险订单和关键时段做偏置选择”：

- **风险邻域 N1（产线/时间维度，偏向高风险订单产品）**：
  - 目标：优先调整与高风险订单产品相关的产能分布，使其在接近截止时间前获得更多可用产能，或从高成本时段向更便宜的时段平移；
  - 实现方式（在 `LocalSearch` 内部新增私有方法）：
    - 从 `high_risk_orders` 中随机选一个高风险订单 `o`，记其产品为 `p`；
    - 在 `current_best.gene1` 中扫描所有位置 `(line, slot)`，找到满足：
      - 该位置产品为 `p`；
      - 对应的全局时间 `slot` 位于 `[o.release_slot, o.due_slot)` 窗口内；
    - 若候选位置不足，则退化为旧版随机 N1；
    - 否则，在这些候选位置中选一个作为“锚点”，再在同一条产线上选取另一个随机 slot，与之交换产品类型；
    - 这样可以在不破坏编码结构的前提下，优先对“有可能影响高风险订单”的时间段做调整。

- **风险邻域 N2（订单优先级维度，偏向高风险订单）**：
  - 目标：通过调整 `gene2` 中订单优先级的相对位置，让高风险订单在解码时更早地获得产能；
  - 实现方式：
    - 在 `gene2` 中找到所有对应高风险订单的下标位置集合 `positions_high`；
    - 若集合为空，则退化为旧版随机 N2（随机交换任意两个订单的位置）；
    - 否则，从 `positions_high` 中随机选一个索引 `i_high`，再在 `[0, i_high]` 区间内随机选一个较早的位置 `i_target`；
    - 交换 `gene2[i_high]` 与 `gene2[i_target]`，相当于将高风险订单整体往前“推一推”。

> 以上两个风险邻域都在保持原有编码与解码逻辑不变的前提下，引入了“高风险订单优先”的偏置，不需要改动解码模块。

### 6.4 受控退火接受策略

在风险驱动路径中，局部搜索不再使用“只接受更优解”的纯贪心策略，而是引入一个简单、可配置的退火式接受规则：

- 接受规则：
  - 若 `new_fitness >= current_fitness`：始终接受（与旧策略一致）；
  - 若 `new_fitness < current_fitness`：
    - 以一定概率接受略差解，概率由一个随迭代衰减的参数控制：
      - 初始值 `p_accept = ANNEALING_INIT_ACCEPT_PROB`（例如 0.3）；
      - 每次迭代后更新 `p_accept = max(ANNEALING_MIN_ACCEPT_PROB, p_accept * ANNEALING_DECAY_RATE)`；
      - 实际接受概率为 `p = clamp(p_accept, ANNEALING_MIN_ACCEPT_PROB, 1.0)`；
    - 当随机数 `< p` 时，即便新解略差也会被接受。

- 设计要点：
  - 退火只作用在“局部搜索是否接受略差解”这一点上，不改变适应度的定义；
  - 通过 `ANNEALING_INIT_ACCEPT_PROB` / `ANNEALING_DECAY_RATE` / `ANNEALING_MIN_ACCEPT_PROB` 三个参数，可以调节：
    - 初期探索强度（略差解可被接受的概率有多大）；
    - 探索期持续时间（概率衰减速度）；
    - 后期是否仍保留极低概率的跳出局部最优能力。
  - 当 `ENABLE_RISK_GUIDED_LS=False` 时，不会使用上述退火逻辑，保持旧有贪心策略。

### 6.5 停止条件与调试信息

- 停止条件：
  - 传统路径（贪心 ILS/VNS）：仍使用硬编码的“连续 10 次无改善提前停止”，后续可平滑迁移到 `LS_NO_IMPROVEMENT_LIMIT`；
  - 风险驱动路径：
    - 优先使用 `RISK_LS_NO_IMPROVEMENT_LIMIT`（若配置中存在）；
    - 否则退化为 `LS_NO_IMPROVEMENT_LIMIT` 或默认 10 次；
    - 条件触发时，在日志中打印“连续 N 次无改善/未接受，提前终止”。

- 调试信息：
  - 在风险驱动路径中，局部搜索日志会在启动时额外打印一行说明：
    - 例如：“使用风险驱动局部搜索 + 受控退火接受策略”；
  - 当 `DEBUG_RISK_LS=True` 时：
    - 可以在每次接受略差解时打印 Δfitness 与当时的接受概率；
    - 可选打印高风险订单列表（按风险分数排序），用于校验风险评分是否符合直觉。

### 6.6 Step 3 实现范围小结

- 本 Step 在实现上将完成：
  - 在 `LocalSearch.optimize(...)` 内增加路径分支，通过 `ENABLE_RISK_GUIDED_LS` 控制新旧局部搜索行为；
  - 基于 `FitnessEvaluator.evaluate_with_details(...)` 为每个订单计算风险分数，并据此构造高风险订单集合；
  - 在 Gene1 / Gene2 两个维度上引入围绕高风险订单的目标导向邻域；
  - 在局部搜索阶段内部实现受控退火接受策略，允许在早期以一定概率接受略差解；
  - 在 `Config` 中使用已预留的风险与退火相关参数，不再新增额外字段；
  - 可选在命令行入口 / 服务层入口中开启 `ENABLE_RISK_GUIDED_LS`，以便直接体验新版局部搜索效果。

## 7. Step 4：滚动调度集成与最小对比回归

本节在不改变滚动调度外观行为与对外接口的前提下，完成“岛模型 GA + 风险驱动局部搜索”的集成与最小可复现对比。

### 7.1 集成设计与改动点

- 滚动调度主流程保持不变：
  - `RollingScheduler.run_daily_schedule(...)` → `run_optimization(...)` → “GA → 局部搜索 → 解码/指标”。
- GA 与局部搜索的接入方式：
  - `run_optimization(...)` 仍调用 `ga.engine.run_ga(...)` 与 `local_search.ils_vns.improve_solution(...)`；
  - 新 GA/LS 通过 `Config` 的开关与参数在内部路由，无需改动滚动调度器的函数签名或调用链；
  - 开关与参数：
    - `ENABLE_ISLAND_GA`、`NUM_ISLANDS`、`ISLAND_MIGRATION_*`、`ISLAND_*_SCALE`；
    - `ENABLE_RISK_GUIDED_LS`、`RISK_WEIGHT_*`、`RISK_THRESHOLD_*`、`ANNEALING_*`、`RISK_LS_*`。
- 可退化与兼容性：
  - 未开启岛模型或 `NUM_ISLANDS <= 1` 时，`run_ga(...)` 自动走单种群路径；
  - 未开启风险驱动 LS 时，`LocalSearch.optimize(...)` 自动走旧版随机+贪心路径。

### 7.2 新增脚本与数据流

- 新增 `scripts/min_compare_old_vs_new.py`（最小对比回归脚本）：
  - 加载一份示例订单（默认 `data/sample_orders_small.csv`）；
  - 构造相同的 `start_slot` 与 `planning_horizon`（默认 `SLOTS_PER_DAY * 10`，与滚动调度一致）；
  - 运行两次优化：
    - 旧版：`ENABLE_ISLAND_GA=False`、`ENABLE_RISK_GUIDED_LS=False`；
    - 新版：`ENABLE_ISLAND_GA=True`（如 `NUM_ISLANDS=3`）、`ENABLE_RISK_GUIDED_LS=True`；
  - 两次均调用 `run_ga(...)` → `improve_solution(...)` → `Decoder.decode(...)` → `Schedule.calculate_metrics(...)`；
  - 输出对比指标：`profit/revenue/cost/penalty` 与 `on_time_rate/avg_completion_rate`；
  - 将摘要写入 `output/min_compare_*.txt`，便于复查与记录。

### 7.3 配置项示例（对比运行）

- 旧版（基线）：  
  - `ENABLE_ISLAND_GA=False`  
  - `ENABLE_RISK_GUIDED_LS=False`
- 新版（升级）：  
  - `ENABLE_ISLAND_GA=True`、`NUM_ISLANDS=3`、`ISLAND_MIGRATION_INTERVAL=20`、`ISLAND_MIGRATION_ELITE_COUNT=2`  
  - `ENABLE_RISK_GUIDED_LS=True`、`ANNEALING_INIT_ACCEPT_PROB=0.3`、`ANNEALING_DECAY_RATE=0.95`、`ANNEALING_MIN_ACCEPT_PROB=0.01`

### 7.4 影响范围

- 源码改动：
  - 无需改动滚动调度器与服务层接口，仅新增脚本；
  - 复用既有 GA/LS 的配置路由与实现。
- 文档改动：
  - 本文件新增 Step 4 章节；
  - `/update/ALGORITHM.md` 新增“效果与讨论”；
  - `/update/INDEX.md` 追加 Step 4 记录与复现说明。

### 7.5 验证方式

1. 在项目根目录执行：  
   `python scripts/min_compare_old_vs_new.py --data small`
2. 观察控制台输出与 `output/min_compare_*.txt`：
   - 对比旧版 vs 新版的 `profit/revenue/cost/penalty`；
   - 关注罚款与按期率的变化，验证风险驱动 LS 对高罚款场景的改善；
   - 记录运行参数与窗口设置，确保可复现。

