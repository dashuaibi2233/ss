"""
测试滚动调度的release_slot过滤逻辑
验证每天8点只调度已到达的订单
"""
import sys
sys.path.append('src')

from scheduler.order_manager import OrderManager
from models.order import Order

print("="*70)
print("测试滚动调度的 release_slot 过滤逻辑")
print("="*70)

# 创建订单管理器
om = OrderManager()

# 添加测试订单
# Order(order_id, product, quantity, due_slot, unit_price, release_slot)
# 订单1-3: release_slot=1 (第1天就到达)
# 订单4-6: release_slot=7 (第2天才到达)
# 订单7-9: release_slot=13 (第3天才到达)
# 注意：due_slot是截止日期当天早上8点，订单必须在此之前完成
test_orders = [
    Order(1, 1, 100, 6, 50.0, 1),    # 第1天到达，第1天截止（slot 1-5可生产）
    Order(2, 2, 120, 12, 60.0, 1),   # 第1天到达，第2天截止（slot 1-11可生产）
    Order(3, 3, 90, 18, 55.0, 1),    # 第1天到达，第3天截止（slot 1-17可生产）
    Order(4, 1, 150, 12, 50.0, 7),   # 第2天到达，第2天截止（slot 7-11可生产）
    Order(5, 2, 130, 18, 60.0, 7),   # 第2天到达，第3天截止（slot 7-17可生产）
    Order(6, 3, 110, 24, 55.0, 7),   # 第2天到达，第4天截止（slot 7-23可生产）
    Order(7, 1, 140, 18, 50.0, 13),  # 第3天到达，第3天截止（slot 13-17可生产）
    Order(8, 2, 160, 24, 60.0, 13),  # 第3天到达，第4天截止（slot 13-23可生产）
    Order(9, 3, 120, 30, 55.0, 13),  # 第3天到达，第5天截止（slot 13-29可生产）
]

for order in test_orders:
    om.add_order(order)

print(f"\n总订单数: {len(test_orders)}")
print("\n订单列表:")
for order in test_orders:
    print(f"  订单{order.order_id}: release_slot={order.release_slot}, due_slot={order.due_slot}, remaining={order.remaining}")

# 模拟多天调度
print("\n" + "="*70)
print("模拟滚动调度")
print("="*70)

for day in range(5):
    print(f"\n{'='*70}")
    print(f"第 {day + 1} 天早上8点调度")
    print(f"{'='*70}")
    
    # 计算当前slot（每天6个slot，第day天早上8点对应slot = day*6 + 1）
    current_slot = om.time_to_slot(day, hour=8)
    print(f"当前起始slot: {current_slot}")
    
    # 获取可调度订单
    eligible_orders = om.get_eligible_orders(current_slot)
    
    # 统计
    all_orders = om.get_all_orders()
    total_unfinished = sum(1 for o in all_orders if o.remaining > 0)
    future_orders = [o for o in all_orders if o.remaining > 0 and o.release_slot > current_slot]
    
    print(f"\n订单池统计:")
    print(f"  - 总未完成订单: {total_unfinished} 个")
    print(f"  - 已到达可调度: {len(eligible_orders)} 个 (release_slot <= {current_slot})")
    print(f"  - 未来订单: {len(future_orders)} 个 (release_slot > {current_slot})")
    
    if eligible_orders:
        print(f"\n可调度订单详情:")
        for order in eligible_orders:
            print(f"  ✅ 订单{order.order_id}: release_slot={order.release_slot} <= {current_slot}")
    
    if future_orders:
        print(f"\n未来订单（本轮不调度）:")
        for order in future_orders:
            print(f"  ⏳ 订单{order.order_id}: release_slot={order.release_slot} > {current_slot}")
    
    # 验证：所有可调度订单的release_slot都应该 <= current_slot
    all_valid = all(o.release_slot <= current_slot for o in eligible_orders)
    if all_valid:
        print(f"\n✅ 验证通过：所有可调度订单都满足 release_slot <= {current_slot}")
    else:
        print(f"\n❌ 验证失败：存在订单不满足 release_slot <= {current_slot}")
        for o in eligible_orders:
            if o.release_slot > current_slot:
                print(f"  错误：订单{o.order_id} release_slot={o.release_slot} > {current_slot}")

print("\n" + "="*70)
print("测试完成")
print("="*70)

# 总结
print("\n📊 测试总结:")
print("1. 第1天(slot=1): 应该只调度订单1-3 (release_slot=1)")
print("2. 第2天(slot=7): 应该调度订单1-6 (release_slot<=7)")
print("3. 第3天(slot=13): 应该调度订单1-9 (release_slot<=13)")
print("4. 每天只调度已到达的订单，未来订单等待下一天")
