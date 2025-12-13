# /update 文档索引与版本记录

> 本文件用于：
> - 维护 `/update` 目录下文档与 `docs/` 目录中原始文档之间的映射关系；
> - 记录每一次算法升级相关变更的 Step、内容与验证方式；
> - 作为后续阅读 `/update/ALGORITHM.md` 与 `/update/DEV_NOTES.md` 的导航入口。

---

## 1. 文档映射关系

- **`/update/ALGORITHM.md`**
  - 角色：升级版算法说明文档（面向课程论文与高层设计）。
  - 与原文关系：
    - 作为 `docs/ALGORITHM.md` 中算法设计章节（整体框架、问题建模、遗传算法与局部搜索描述）的升级替代版本；
    - 所有关于“算法机制/流程层面”的说明以后以 `/update/ALGORITHM.md` 为准，`docs/ALGORITHM.md` 保留为历史基线参考。

- **`/update/ALGORITHM_UPDATE.md`**
  - 角色：聚焦“从单种群 GA + 随机 ILS/VNS 升级到 岛模型并行 GA + 风险驱动局部搜索”的专门解释文档；
  - 与原文关系：
    - 补充说明 `docs/ALGORITHM.md` 与 `/update/ALGORITHM.md` 之间的演进关系；
    - 强调升级动机、两条升级方向及其在系统中的定位，不直接承担完整算法说明职责。

- **`/update/DEV_NOTES.md`**
  - 角色：实现对齐与开发笔记文档（面向开发者）。
  - 与原文关系：
    - 对应并细化 `docs/ALGORITHM.md` 中隐含的实现假设与调用链说明；
    - 记录模块职责、接口约定、新增配置项以及每一步实现的影响范围。

> 后续如在 `/update` 下新增其他文档（例如实验记录、参数调优说明），需在本节增加对应映射说明。

---

## 2. 版本记录（按 Step 递增）

> 约定：每完成一个 Step，必须在此追加一条记录，说明：
> - Step 编号与简要标题；
> - 主要修改文档与代码范围；
> - 验证方式与可复现运行说明（如适用）。

### Step 1（设计阶段）：现状盘点 + 落地设计

- **日期**：2025-12-13
- **状态**：已完成（纯文档更新，无代码改动）。
- **涉及文档**：
  - 新增 `/update/DEV_NOTES.md`：
    - 梳理现有 GA / 局部搜索 / 滚动调度的模块职责与调用链；
    - 初步列出岛模型 GA 与风险驱动局部搜索涉及的新增/改造模块；
    - 给出岛数量、迁移周期、迁移精英数、岛类型参数、风险阈值、退火参数等配置项的设计草案。
  - 新增 `/update/ALGORITHM.md`：
    - 以抽象语言给出“算法升级概述”，明确两条升级方向：
      - 岛模型并行遗传算法（增强全局搜索与多样性）；
      - 风险驱动的定向局部搜索（结合罚款跳变与成本结构）。
    - 不包含任何具体代码或实现细节。
  - `/update/ALGORITHM_UPDATE.md`：
    - 作为更详细的升级说明文档，补充解释升级动机与整体流程（本 Step 未修改其内容，仅引用其思想）。
- **涉及代码**：
  - 本 Step 不修改任何源码文件，仅通过阅读现有实现完成现状盘点与设计对齐。
- **验证方式**：
  - 通过检查：
    - `/update/DEV_NOTES.md` 是否完整描述现状架构与计划中的模块改造点；
    - `/update/ALGORITHM.md` 是否以非实现化语言清晰概述升级方向；
    - `/update/INDEX.md` 是否明确建立了 `/update` 与 `docs/ALGORITHM.md` 之间的映射关系。
  - 由于未涉及代码变更，本 Step 无需运行程序进行回归验证。

---

### Step 2：岛模型并行 GA 实现与接入

- **日期**：2025-12-13
- **状态**：已完成（新增岛模型 GA，可配置开关，保持默认单种群行为不变）。
- **涉及文档**：
  - `/update/DEV_NOTES.md`：
    - 新增「5. Step 2：岛模型并行 GA 实现方案」章节；
    - 描述多岛结构、异质岛类型（利润导向/交付导向/探索导向）、精英迁移策略以及与单种群 GA 的可退化关系；
    - 明确新增模块 `src/ga/island_engine.py` 与在入口 `run_ga(...)` 处的路由逻辑。
  - `/update/ALGORITHM.md`：
    - 新增「4. 岛模型并行遗传算法的执行机制（抽象）」章节；
    - 以流程视角描述多岛结构、迭代进化、精英迁移与终止条件，并强调与单种群框架的向上兼容性；
    - 仍不出现任何代码/类名/函数名，仅在机制层面对齐实现思路。
- **涉及代码**：
  - `src/config.py`：
    - 新增岛模型 GA 配置项（默认保持关闭，以维持旧行为）：
      - `ENABLE_ISLAND_GA`（默认 False）、`NUM_ISLANDS`（默认 1）、`ISLAND_MIGRATION_INTERVAL`、`ISLAND_MIGRATION_ELITE_COUNT`、`ISLAND_TYPES`、
        `ISLAND_PROFIT_SELECTION_PRESSURE`、`ISLAND_EXPLORATION_MUTATION_SCALE` 等；
    - 预留风险驱动局部搜索与受控退火的相关参数与调试开关，供 Step 3 使用（但当前未启用）。
  - 新增 `src/ga/island_engine.py`：
    - 实现 `IslandGAEngine`，内部维护多岛种群：
      - 每个岛独立执行选择–交叉–变异–精英保留的进化流程；
      - 按类型区分利润导向/交付导向/探索导向，在初始化比例、选择压力和变异强度上体现异质偏好；
      - 周期性执行环形精英迁移，在各岛之间缓慢传播优秀结构；
      - 全程使用统一利润适应度定义，按全局最优解输出结果。
    - 提供便捷入口 `run_island_ga(...)`，签名与现有 `run_ga(...)` 对齐（订单 + 配置 + 规划窗口 → 最优染色体）。
  - 修改 `src/ga/engine.py`：
    - 在文件头部按模块化方式引入 `run_island_ga`；
    - 在便捷函数 `run_ga(...)` 中增加配置分支：
      - 当 `config.ENABLE_ISLAND_GA` 为 True 且 `config.NUM_ISLANDS > 1` 时，委托给岛模型 GA；
      - 其他情况保持原单种群 GAEngine 路径与日志输出不变，保证旧配置下行为完全兼容。
- **验证方式与可复现实验说明**：
  - **旧版（单种群 GA）回归验证**：
    1. 确认配置中保持默认值：`ENABLE_ISLAND_GA = False` 或 `NUM_ISLANDS <= 1`；
    2. 在项目根目录下运行：
       - `python src/main.py`
    3. 期望现象：
       - 控制台日志仍显示“启动遗传算法...”，而非“启动岛模型并行遗传算法...”；
       - 调度流程可以正常完成，输出多日累计指标与甘特图/指标图表，与升级前逻辑一致（数值允许因随机性有微小差异）。
  - **新版（岛模型 GA）功能验证**：
    1. 在调度入口（例如 `src/main.py` 或 `src/service.py` 的配置初始化后）显式设置：
       - `config.ENABLE_ISLAND_GA = True`
       - `config.NUM_ISLANDS = 3`
    2. 使用与旧版相同的命令运行一次完整调度：
       - `python src/main.py`
    3. 期望现象：
       - 控制台日志中出现“启动岛模型并行遗传算法...”，并打印岛数量；
       - 调度流程照常结束，未出现导入错误或接口不匹配问题；
       - 与单种群 GA 相比，最佳适应度与罚款/利润结构可能有所差异（具体效果将在 Step 4 的对比实验中系统记录）。

### Step 3：风险驱动局部搜索实现与切换

- **日期**：2025-12-13
- **状态**：已完成（新增风险驱动局部搜索路径，可配置开关，默认仍可保持旧 ILS/VNS 行为）。
- **涉及文档**：
  - `/update/DEV_NOTES.md`：
    - 新增「6. Step 3：风险驱动局部搜索实现方案」章节；
    - 说明如何在 `LocalSearch` 内通过开关在“旧版随机邻域 + 贪心接受”和“风险驱动 + 退火接受”之间切换；
    - 描述风险评分的具体计算方式、围绕高风险订单的目标导向邻域设计，以及退火接受策略的参数与作用范围。
  - `/update/ALGORITHM.md`：
    - 新增「5. 风险驱动局部搜索的执行机制（抽象）」章节；
    - 从抽象层面说明：
      - 风险分数如何综合潜在罚款、需求缺口和截止紧迫度；
      - 邻域如何围绕高风险订单在时间/产能与优先级两个维度做定向微调；
      - 退火接受如何在局部搜索内部平衡探索与利用。
- **涉及代码**：
  - `src/local_search/ils_vns.py`：
    - 在 `LocalSearch.optimize(...)` 内增加路径分支：
      - 当 `config.ENABLE_RISK_GUIDED_LS` 为 `True` 时，使用风险驱动局部搜索路径；
      - 否则保持原有 ILS/VNS 行为不变；
    - 引入风险评分与目标导向邻域：
      - 使用适应度评估器获取当前解对应的调度方案与订单完成量；
      - 基于潜在罚款、需求缺口和截止紧迫度计算每个订单的风险分数，并筛选高风险订单集合；
      - 在时间/产线与订单优先级两个维度上，优先对高风险订单及其相关位置进行邻域扰动；
    - 在局部搜索阶段实现受控退火接受：
      - 改善解始终接受；
      - 略差解根据随迭代衰减的接受概率有条件接受，参数由 `ANNEALING_INIT_ACCEPT_PROB`、`ANNEALING_DECAY_RATE`、`ANNEALING_MIN_ACCEPT_PROB` 控制。
  - `src/config.py`：
    - 已在 Step 2 中预留的风险与退火相关配置项在本 Step 得到实际使用：
      - `ENABLE_RISK_GUIDED_LS`、`RISK_WEIGHT_*`、`RISK_THRESHOLD_*`、`RISK_LS_MAX_ITER`、`RISK_LS_NO_IMPROVEMENT_LIMIT`、`ANNEALING_*`、`DEBUG_RISK_LS` 等。
  - `src/main.py` / `src/service.py`（入口层，可选改动）：
    - 可在加载默认配置时显式设置：
      - `config.ENABLE_RISK_GUIDED_LS = True`
    - 以便在演示和 GUI 模式下直接体验“岛模型 GA + 风险驱动局部搜索”的完整升级版本。
- **验证方式与可复现实验说明**：
  - **旧版（随机邻域 + 贪心接受）局部搜索回归验证**：
    1. 确认配置中保持默认值：`ENABLE_RISK_GUIDED_LS = False`；
    2. 在项目根目录下运行：
       - `python src/main.py`
    3. 期望现象：
       - 局部搜索阶段日志保持原有格式，仅打印“启动局部搜索 (ILS/VNS)...”“第 N 次迭代: 改善/提前终止”等信息；
       - 与 Step 2 相比，整体调度结果在允许的随机波动范围内保持一致。
  - **新版（风险驱动局部搜索）功能验证**：
    1. 在入口配置中显式设置：
       - `config.ENABLE_RISK_GUIDED_LS = True`
    2. 使用与旧版相同的命令运行一次完整调度：
       - `python src/main.py`
    3. 期望现象：
       - 局部搜索阶段仍以“启动局部搜索 (ILS/VNS)...”开头，但会额外打印“使用风险驱动局部搜索 + 受控退火接受策略”等说明；
       - 在 `DEBUG_RISK_LS=True` 时，可观察到偶尔接受略差解的日志记录以及排序后的高风险订单信息；
       - 与旧版相比，调度结果在“罚款风险较高”的场景下有机会得到更优的罚款/利润平衡（具体对比将在 Step 4 中系统化记录）。

---

> 后续 Step 4 完成后，需要在本节继续追加记录：
> - 说明最终集成与对比实验的改动；
> - 给出旧版 vs 新版的最小对比回归结果摘要与推荐默认配置。

### Step 4：滚动调度集成 + 最小对比回归

- 日期：2025-12-13
- 状态：已完成（保持滚动调度主流程与接口不变，新增最小对比脚本与记录）。
- 涉及文档：
  - `/update/DEV_NOTES.md`：新增「7. Step 4」集成与对比说明；
  - `/update/ALGORITHM.md`：在“效果与讨论”下补充示例结果与原因分析。
- 涉及代码：
  - 新增 `scripts/min_compare_old_vs_new.py`；
  - 复用 `run_ga(...)` 与 `improve_solution(...)` 的配置路由，无需改动滚动调度器。
- 可复现验证方式：
  1. 在项目根目录运行：
     - `python scripts/min_compare_old_vs_new.py`
     - 可通过环境变量 `MIN_COMPARE_CSV` 指定数据集路径，默认使用 `data/sample_orders_small.csv`
  2. 观察控制台输出与生成的 `output/min_compare_*.txt` 摘要。
- 运行参数（默认）：
  - 旧版：`ENABLE_ISLAND_GA=False`、`ENABLE_RISK_GUIDED_LS=False`；
  - 新版：`ENABLE_ISLAND_GA=True`、`NUM_ISLANDS=3`、`ISLAND_MIGRATION_INTERVAL=20`、`ISLAND_MIGRATION_ELITE_COUNT=2`、`ENABLE_RISK_GUIDED_LS=True`。
- 示例结果（sample_orders_small.csv，窗口=10天）：
  - OLD：Profit=207200.00，Revenue=215150.00，Cost=7950.00，Penalty=0.00；On-time=100.0%，AvgCompletion=100.0%，Runtime≈1.15s
  - NEW：Profit=201884.00，Revenue=210510.00，Cost=7930.00，Penalty=696.00；On-time=95.0%，AvgCompletion=96.7%，Runtime≈3.99s
  - Δ：Profit=-5316.00，Penalty=+696.00，Cost=-20.00
- 原因简述：
  - 小型数据集下，受控退火在局部阶段早期接受少量略差解，导致个别订单完成时序后移并触发罚款；
  - 多岛的结构多样性在该场景未显著降低违约风险，收益增量不足以抵消罚款增量。
- 推荐后续调整方向：
  - 降低 `ANNEALING_INIT_ACCEPT_PROB` 或提高 `RISK_THRESHOLD_HIGH`，收紧“略差解”接受；
  - 适度提高“交付导向”比例或缩短迁移周期，使高风险订单更早受益于跨岛传播的结构。

#### 附：升级版测试案例集
- 新增生成脚本：`scripts/generate_test_cases_for_upgrade.py`
- 产出数据集：
  - `data/cases_high_penalty_cluster.csv`（高罚款聚集场景）
  - `data/cases_uniform_deadlines.csv`（截止时间均匀分布）
  - `data/cases_staggered_arrivals.csv`（到达时间错峰）
  - `data/cases_mixed_products_tight_capacity.csv`（产品混合且产能偏紧）
- 生成方式：
  - `python scripts/generate_test_cases_for_upgrade.py`
- 验证示例（高罚款聚集场景）：
  - `MIN_COMPARE_CSV=data/cases_high_penalty_cluster.csv python scripts/min_compare_old_vs_new.py`
  - 结果摘要：升级版相对旧版 利润变化≈ +19,571.50；罚款下降；完成率提升。
 - 验证示例（截止时间均匀分布）：
   - `MIN_COMPARE_CSV=data/cases_uniform_deadlines.csv python scripts/min_compare_old_vs_new.py`
   - 结果摘要：利润变化≈ +45.00；罚款相同；成本下降约 45；表现基本持平但更稳。
 - 验证示例（到达错峰）：
   - `MIN_COMPARE_CSV=data/cases_staggered_arrivals.csv python scripts/min_compare_old_vs_new.py`
   - 结果摘要：利润变化≈ -3,990.00；罚款上升约 990；需收紧退火与提高交付偏好以降低违约。
 - 验证示例（混合产品/产能偏紧）：
  - `MIN_COMPARE_CSV=data/cases_mixed_products_tight_capacity.csv python scripts/min_compare_old_vs_new.py`
  - 结果摘要：利润变化≈ +2,410.00；罚款上升约 1,110；收入增加更明显，建议调低高风险接受概率进一步平衡。

### GUI v2 接口对齐（新增说明）
- 日期：2025-12-13
- 内容：新增 `/update/GUI_V2_接口说明.md`，对齐“完整周期运行 + 按天浏览”的入口与数据结构，补充新方案参数开关（岛模型/ILS/GA参数）。
- 说明：该文件等价替代 `docs/GUI_V2_使用说明.md` 中“技术实现/数据结构/运行方式”的接口说明；原文的 UI 与展示结构保持一致。
