"""
生成满负荷的订单数据
目标：让5天的产能利用率达到90%以上
"""
import pandas as pd
import random

# 产能配置
capacity = {1: 50, 2: 60, 3: 55}
num_lines = 3
slots_per_day = 6
num_days = 5

# 计算目标订单量（90%产能利用率）
target_utilization = 0.90

orders = []
order_id = 1

for day in range(1, num_days + 1):
    due_slot = day * slots_per_day
    
    # 每天为每种产品生成订单
    for product in [1, 2, 3]:
        daily_capacity = capacity[product] * slots_per_day * num_lines
        target_demand = int(daily_capacity * target_utilization)
        
        # 将每天的需求分成2-4个订单
        num_orders = random.randint(2, 4)
        remaining = target_demand
        
        for i in range(num_orders):
            if i == num_orders - 1:
                # 最后一个订单取剩余量
                quantity = remaining
            else:
                # 随机分配，但保证不超过剩余量的60%
                max_qty = int(remaining * 0.6)
                min_qty = int(remaining * 0.2)
                quantity = random.randint(min_qty, max_qty)
                remaining -= quantity
            
            if quantity > 0:
                # 单价在一定范围内随机
                base_price = {1: 50, 2: 65, 3: 60}
                unit_price = base_price[product] + random.randint(-5, 10)
                
                orders.append({
                    'order_id': order_id,
                    'product': product,
                    'quantity': quantity,
                    'due_slot': due_slot,
                    'unit_price': unit_price
                })
                order_id += 1

# 创建DataFrame
df = pd.DataFrame(orders)

# 保存到CSV
output_path = r'data\delay_full.csv'
df.to_csv(output_path, index=False)

print(f"✅ 已生成 {len(df)} 个订单")
print(f"   保存到: {output_path}")

# 统计信息
print("\n订单统计:")
print(f"总订单数: {len(df)}")
print(f"总需求量: {df['quantity'].sum()}")

print("\n各产品需求:")
for product in [1, 2, 3]:
    product_df = df[df['product'] == product]
    demand = product_df['quantity'].sum()
    total_cap = capacity[product] * slots_per_day * num_lines * num_days
    util = demand / total_cap * 100
    print(f"  产品{product}: {demand} (产能利用率: {util:.1f}%)")

total_demand = df['quantity'].sum()
total_capacity = sum(capacity.values()) * slots_per_day * num_lines * num_days
overall_util = total_demand / total_capacity * 100
print(f"\n总体产能利用率: {overall_util:.1f}%")

print("\n按天分布:")
for day in range(1, num_days + 1):
    due_slot = day * slots_per_day
    day_df = df[df['due_slot'] == due_slot]
    print(f"  第{day}天 (due_slot={due_slot}): {len(day_df)}个订单, 总量{day_df['quantity'].sum()}")
