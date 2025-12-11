"""
分析产能利用率
"""
import sys
sys.path.append('src')

from config import Config
from scheduler.order_manager import OrderManager

# 加载配置和订单
config = Config()
order_manager = OrderManager()
order_manager.load_orders_from_csv('data/sample_orders_small.csv')
orders = order_manager.get_all_orders()

# 统计各产品的总需求
demand_by_product = {1: 0, 2: 0, 3: 0}
for order in orders:
    demand_by_product[order.product] += order.quantity

print("="*70)
print("需求与产能分析")
print("="*70)

print("\n各产品总需求：")
total_demand = 0
for product, demand in demand_by_product.items():
    print(f"  产品{product}: {demand}单位")
    total_demand += demand
print(f"  总需求: {total_demand}单位")

# 产能配置
print("\n产能配置：")
for product, capacity in config.CAPACITY.items():
    print(f"  产品{product}: {capacity}单位/slot/产线")

# 计算理论最大产能
num_lines = config.NUM_LINES
num_slots = 36  # 6天 × 6 slots/天

print(f"\n可用资源：")
print(f"  产线数: {num_lines}")
print(f"  时间段数: {num_slots} (6天)")
print(f"  总产线-时段数: {num_lines * num_slots} = {num_lines}×{num_slots}")

# 计算各产品需要的产线-时段数
print("\n各产品需要的产线-时段数：")
required_slots_by_product = {}
for product, demand in demand_by_product.items():
    capacity = config.CAPACITY[product]
    required_slots = demand / capacity
    required_slots_by_product[product] = required_slots
    print(f"  产品{product}: {demand}/{capacity} = {required_slots:.2f}个产线-时段")

total_required_slots = sum(required_slots_by_product.values())
total_available_slots = num_lines * num_slots

print(f"\n产能利用率：")
print(f"  需要: {total_required_slots:.2f}个产线-时段")
print(f"  可用: {total_available_slots}个产线-时段")
print(f"  利用率: {total_required_slots/total_available_slots*100:.1f}%")
print(f"  空闲: {total_available_slots - total_required_slots:.2f}个产线-时段 ({(1-total_required_slots/total_available_slots)*100:.1f}%)")

# 按截止时间分析
print("\n按截止时间分析订单分布：")
slots_deadline = {6: [], 12: [], 18: [], 24: [], 30: [], 36: []}
for order in orders:
    if order.due_slot in slots_deadline:
        slots_deadline[order.due_slot].append(order)

for due_slot in sorted(slots_deadline.keys()):
    orders_list = slots_deadline[due_slot]
    total_qty = sum(o.quantity for o in orders_list)
    print(f"  截止slot {due_slot} (第{due_slot//6}天): {len(orders_list)}个订单, 总量{total_qty}单位")

print("\n结论：")
if total_required_slots < total_available_slots:
    print(f"  ✅ 产能充足！理论上可以完成所有订单")
    print(f"  ⚠️  但会有 {(1-total_required_slots/total_available_slots)*100:.1f}% 的产能空闲")
    print(f"  💡 这是正常的，因为：")
    print(f"     1. 订单有截止时间约束，不能随意安排")
    print(f"     2. 不同产品需要不同产线配置")
    print(f"     3. 算法需要在时间和产品切换之间平衡")
else:
    print(f"  ❌ 产能不足！无法完成所有订单")
