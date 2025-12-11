"""
测试due_slot调整逻辑
验证CSV中的截止时间是否正确转换到截止日期当天早上8点
"""
import sys
sys.path.append('src')

from scheduler.order_manager import OrderManager

print("="*70)
print("测试 due_slot 调整逻辑")
print("="*70)

# 创建订单管理器
om = OrderManager()

# 加载sample_orders_small.csv
print("\n加载 sample_orders_small.csv...")
print("="*70)
om.load_orders_from_csv('data/sample_orders_small.csv', adjust_due_slot=True)

# 获取所有订单
orders = om.get_all_orders()

print("\n" + "="*70)
print("订单截止时间转换结果")
print("="*70)
print(f"{'订单ID':<8} {'原始due_slot':<12} {'调整后':<12} {'说明':<30}")
print("-"*70)

# 手动计算预期值进行对比
test_cases = [
    (1, 6, 7, "第1天任意时段 -> 第2天早上8点"),
    (2, 6, 7, "第1天任意时段 -> 第2天早上8点"),
    (3, 12, 13, "第2天任意时段 -> 第3天早上8点"),
    (4, 12, 13, "第2天任意时段 -> 第3天早上8点"),
    (5, 6, 7, "第1天任意时段 -> 第2天早上8点"),
    (6, 12, 13, "第2天任意时段 -> 第3天早上8点"),
    (7, 18, 19, "第3天任意时段 -> 第4天早上8点"),
    (8, 12, 13, "第2天任意时段 -> 第3天早上8点"),
    (9, 18, 19, "第3天任意时段 -> 第4天早上8点"),
    (10, 18, 19, "第3天任意时段 -> 第4天早上8点"),
]

all_correct = True
for order_id, original_due, expected_due, description in test_cases:
    order = next((o for o in orders if o.order_id == order_id), None)
    if order:
        actual_due = order.due_slot
        status = "✅" if actual_due == expected_due else "❌"
        print(f"{status} {order_id:<8} {original_due:<12} {actual_due:<12} {description}")
        if actual_due != expected_due:
            print(f"   错误: 期望 {expected_due}, 实际 {actual_due}")
            all_correct = False
    else:
        print(f"❌ {order_id:<8} 订单未找到")
        all_correct = False

print("\n" + "="*70)
print("转换公式验证")
print("="*70)

# 验证转换公式
print("\n转换公式: adjusted_due_slot = ((original_due_slot - 1) // 6 + 1) * 6 + 1")
print("\n示例:")
for original in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 18, 24, 30, 36]:
    due_day = (original - 1) // 6
    adjusted = (due_day + 1) * 6 + 1
    print(f"  原始 due_slot={original:2d} -> 第{due_day+1}天 -> 调整为 {adjusted:2d} (第{due_day+2}天早上8点)")

print("\n" + "="*70)
if all_correct:
    print("✅ 所有订单的 due_slot 转换正确！")
else:
    print("❌ 部分订单的 due_slot 转换有误！")
print("="*70)

# 打印订单的时间窗口
print("\n" + "="*70)
print("订单生产时间窗口 [release_slot, due_slot)")
print("="*70)
print(f"{'订单ID':<8} {'release':<10} {'due':<10} {'可生产时段':<30}")
print("-"*70)

for order in sorted(orders, key=lambda x: x.order_id)[:10]:
    time_window = f"slot {order.release_slot} ~ {order.due_slot-1}"
    print(f"{order.order_id:<8} {order.release_slot:<10} {order.due_slot:<10} {time_window}")

print("="*70)
