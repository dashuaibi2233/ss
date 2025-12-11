"""
调试Gene1和Gene2的生成和解码
"""
import sys
sys.path.append('src')

from config import Config
from scheduler.order_manager import OrderManager
from models.chromosome import Chromosome
from ga.decoder import Decoder
import random

# 加载配置和订单
config = Config()
order_manager = OrderManager()
order_manager.load_orders_from_csv('data/sample_orders_small.csv')
orders = order_manager.get_all_orders()

print(f"加载了 {len(orders)} 个订单")
print("\n订单列表：")
for i, order in enumerate(orders):
    print(f"  索引{i}: 订单{order.order_id}, 产品{order.product}, 数量{order.quantity}, 截止slot{order.due_slot}")

# 创建一个简单的染色体
num_lines = config.NUM_LINES
num_slots = 60
gene1_length = num_lines * num_slots

# Gene1: 让所有产线在所有时段都生产产品1
gene1 = [1] * gene1_length  # 全部生产产品1

# Gene2: 按订单ID顺序
gene2 = list(range(len(orders)))  # [0, 1, 2, ..., 19]

print(f"\nGene1长度: {len(gene1)}, 前10个值: {gene1[:10]}")
print(f"Gene2长度: {len(gene2)}, 值: {gene2}")

# 创建染色体
chromosome = Chromosome(gene1=gene1, gene2=gene2)

# 解码
decoder = Decoder(config)
schedule = decoder.decode(chromosome, orders, start_slot=1)

print(f"\n解码结果：")
print(f"  分配记录数: {len(schedule.allocation)}")

if schedule.allocation:
    print("\n前10条分配记录：")
    for i, ((order_id, line, slot), qty) in enumerate(schedule.allocation.items()):
        if i >= 10:
            break
        print(f"    订单{order_id}, 产线{line}, slot{slot}: {qty}单位")
    
    # 统计每个订单的分配
    order_stats = {}
    for (order_id, line, slot), qty in schedule.allocation.items():
        if order_id not in order_stats:
            order_stats[order_id] = 0
        order_stats[order_id] += qty
    
    print(f"\n订单分配统计（共{len(order_stats)}个订单被分配）：")
    for order_id in sorted(order_stats.keys()):
        order = order_manager.get_order(order_id)
        print(f"  订单{order_id}: {order_stats[order_id]}/{order.quantity}")
else:
    print("  ❌ 没有任何分配！")

# 计算指标
schedule.calculate_metrics(orders, config.LABOR_COSTS, config.PENALTY_RATE)
print(f"\n财务指标：")
print(f"  收入: ¥{schedule.revenue:.2f}")
print(f"  成本: ¥{schedule.cost:.2f}")
print(f"  罚款: ¥{schedule.penalty:.2f}")
print(f"  利润: ¥{schedule.profit:.2f}")
