# GUI v2.0 接口说明（新方案对齐）

## 概述
- 目的：将 GUI 的“完整周期运行 + 按天浏览”接口与新方案对齐（支持岛模型 GA 开关、ILS 开关、滚动窗口保持不变）。
- 不改动滚动调度外观行为与对外接口；仅在内部参数与入口方法上对齐新方案的开关与返回结构。

## 对齐接口

### 1. 运行入口（完整周期）
- 方法：`run_full_cycle(num_days: int, csv_path: str, config_overrides: dict) -> SimulationResult`
- 行为：一次性运行 `num_days` 天的滚动调度，返回完整周期的 `SimulationResult`。
- 主要入参：
  - `num_days`：运行的天数（如 3、5、10）。
  - `csv_path`：订单数据 CSV 文件路径。
  - `config_overrides`：用于覆盖默认配置的键值，如：
    - `ENABLE_ISLAND_GA`（bool），`NUM_ISLANDS`（int）
    - `ENABLE_RISK_GUIDED_LS`（bool），`MAX_LS_ITERATIONS`（int）
    - `POPULATION_SIZE`、`MAX_GENERATIONS`、`CROSSOVER_RATE`、`MUTATION_RATE`、`ELITE_SIZE`
    - （可选）`CAPACITY`、`LABOR_COSTS`
- 返回值：`SimulationResult`（按天结构 + 累计统计）

### 2. 结果结构
- `SimulationResult`：
  - `num_days`：运行的天数
  - `days`：字典 `day_index -> DayResult`
  - `cumulative_stats`：总收入/总成本/总罚款/总利润、订单统计、每日明细列表
- `DayResult`：
  - `day_index`：当前天索引（0-based）
  - `schedule`：该天滚动起点到规划窗口的调度方案
  - `orders`：订单进度（累计完成/剩余/状态/是否按期/截止时段/单价）
  - `financial`：当天财务指标（收入/成本/罚款/利润）

### 3. GUI 端使用
- 加载订单后，调用 `run_full_cycle(num_days, csv_path, config_overrides)` 得到 `simulation_result`。
- GUI 保持 v2 的“按天浏览”UI：
  - 天数选择器（前一天/下一天/下拉框）
  - 当前天订单进度表 + 当天财务卡片 + 累计统计

## 新方案的参数开关
- 岛模型 GA：
  - `ENABLE_ISLAND_GA=True/False`，`NUM_ISLANDS>=1`（1 为退化、相当于单群体）
  - （可选）迁移与选择压力根据已有配置保持不变
- 局部搜索（ILS）：
  - `ENABLE_RISK_GUIDED_LS=False`（本 GUI 对齐版默认不开启风险退火）
  - `MAX_LS_ITERATIONS>=0`（为 0 时不执行局部搜索）
- 其它 GA 参数：
  - `POPULATION_SIZE`、`MAX_GENERATIONS`、`CROSSOVER_RATE`、`MUTATION_RATE`、`ELITE_SIZE`

## 返回与展示不变项
- 滚动调度触发时机、冻结窗口、订单池收集、输出计划的使用方式不变。
- 适应度主定义不变：利润 = 收入 − 成本 − 罚款；罚款=订单总金额的10%（未完全完成即罚一次）。
- GUI 展示字段与表格结构不变（只增加参数开关的传参入口）。

## 调用示例（伪代码，GUI 侧）
```
config_overrides = {
  "ENABLE_ISLAND_GA": True,
  "NUM_ISLANDS": 3,
  "ENABLE_RISK_GUIDED_LS": False,
  "POPULATION_SIZE": 30,
  "MAX_GENERATIONS": 50,
  "CROSSOVER_RATE": 0.8,
  "MUTATION_RATE": 0.1,
  "ELITE_SIZE": 3
}
simulation_result = run_full_cycle(num_days=5, csv_path="data/delay_full.csv", config_overrides=config_overrides)
gui_state.simulation_result = simulation_result
gui_state.current_day = 0
```

## 与 docs/GUI_V2_使用说明.md 的关系
- 本文件为“接口对齐”补充说明，等价替代原文中的“技术实现/数据结构/运行方式”相关部分。
- GUI 交互方式、按天浏览、不变字段与表格说明保持与原文一致；仅新增/明确“新方案参数开关与入口方法”。

