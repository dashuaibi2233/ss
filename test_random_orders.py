"""
快速测试 sample_orders_random.csv 的订单到达效果
"""
import sys
sys.path.append('src')

from scheduler.order_manager import OrderManager

print("="*70)
print("测试 sample_orders_random.csv - 订单随机到达效果")
print("="*70)

# 加载订单
om = OrderManager()
count = om.load_orders_from_csv('data/sample_orders_random.csv')

print(f"\n✅ 已加载 {count} 个订单")

# 获取所有订单
all_orders = om.get_all_orders()

# 按release_slot排序
all_orders.sort(key=lambda x: x.release_slot)

print("\n📋 订单到达时间表:")
print("-" * 70)
print(f"{'订单ID':<8} {'产品':<6} {'数量':<8} {'到达slot':<10} {'截止slot':<10} {'时间窗口'}")
print("-" * 70)

for order in all_orders:
    release_day = (order.release_slot - 1) // 6 + 1
    due_day = (order.due_slot - 1) // 6 + 1
    window = order.due_slot - order.release_slot
    print(f"{order.order_id:<8} {order.product:<6} {order.quantity:<8} "
          f"{order.release_slot:<4}(第{release_day}天) {order.due_slot:<4}(第{due_day}天) "
          f"{window}个slot")

# 模拟前10天的调度
print("\n" + "="*70)
print("模拟前10天的订单到达情况")
print("="*70)

for day in range(10):
    current_slot = day * 6 + 1
    eligible = om.get_eligible_orders(current_slot)
    
    # 统计新到达的订单
    if day == 0:
        new_orders = eligible
    else:
        prev_slot = (day - 1) * 6 + 1
        prev_eligible = om.get_eligible_orders(prev_slot)
        prev_ids = {o.order_id for o in prev_eligible}
        new_orders = [o for o in eligible if o.order_id not in prev_ids]
    
    print(f"\n第 {day + 1} 天 (slot {current_slot}):")
    print(f"  - 可调度订单: {len(eligible)} 个")
    if new_orders:
        new_ids = [o.order_id for o in new_orders]
        print(f"  - 新到达订单: {len(new_orders)} 个 → 订单 {new_ids}")
    else:
        print(f"  - 新到达订单: 0 个")

print("\n" + "="*70)
print("✅ 测试完成！")
print("="*70)
print("\n💡 观察要点:")
print("  1. 订单不是第1天全部到达，而是逐步到达")
print("  2. 每天的可调度订单数量逐渐增加")
print("  3. 每天都有新订单到达（除了某些天）")
print("  4. 适合测试滚动调度和订单随机到达机制")
