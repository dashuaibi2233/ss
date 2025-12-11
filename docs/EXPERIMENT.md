# 实验方案文档

## 实验目标

评估智能制造生产调度系统的性能和效果，基于《设计大纲.md》第5章的实验设计方案。

**主要目标：**
1. 验证算法的正确性和可行性
2. 评估 GA + ILS/VNS 混合算法的优化效果
3. 对比不同算法的性能差异
4. 分析参数对算法性能的影响

---

## 1. 实验环境与参数设置

### 1.1 实验环境

**硬件环境：**
- CPU: （实验时填写具体型号）
- 内存: （实验时填写）
- 操作系统: Windows/Linux/macOS

**软件环境：**
- Python 版本: 3.8+
- 主要依赖库:
  - `numpy >= 1.21.0`: 数值计算
  - `pandas >= 1.3.0`: 数据处理
  - `matplotlib >= 3.4.0`: 图表绘制
  - `seaborn >= 0.11.0`: 统计可视化
  - `scipy >= 1.7.0`: 科学计算

### 1.2 GA参数设置

| 参数 | 符号 | 取值范围 | 默认值 | 说明 |
|------|------|----------|--------|------|
| 种群规模 | PopSize | 30-100 | 30 | 演示用较小值加快速度 |
| 最大迭代次数 | MaxGen | 50-300 | 50 | 演示用较小值 |
| 交叉概率 | P_c | 0.7-0.9 | 0.8 | 固定 |
| 变异概率 | P_m | 0.05-0.15 | 0.1 | 固定 |
| 精英个体数 | EliteSize | 3-10 | 3 | 保留最优解 |
| 锦标赛规模 | TournamentSize | 2-5 | 3 | 选择操作 |
| 早停阈值 | - | - | 20代 | 连续20代无改善则停止 |

### 1.3 局部搜索参数

| 参数 | 取值 | 说明 |
|------|------|------|
| 最大迭代次数 | 50 | ILS/VNS的迭代上限 |
| 邻域类型 | N1, N2 | 交换时间段产品、微调订单分配 |
| 接受策略 | 贪心 | 只接受改进解 |

### 1.4 生产参数

| 参数 | 取值 | 说明 |
|------|------|------|
| 生产线数量 | 3 | 固定 |
| 产品种类 | 3 | 固定 |
| 时间段/天 | 6 | 每4小时一个slot |
| 规划天数 | 10 | 默认10天（60个slot） |
| 产品1产能 | 50 | 单位/slot/产线 |
| 产品2产能 | 60 | 单位/slot/产线 |
| 产品3产能 | 55 | 单位/slot/产线 |

### 1.5 成本参数

**人工成本（按时间段，每天6个slot）：**
- Slot 1-2 (8:00-16:00): 100元/slot（正常工作时间）
- Slot 3 (16:00-20:00): 115元/slot（开始偏离）
- Slot 4 (20:00-24:00): 135元/slot（晚班）
- Slot 5 (0:00-4:00): 150元/slot（深夜，成本最高）
- Slot 6 (4:00-8:00): 140元/slot（凌晨）

**配置示例：**
```python
labor_costs_per_day = [100, 100, 115, 135, 150, 140]  # 6个slot/天
```

**其他参数：**
- **违约罚款规则**: 如果订单未完全完成，罚款 = 订单总金额 × 10%
  - 公式：`Penalty = quantity × unit_price × 0.1`（当 remaining > 0 时）
- 产品单价: 根据订单CSV文件中的unit_price字段确定

---

## 2. 测试算例设计

### 2.1 小规模算例

**目的：** 验证算法正确性，便于调试和可视化

**规模：**
- 订单数量: 20个
- 规划时域: 10天（60个slot）
- 数据文件: `data/sample_orders_small.csv`

**订单分布：**
- 产品类型: 均匀分布在3种产品（产品1、2、3）
- 订单数量: 80-300单位
- 截止时间: slot 4-36（分散在前6天）
- 单价: 48-70元（根据产品和订单不同）

**实际数据示例：**
```csv
order_id,product,quantity,due_slot,unit_price
1,2,220,5,70
2,1,150,6,50
3,3,180,8,60
...
```

### 2.2 中等规模算例

**目的：** 评估算法性能和运行效率

**规模：**
- 订单数量: 50-100个
- 规划时域: 7-14天（42-84个slot）
- 数据文件: `data/sample_orders_medium.csv`

**订单分布：**
- 产品类型: 均匀分布
- 订单数量: 70-160单位
- 截止时间: 均匀分布或集中分布（两种场景）

### 2.3 滚动调度测试

**目的：** 验证滚动调度机制的正确性

**测试方案：**
- 模拟3天的滚动调度过程
- 每天早上8点执行一次调度
- 观察订单状态更新和累计统计

**验证要点：**
1. **订单状态更新**：每天执行后，订单的`remaining`应该减少
2. **未完成订单数递减**：Day 1→Day 2→Day 3，未完成订单数应逐渐减少
3. **多日累计统计**：
   - 总收入 = Day1收入 + Day2收入 + Day3收入
   - 总成本 = Day1成本 + Day2成本 + Day3成本
   - 总罚款 = Day1罚款 + Day2罚款 + Day3罚款
   - 总利润 = 总收入 - 总成本 - 总罚款
4. **冻结时段机制**：已执行的时段不应被重新调度

**预期结果示例：**
```
Day 1: 待处理订单 20个 (未完成: 20个) → 完成15个
Day 2: 待处理订单 20个 (未完成: 5个)  → 完成2个
Day 3: 待处理订单 20个 (未完成: 3个)  → 完成0个
最终: 完成订单数 17/20 (85%)
```

### 2.4 不同截止时间分布场景

**场景A：截止时间集中（高峰交付）**
- 50%的订单集中在前3天到期
- 模拟订单高峰期

**场景B：截止时间均匀分布（平稳生产）**
- 订单截止时间均匀分布在整个规划期
- 模拟正常生产状态

---

## 3. 对比算法设计

### 3.1 基准算法（Baseline）

**规则调度算法 - EDD（Earliest Due Date）**

```
算法流程:
1. 按截止时间对订单排序（最早截止优先）
2. 按时间顺序为每个订单分配最早可用的产能
3. 优先使用成本低的时间段（白班 > 晚班 > 夜班）
```

### 3.2 对比算法1

**仅GA（无局部搜索）**

- 使用相同的GA参数
- 不执行局部搜索步骤
- 评估局部搜索的贡献

### 3.3 对比算法2（本文算法）

**GA + ILS/VNS**

- 完整的混合优化框架
- GA全局搜索 + 局部搜索精化

---

## 4. 评价指标

### 4.1 主要指标

| 指标 | 计算公式 | 说明 |
|------|----------|------|
| **总利润** | Revenue - Cost - Penalty | 核心优化目标 |
| **总收入** | ∑ q_o^done × s_o | 已完成订单收入 |
| **总成本** | ∑∑ c_t × WorkIndicator_{l,t} | 人工成本 |
| **总罚款** | ∑_{o: q_o^done < q_o} 0.1 × q_o × s_o | 违约罚款（订单总金额10%） |

### 4.2 辅助指标

| 指标 | 计算公式 | 说明 |
|------|----------|------|
| **订单按期完成率** | 按时完成订单数 / 总订单数 | 服务质量 |
| **订单完成量比例** | ∑ q_o^done / ∑ q_o | 产能利用 |
| **产线平均负载率** | 实际工作slot数 / 总可用slot数 | 资源利用 |
| **算法运行时间** | 秒 | 计算效率 |

### 4.3 收敛性指标

- **GA收敛曲线**: 迭代次数 vs 最优适应度
- **收敛代数**: 达到稳定解的迭代次数
- **适应度提升率**: (最终适应度 - 初始适应度) / 初始适应度

---

## 5. 实验步骤

### 5.1 数据准备

```bash
# 1. 准备订单数据
# 使用现有样本或生成新数据
python scripts/generate_orders.py --size small --output data/orders_test.csv

# 2. 配置参数
# 编辑 src/config.py，设置实验参数
```

### 5.2 参数调优

```bash
# 运行参数敏感性分析
python experiments/parameter_tuning.py --param population_size --range 30,50,100
python experiments/parameter_tuning.py --param max_generations --range 100,200,300
```

### 5.3 运行对比实验

```bash
# 运行基准算法
python src/main.py --algorithm edd --data data/sample_orders_small.csv

# 运行仅GA
python src/main.py --algorithm ga_only --data data/sample_orders_small.csv

# 运行完整算法
python src/main.py --algorithm ga_ils --data data/sample_orders_small.csv
```

### 5.4 结果分析与可视化

```bash
# 生成对比报告
python experiments/compare_algorithms.py --output results/comparison_report.pdf

# 绘制收敛曲线
python experiments/plot_convergence.py --input results/ --output figures/
```

### 5.5 撰写实验报告

整理实验数据，生成表格和图表，撰写分析报告。

---

## 6. 预期实验结果

### 6.1 算法性能对比（预期）

| 算法 | 总利润 | 按期完成率 | 运行时间 |
|------|--------|------------|----------|
| EDD（基准） | 基准值 | 较低 | 最快 |
| 仅GA | +10-15% | 中等 | 中等 |
| GA+ILS/VNS | +15-25% | 最高 | 较慢 |

### 6.2 可视化输出

1. **甘特图**: 展示生产线调度安排
2. **利润分解图**: Revenue、Cost、Penalty的占比
3. **收敛曲线**: GA迭代过程的适应度变化
4. **对比柱状图**: 不同算法的各项指标对比
5. **负载率热力图**: 各生产线各时间段的负载情况

---

## 7. 实验运行方式

### 7.1 快速演示（默认配置）

```bash
# 进入项目根目录
cd c:\Users\Yuban\Desktop\computer_agent\smart-scheduling

# 运行小规模算例演示（默认使用 data/sample_orders_small.csv）
python src\main.py
```

**输出位置：**
- 控制台：实时进度和详细指标
- `output/gantt_chart.png` - 甘特图
- `output/profit_breakdown.png` - 利润分解图
- `output/order_completion.png` - 订单完成率图
- `output/line_utilization.png` - 产线利用率图

---

### 7.2 切换不同算例

#### 使用小规模算例（10个订单）

```bash
python scripts\run_experiments.py --data small --algorithm ga_ils
```

#### 使用中等规模算例（需先创建）

```bash
# 1. 创建中等规模订单数据
python scripts\generate_medium_orders.py

# 2. 运行实验
python scripts\run_experiments.py --data medium --algorithm ga_ils
```

---

### 7.3 切换不同算法

#### 方法1：基准算法（EDD规则）

```bash
python scripts\run_experiments.py --algorithm edd --data small
```

**说明：** 使用最早截止日期优先（EDD）规则，不使用GA和局部搜索

#### 方法2：仅使用GA（无局部搜索）

```bash
python scripts\run_experiments.py --algorithm ga_only --data small
```

**说明：** 只运行遗传算法，跳过局部搜索步骤

#### 方法3：完整算法（GA + ILS/VNS）

```bash
python scripts\run_experiments.py --algorithm ga_ils --data small
```

**说明：** 完整的混合优化框架（默认）

---

### 7.4 批量运行对比实验

```bash
# 运行所有算法对比实验
python scripts\run_experiments.py --mode comparison --data small

# 运行参数敏感性分析
python scripts\run_experiments.py --mode sensitivity --param population_size
```

**输出位置：**
- `results/metrics_edd_small.csv` - EDD算法指标
- `results/metrics_ga_only_small.csv` - 仅GA算法指标
- `results/metrics_ga_ils_small.csv` - 完整算法指标
- `results/comparison_report.txt` - 对比报告
- `results/gantt_edd_small.png` - EDD甘特图
- `results/gantt_ga_only_small.png` - 仅GA甘特图
- `results/gantt_ga_ils_small.png` - 完整算法甘特图

---

### 7.5 自定义实验参数

#### 修改GA参数

```bash
python scripts\run_experiments.py --data small --algorithm ga_ils \
    --population 100 --generations 300 --crossover 0.9 --mutation 0.05
```

#### 修改局部搜索参数

```bash
python scripts\run_experiments.py --data small --algorithm ga_ils \
    --ls_iterations 100
```

#### 修改产能参数

编辑 `src/config.py`：

```python
# 产能参数
CAPACITY = {
    1: 100,  # 产品1产能（原50）
    2: 120,  # 产品2产能（原60）
    3: 110,  # 产品3产能（原55）
}
```

---

### 7.6 结果保存路径约定

#### 标准输出路径结构

```
results/
├── metrics_{algorithm}_{dataset}.csv      # 指标数据
├── gantt_{algorithm}_{dataset}.png        # 甘特图
├── profit_{algorithm}_{dataset}.png       # 利润分解图
├── completion_{algorithm}_{dataset}.png   # 订单完成率图
├── utilization_{algorithm}_{dataset}.png  # 产线利用率图
├── convergence_{algorithm}_{dataset}.png  # 收敛曲线（仅GA相关）
└── comparison_report_{timestamp}.txt      # 对比报告
```

#### 命名规则

- `{algorithm}`: `edd`, `ga_only`, `ga_ils`
- `{dataset}`: `small`, `medium`, `custom`
- `{timestamp}`: `YYYYMMDD_HHMMSS`

#### 示例

```
results/
├── metrics_ga_ils_small.csv
├── gantt_ga_ils_small.png
├── profit_ga_ils_small.png
├── comparison_report_20251209_001530.txt
```

---

### 7.7 完整实验流程示例

```bash
# 步骤1: 准备数据
# 使用现有的 data/sample_orders_small.csv 或创建新数据

# 步骤2: 运行所有算法对比
python scripts\run_experiments.py --mode comparison --data small

# 步骤3: 查看结果
# 打开 results/ 目录查看生成的图表和CSV文件

# 步骤4: 生成对比报告
python scripts\run_experiments.py --mode report

# 步骤5: 查看报告
# 打开 results/comparison_report_*.txt
```

---

### 7.8 实验脚本参数说明

#### run_experiments.py 参数

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `--data` | 数据集 | `small`, `medium`, `custom` | `small` |
| `--algorithm` | 算法类型 | `edd`, `ga_only`, `ga_ils` | `ga_ils` |
| `--mode` | 运行模式 | `single`, `comparison`, `sensitivity`, `report` | `single` |
| `--population` | 种群规模 | 整数 | 50 |
| `--generations` | 最大迭代次数 | 整数 | 100 |
| `--crossover` | 交叉概率 | 0-1 | 0.8 |
| `--mutation` | 变异概率 | 0-1 | 0.1 |
| `--ls_iterations` | 局部搜索迭代次数 | 整数 | 50 |
| `--output_dir` | 输出目录 | 路径 | `results` |
| `--save_metrics` | 保存指标到CSV | - | True |
| `--save_charts` | 保存图表 | - | True |

#### 使用示例

```bash
# 示例1: 运行单个实验
python scripts\run_experiments.py --data small --algorithm ga_ils

# 示例2: 对比所有算法
python scripts\run_experiments.py --mode comparison --data small

# 示例3: 参数敏感性分析
python scripts\run_experiments.py --mode sensitivity --param population_size

# 示例4: 自定义参数
python scripts\run_experiments.py --data small --algorithm ga_ils \
    --population 100 --generations 200 --ls_iterations 100

# 示例5: 只生成报告（不运行实验）
python scripts\run_experiments.py --mode report
```

---

## 8. 实验结果分析

### 8.1 指标CSV格式

`results/metrics_{algorithm}_{dataset}.csv`:

```csv
metric,value
total_profit,45678.90
total_revenue,52000.00
total_cost,4500.00
total_penalty,1821.10
on_time_rate,0.85
avg_completion_rate,0.92
working_slots,45
runtime_seconds,125.34
```

### 8.2 对比报告格式

`results/comparison_report_{timestamp}.txt`:

```
=================================================================
ALGORITHM COMPARISON REPORT
Generated: 2025-12-09 00:15:30
Dataset: small (10 orders)
=================================================================

FINANCIAL METRICS:
------------------------------------------------------------------
Algorithm       Profit      Revenue     Cost        Penalty
------------------------------------------------------------------
EDD             35,234.50   48,000.00   4,200.00    8,565.50
GA_ONLY         42,156.80   51,500.00   4,350.00    4,993.20
GA_ILS          45,678.90   52,000.00   4,500.00    1,821.10
------------------------------------------------------------------

PERFORMANCE METRICS:
------------------------------------------------------------------
Algorithm       On-time Rate    Completion Rate    Runtime(s)
------------------------------------------------------------------
EDD             65.0%           78.5%              0.12
GA_ONLY         80.0%           88.2%              98.45
GA_ILS          85.0%           92.0%              125.34
------------------------------------------------------------------

IMPROVEMENT ANALYSIS:
------------------------------------------------------------------
GA_ONLY vs EDD:     +19.6% profit, +15.0% on-time rate
GA_ILS vs EDD:      +29.6% profit, +20.0% on-time rate
GA_ILS vs GA_ONLY:  +8.4% profit, +5.0% on-time rate
------------------------------------------------------------------
```

---

## 9. 参考

详细实验设计请参考《设计大纲.md》第5章。

**相关文件：**
- 设计文档: `docs/设计大纲.md`
- 主程序: `src/main.py`
- 实验脚本: `scripts/run_experiments.py`
- 配置文件: `src/config.py`
- 示例数据: `data/sample_orders_small.csv`
