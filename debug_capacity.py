"""
调试产能计算
"""
import sys
sys.path.append('src')

from config import Config
from scheduler.order_manager import OrderManager
from models.chromosome import Chromosome
from ga.decoder import Decoder

# 加载配置和订单
config = Config()
order_manager = OrderManager()
order_manager.load_orders_from_csv('data/sample_orders_small.csv')
orders = order_manager.get_all_orders()

# 创建一个简单的染色体
num_lines = config.NUM_LINES
num_slots = 60
gene1_length = num_lines * num_slots

# Gene1: 让所有产线在所有时段都生产产品1
gene1 = [1] * gene1_length

# Gene2: 按订单ID顺序
gene2 = list(range(len(orders)))

chromosome = Chromosome(gene1=gene1, gene2=gene2)

# 创建decoder并计算产能
decoder = Decoder(config)
available_capacity = decoder.calculate_available_capacity(gene1, start_slot=1)

print(f"可用产能记录数: {len(available_capacity)}")
print(f"\n前20条产能记录：")
for i, ((line, slot, product), capacity) in enumerate(available_capacity.items()):
    if i >= 20:
        break
    print(f"  产线{line}, slot{slot}, 产品{product}: 产能{capacity}")

print(f"\n配置信息：")
print(f"  产线数: {config.NUM_LINES}")
print(f"  产品数: {config.NUM_PRODUCTS}")
print(f"  产能配置: {config.CAPACITY}")

# 检查订单2（产品1）
print(f"\n检查订单2（索引1）：")
order = orders[1]
print(f"  订单ID: {order.order_id}")
print(f"  产品类型: {order.product}")
print(f"  需求数量: {order.quantity}")
print(f"  截止slot: {order.due_slot}")

# 查找可用于订单2的产能
matching_capacity = []
for (line, slot, product), capacity in available_capacity.items():
    if product == order.product and capacity > 0:
        matching_capacity.append((slot, line, capacity))

print(f"\n可用于订单2的产能（产品{order.product}）：")
if matching_capacity:
    matching_capacity.sort()
    for slot, line, capacity in matching_capacity[:10]:
        print(f"  slot{slot}, 产线{line}: {capacity}")
else:
    print("  ❌ 没有可用产能！")
