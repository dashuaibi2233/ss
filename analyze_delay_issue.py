"""
分析delay.csv数据的产能利用问题
"""
import pandas as pd

# 读取数据
df = pd.read_csv(r'data\delay.csv')

print("=" * 60)
print("订单数据分析")
print("=" * 60)

# 按产品统计需求
print("\n各产品总需求量:")
product_demand = df.groupby('product')['quantity'].sum()
for product, demand in product_demand.items():
    print(f"  产品{product}: {demand}")

print(f"\n总需求量: {df['quantity'].sum()}")
print(f"订单数量: {len(df)}")

# 产能配置
capacity = {1: 50, 2: 60, 3: 55}
num_lines = 3
slots_per_day = 6
num_days = 5

print("\n" + "=" * 60)
print("产能配置")
print("=" * 60)
print(f"生产线数量: {num_lines}")
print(f"每天时间段数: {slots_per_day}")
print(f"模拟天数: {num_days}")

print("\n各产品产能:")
for product, cap in capacity.items():
    daily_cap = cap * slots_per_day * num_lines
    total_cap = daily_cap * num_days
    print(f"  产品{product}: {cap}/slot × {slots_per_day} slots × {num_lines} 线 = {daily_cap}/天")
    print(f"           {num_days}天总产能: {total_cap}")

# 计算产能利用率
print("\n" + "=" * 60)
print("产能利用率分析")
print("=" * 60)

for product in [1, 2, 3]:
    demand = product_demand.get(product, 0)
    daily_cap = capacity[product] * slots_per_day * num_lines
    total_cap = daily_cap * num_days
    utilization = demand / total_cap * 100
    
    print(f"\n产品{product}:")
    print(f"  需求量: {demand}")
    print(f"  5天总产能: {total_cap}")
    print(f"  产能利用率: {utilization:.1f}%")
    
    if utilization < 100:
        idle_capacity = total_cap - demand
        idle_slots = idle_capacity / capacity[product]
        print(f"  空闲产能: {idle_capacity} (约 {idle_slots:.1f} 个slot)")

# 总体分析
total_demand = df['quantity'].sum()
total_capacity = sum(capacity.values()) * slots_per_day * num_lines * num_days
overall_utilization = total_demand / total_capacity * 100

print("\n" + "=" * 60)
print("总体产能利用率")
print("=" * 60)
print(f"总需求: {total_demand}")
print(f"总产能: {total_capacity}")
print(f"总体利用率: {overall_utilization:.1f}%")

if overall_utilization < 100:
    print(f"\n⚠️ 问题发现: 即使5天也无法达到满产能!")
    print(f"   空闲产能: {total_capacity - total_demand}")
    print(f"   空闲比例: {100 - overall_utilization:.1f}%")
    
    # 计算需要多少天才能满产能
    daily_total_cap = sum(capacity.values()) * slots_per_day * num_lines
    days_needed = total_demand / daily_total_cap
    print(f"\n   如果要达到满产能，需要约 {days_needed:.1f} 天的订单量")
    print(f"   当前订单量只够 {days_needed:.1f} 天的生产")

# 按due_slot分析订单分布
print("\n" + "=" * 60)
print("订单时间分布")
print("=" * 60)
due_slot_dist = df.groupby('due_slot').agg({
    'order_id': 'count',
    'quantity': 'sum'
}).rename(columns={'order_id': 'order_count', 'quantity': 'total_quantity'})

for due_slot, row in due_slot_dist.iterrows():
    day = (due_slot - 1) // slots_per_day + 1
    print(f"due_slot={due_slot} (第{day}天): {row['order_count']}个订单, 总量{row['total_quantity']}")
