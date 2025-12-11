# 快速开始指南

## 系统概述

智能制造生产调度系统 - 基于遗传算法和局部搜索的混合优化框架

---

## 快速运行

### 1. 基础演示（推荐）

```bash
# 进入项目目录
cd c:\Users\Yuban\Desktop\computer_agent\smart-scheduling

# 运行默认演示
python src\main.py
```

**输出：**
- 控制台显示调度过程和指标
- `output/` 目录生成甘特图和指标图表

---

### 2. 运行实验对比

```bash
# 对比所有算法（EDD, GA_ONLY, GA_ILS）
python scripts\run_experiments.py --mode comparison --data small
```

**输出：**
- `results/` 目录生成所有算法的结果
- 自动生成对比报告

---

## 目录结构

```
smart-scheduling/
├── data/                          # 数据文件
│   └── sample_orders_small.csv   # 示例订单（10个）
├── src/                           # 源代码
│   ├── models/                    # 数据模型
│   ├── ga/                        # 遗传算法
│   ├── local_search/              # 局部搜索
│   ├── scheduler/                 # 调度器
│   ├── visualization/             # 可视化
│   ├── config.py                  # 配置文件
│   └── main.py                    # 主程序
├── scripts/                       # 实验脚本
│   └── run_experiments.py         # 批量实验
├── docs/                          # 文档
│   ├── EXPERIMENT.md              # 实验方案
│   └── QUICK_START.md             # 本文件
├── output/                        # 默认输出（main.py）
└── results/                       # 实验结果（run_experiments.py）
```

---

## 常用命令

### 运行不同算法

```bash
# EDD基准算法
python scripts\run_experiments.py --algorithm edd --data small

# 仅GA（无局部搜索）
python scripts\run_experiments.py --algorithm ga_only --data small

# 完整算法（GA + ILS/VNS）
python scripts\run_experiments.py --algorithm ga_ils --data small
```

### 自定义参数

```bash
# 修改GA参数
python scripts\run_experiments.py --algorithm ga_ils --data small \
    --population 100 --generations 200 --mutation 0.05

# 修改局部搜索迭代次数
python scripts\run_experiments.py --algorithm ga_ils --data small \
    --ls_iterations 100
```

---

## 输出文件说明

### main.py 输出（output/）

- `gantt_chart.png` - 生产甘特图
- `profit_breakdown.png` - 利润分解图
- `order_completion.png` - 订单完成率图
- `line_utilization.png` - 产线利用率图

### run_experiments.py 输出（results/）

- `metrics_{algorithm}_{dataset}.csv` - 数值指标
- `gantt_{algorithm}_{dataset}.png` - 甘特图
- `profit_{algorithm}_{dataset}.png` - 利润图
- `completion_{algorithm}_{dataset}.png` - 完成率图
- `utilization_{algorithm}_{dataset}.png` - 利用率图
- `comparison_report_{timestamp}.txt` - 对比报告

---

## 修改配置

编辑 `src/config.py`：

```python
# GA参数
POPULATION_SIZE = 50        # 种群规模
MAX_GENERATIONS = 100       # 最大迭代次数
CROSSOVER_RATE = 0.8        # 交叉概率
MUTATION_RATE = 0.1         # 变异概率

# 产能参数
CAPACITY = {
    1: 50,   # 产品1产能
    2: 60,   # 产品2产能
    3: 55,   # 产品3产能
}

# 成本参数
PENALTY_RATE = 0.1          # 罚款比例
```

---

## 添加新订单

编辑 `data/sample_orders_small.csv`：

```csv
order_id,product,quantity,due_slot,unit_price
11,1,100,15,50
12,2,120,20,60
```

**字段说明：**
- `order_id`: 订单编号（唯一）
- `product`: 产品类型（1/2/3）
- `quantity`: 订单数量
- `due_slot`: 截止时间段
- `unit_price`: 单价

---

## 常见问题

### Q: 如何加快运行速度？

A: 减小GA参数：
```bash
python scripts\run_experiments.py --algorithm ga_ils --data small \
    --population 30 --generations 50 --ls_iterations 20
```

### Q: 如何提高解的质量？

A: 增大GA参数：
```bash
python scripts\run_experiments.py --algorithm ga_ils --data small \
    --population 100 --generations 300 --ls_iterations 100
```

### Q: 如何查看详细的调度过程？

A: 运行 `main.py`，控制台会显示详细的GA和局部搜索过程。

---

## 更多信息

- 详细实验方案：`docs/EXPERIMENT.md`
- 设计文档：`设计大纲.md`
- 源代码：`src/` 目录

---

## 技术支持

如有问题，请检查：
1. Python版本 >= 3.8
2. 已安装依赖：`matplotlib`, `numpy`
3. CSV文件格式正确
4. 路径使用正确的分隔符（Windows: `\`, Linux/Mac: `/`）
