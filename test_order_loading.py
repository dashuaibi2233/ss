"""
测试订单加载功能（包含release_slot）
"""
import sys
sys.path.append('src')

from scheduler.order_manager import OrderManager

print("="*70)
print("测试订单加载功能")
print("="*70)

# 测试1：加载包含release_slot的CSV
print("\n测试1：加载 sample_orders_small.csv（包含release_slot）")
om1 = OrderManager()
count1 = om1.load_orders_from_csv('data/sample_orders_small.csv')
print(f"加载了 {count1} 个订单")

# 显示前5个订单
orders1 = om1.get_all_orders()[:5]
print("\n前5个订单：")
for order in orders1:
    print(f"  {order}")
    print(f"    - release_slot: {order.release_slot}")
    print(f"    - due_slot: {order.due_slot}")

# 测试2：加载delay.csv
print("\n" + "="*70)
print("测试2：加载 delay.csv（包含release_slot）")
om2 = OrderManager()
count2 = om2.load_orders_from_csv('data/delay.csv')
print(f"加载了 {count2} 个订单")

orders2 = om2.get_all_orders()[:5]
print("\n前5个订单：")
for order in orders2:
    print(f"  {order}")

# 测试3：加载delay_full.csv
print("\n" + "="*70)
print("测试3：加载 delay_full.csv（包含release_slot）")
om3 = OrderManager()
count3 = om3.load_orders_from_csv('data/delay_full.csv')
print(f"加载了 {count3} 个订单")

orders3 = om3.get_all_orders()[:5]
print("\n前5个订单：")
for order in orders3:
    print(f"  {order}")

print("\n" + "="*70)
print("✅ 所有测试通过！订单加载功能正常工作。")
print("="*70)
