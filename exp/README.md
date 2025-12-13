# 实验设计与图表说明（无风险局部搜索版本）

## 目标与范围
- 仅评估“岛模型并行 GA”的收益与稳定性，关闭风险驱动局部搜索
- 在相同数据与滚动窗口下，对比“单种群 GA”与“岛模型 GA”
- 输出利润、成本、罚款、按期率与完成率的差异，并给出原因分析

## 对比组（实验网格）
- A：单种群 GA + 关闭 ILS（GA Only）
- B：岛模型 GA + 关闭 ILS（Island GA Only）
- C：单种群 GA + 开启 ILS（GA + ILS）
- D：岛模型 GA + 开启 ILS（Island GA + ILS）

说明：
- ILS 为旧版贪心路径（随机邻域 + 仅接受更优解，10 次无改善提前停止）
- 风险驱动局部搜索（退火接受）不参与本轮实验

## 数据与窗口
- 基线数据：`data/sample_orders_small.csv`、`data/sample_orders_medium.csv`
- 场景数据（已提供）：  
  - `data/cases_high_penalty_cluster.csv`（高罚款聚集）  
  - `data/cases_uniform_deadlines.csv`（截止均匀分布）  
  - `data/cases_staggered_arrivals.csv`（到达错峰）  
  - `data/cases_mixed_products_tight_capacity.csv`（混合产品/产能偏紧）
- 自定义约束数据（按需求生成）：  
  - `python scripts/generate_custom_case.py --count 32 --start_min 1 --start_max 40 --due_min 20 --due_max 60 --price_min 60 --price_max 120 --min_duration 6 --quantity_min 150 --quantity_max 250 --output data/custom_case.csv`
- 滚动窗口天数：6 天与 10 天分别跑一遍

## 指标与记录
- 财务：`Profit`、`Revenue`、`Cost`、`Penalty`
- 交付：`On-time Rate`、`AvgCompletionRate`、`Completed Orders`
- 性能：`Runtime (s)`（次要）
- 产线：`Line Utilization`（负载均衡与夜班占比）
- 记录格式：CSV 指标 + 终端摘要 + 图表文件

## 参数与变量
- 岛数量 `NUM_ISLANDS ∈ {1, 3, 5}`（1 为退化）
- 迁移周期 `ISLAND_MIGRATION_INTERVAL ∈ {10, 20, 40}`
- 迁移精英数 `ISLAND_MIGRATION_ELITE_COUNT ∈ {1, 2, 4}`
- 选择压力 `ISLAND_PROFIT_SELECTION_PRESSURE ∈ {1.0, 1.2}`
- 探索变异放大 `ISLAND_EXPLORATION_MUTATION_SCALE ∈ {1.0, 1.5}`
- ILS 开关：`ENABLE_RISK_GUIDED_LS=False`，按需启用旧版贪心 ILS

## 运行方式
### 1）单次最小对比（终端摘要）
1. 指定数据集  
   `MIN_COMPARE_CSV=<path> python scripts/min_compare_old_vs_new.py`
2. 输出内容  
   旧版 vs 新版的 `Profit/Revenue/Cost/Penalty`、`On-time/Completion` 与差异（并写入 `output/min_compare_*.txt`）

### 2）滚动调度入口（末尾打印对比）
1. 运行  
   `python src/main.py`
2. 说明  
   保持主流程与外观不变，末尾打印“旧版 vs 新版（同数据同窗口）”差异与简要原因

### 3）批量实验（含 GA Only 与 GA+ILS）
1. 运行  
   `python scripts/run_experiments.py --mode comparison --data small --save_metrics --save_charts`
2. 输出  
   CSV 指标、甘特图、利润分解、完成率、产线负载图及文本对比报告

## 图表清单（输出至 `output/`）
- `gantt_chart.png`：时间轴-产线分配（颜色区分产品或订单）
- `profit_breakdown.png`：`Revenue/Cost/Penalty/Profit` 构成或堆叠
- `order_completion.png`：完成率、按期率、多天趋势
- `line_utilization.png`：各产线工作时段占比（负载均衡与夜班占比）

建议新增（论文/报告）：
- 并排条形图：A/B/C/D 的 `Profit/Cost/Penalty` 并列对比
- GA 收敛曲线：代数 vs 最优/平均适应度（单群体 vs 岛模型；ILS 开关分层）
- 岛模型各岛最优曲线 + 迁移代数标注（观察精英迁移作用）
- 每日罚款与按期率折线（在高罚款聚集/错峰到达场景更敏感）

## 结论撰写要点
- 岛模型贡献：多风格并行 + 精英迁移，降低早熟收敛，在高罚款或紧产能场景改善罚款与成本平衡
- ILS 贡献：在既有结构基础上小幅稳定提升利润与完成率（贪心路径更稳）
- 若持平或略差：  
  调小探索变异、缩短迁移周期、提高利润/交付导向权重；ILS 迭代与早停阈值适度调整；窗口长度与数据分布匹配

## 复现与留痕
- 每次对比将终端摘要或关键数值追加至 `update/INDEX.md` 的实验记录区
- 在 `update/ALGORITHM.md` 的“效果与讨论”以抽象语言总结场景化结论（不出现实现细节）
