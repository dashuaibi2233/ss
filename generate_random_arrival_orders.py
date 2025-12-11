"""
生成随机到达的测试订单数据
用于验证订单随机到达和每天8点调度的效果
"""
import csv
import random

# 配置参数
num_orders = 20
num_products = 3
num_days = 10  # 订单在前10天内到达
slots_per_day = 6

# 生成订单
orders = []

for i in range(1, num_orders + 1):
    order_id = i
    product = random.randint(1, num_products)
    quantity = random.randint(80, 300)
    
    # release_slot: 在前10天内随机分布
    # 让订单在不同天到达，不要都在第一天
    release_day = random.randint(0, num_days - 1)  # 0-9天
    release_slot_in_day = random.randint(1, slots_per_day)  # 1-6
    release_slot = release_day * slots_per_day + release_slot_in_day
    
    # due_slot: 必须大于release_slot，给订单2-5天的生产时间
    production_days = random.randint(2, 5)
    due_day = release_day + production_days
    due_slot_in_day = random.randint(1, slots_per_day)
    due_slot = due_day * slots_per_day + due_slot_in_day
    
    # unit_price: 根据产品类型设置
    base_prices = {1: 50, 2: 60, 3: 55}
    unit_price = base_prices[product] + random.randint(-5, 10)
    
    orders.append({
        'order_id': order_id,
        'product': product,
        'quantity': quantity,
        'release_slot': release_slot,
        'due_slot': due_slot,
        'unit_price': unit_price
    })

# 按release_slot排序（方便查看）
orders.sort(key=lambda x: (x['release_slot'], x['order_id']))

# 写入CSV文件
output_file = 'data/sample_orders_random.csv'
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    fieldnames = ['order_id', 'product', 'quantity', 'release_slot', 'due_slot', 'unit_price']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(orders)

print(f"✅ 已生成 {output_file}")
print(f"   订单数: {len(orders)}")
print(f"\n订单到达分布（按天统计）:")

# 统计每天到达的订单数
arrival_by_day = {}
for order in orders:
    day = (order['release_slot'] - 1) // slots_per_day + 1
    if day not in arrival_by_day:
        arrival_by_day[day] = []
    arrival_by_day[day].append(order['order_id'])

for day in sorted(arrival_by_day.keys()):
    order_ids = arrival_by_day[day]
    print(f"  第{day}天: {len(order_ids)}个订单到达 (订单{min(order_ids)}-{max(order_ids)})")

print(f"\n前5个订单预览:")
for order in orders[:5]:
    release_day = (order['release_slot'] - 1) // slots_per_day + 1
    due_day = (order['due_slot'] - 1) // slots_per_day + 1
    print(f"  订单{order['order_id']}: 产品{order['product']}, "
          f"数量{order['quantity']}, "
          f"第{release_day}天到达(slot {order['release_slot']}), "
          f"第{due_day}天截止(slot {order['due_slot']})")

print(f"\n📊 数据特征:")
print(f"  - 订单在前{num_days}天内随机到达")
print(f"  - 每个订单有2-5天的生产时间窗口")
print(f"  - 部分订单可能因产能不足而延期，产生罚款")
print(f"  - 适合测试滚动调度和订单随机到达机制")
