"""
对比两个订单数据集的产能利用情况
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 产能配置
capacity = {1: 50, 2: 60, 3: 55}
num_lines = 3
slots_per_day = 6
num_days = 5

def analyze_dataset(file_path, dataset_name):
    """分析数据集"""
    df = pd.read_csv(file_path)
    
    print(f"\n{'='*60}")
    print(f"{dataset_name}")
    print(f"{'='*60}")
    
    # 基本统计
    total_demand = df['quantity'].sum()
    total_capacity = sum(capacity.values()) * slots_per_day * num_lines * num_days
    overall_util = total_demand / total_capacity * 100
    
    print(f"订单数量: {len(df)}")
    print(f"总需求量: {total_demand}")
    print(f"总产能: {total_capacity}")
    print(f"总体利用率: {overall_util:.1f}%")
    
    # 各产品统计
    print("\n各产品利用率:")
    product_stats = []
    for product in [1, 2, 3]:
        product_df = df[df['product'] == product]
        demand = product_df['quantity'].sum()
        total_cap = capacity[product] * slots_per_day * num_lines * num_days
        util = demand / total_cap * 100
        
        product_stats.append({
            'product': product,
            'demand': demand,
            'capacity': total_cap,
            'utilization': util
        })
        
        print(f"  产品{product}: 需求{demand}, 产能{total_cap}, 利用率{util:.1f}%")
    
    return {
        'name': dataset_name,
        'total_orders': len(df),
        'total_demand': total_demand,
        'total_capacity': total_capacity,
        'overall_util': overall_util,
        'product_stats': product_stats
    }

# 分析两个数据集
delay_stats = analyze_dataset(r'data\delay.csv', 'delay.csv (原始数据)')
delay_full_stats = analyze_dataset(r'data\delay_full.csv', 'delay_full.csv (满负荷数据)')

# 创建对比图表
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('订单数据对比分析', fontsize=16, fontweight='bold')

# 1. 总体对比
ax1 = axes[0, 0]
datasets = ['delay.csv', 'delay_full.csv']
orders = [delay_stats['total_orders'], delay_full_stats['total_orders']]
demands = [delay_stats['total_demand'], delay_full_stats['total_demand']]

x = range(len(datasets))
width = 0.35

bars1 = ax1.bar([i - width/2 for i in x], orders, width, label='订单数量', alpha=0.8)
ax1_twin = ax1.twinx()
bars2 = ax1_twin.bar([i + width/2 for i in x], demands, width, label='总需求量', alpha=0.8, color='orange')

ax1.set_xlabel('数据集')
ax1.set_ylabel('订单数量', color='blue')
ax1_twin.set_ylabel('总需求量', color='orange')
ax1.set_title('订单数量与总需求对比')
ax1.set_xticks(x)
ax1.set_xticklabels(datasets)
ax1.tick_params(axis='y', labelcolor='blue')
ax1_twin.tick_params(axis='y', labelcolor='orange')

# 添加数值标签
for i, (bar, val) in enumerate(zip(bars1, orders)):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(), str(val), 
             ha='center', va='bottom', fontsize=10)
for i, (bar, val) in enumerate(zip(bars2, demands)):
    ax1_twin.text(bar.get_x() + bar.get_width()/2, bar.get_height(), str(val), 
                  ha='center', va='bottom', fontsize=10)

# 2. 产能利用率对比
ax2 = axes[0, 1]
utils = [delay_stats['overall_util'], delay_full_stats['overall_util']]
colors = ['red' if u < 70 else 'orange' if u < 85 else 'green' for u in utils]
bars = ax2.bar(datasets, utils, color=colors, alpha=0.7)
ax2.set_ylabel('产能利用率 (%)')
ax2.set_title('总体产能利用率对比')
ax2.axhline(y=90, color='green', linestyle='--', label='目标利用率 (90%)')
ax2.axhline(y=70, color='orange', linestyle='--', label='警戒线 (70%)')
ax2.legend()

# 添加数值标签
for bar, val in zip(bars, utils):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val:.1f}%', 
             ha='center', va='bottom', fontsize=11, fontweight='bold')

# 3. 各产品利用率对比 - delay.csv
ax3 = axes[1, 0]
products = ['产品1', '产品2', '产品3']
delay_product_utils = [s['utilization'] for s in delay_stats['product_stats']]
colors_delay = ['red' if u < 70 else 'orange' if u < 85 else 'green' for u in delay_product_utils]
bars = ax3.bar(products, delay_product_utils, color=colors_delay, alpha=0.7)
ax3.set_ylabel('产能利用率 (%)')
ax3.set_title('delay.csv - 各产品利用率')
ax3.axhline(y=90, color='green', linestyle='--', alpha=0.5)
ax3.set_ylim(0, 100)

for bar, val in zip(bars, delay_product_utils):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val:.1f}%', 
             ha='center', va='bottom', fontsize=10)

# 4. 各产品利用率对比 - delay_full.csv
ax4 = axes[1, 1]
delay_full_product_utils = [s['utilization'] for s in delay_full_stats['product_stats']]
colors_full = ['red' if u < 70 else 'orange' if u < 85 else 'green' for u in delay_full_product_utils]
bars = ax4.bar(products, delay_full_product_utils, color=colors_full, alpha=0.7)
ax4.set_ylabel('产能利用率 (%)')
ax4.set_title('delay_full.csv - 各产品利用率')
ax4.axhline(y=90, color='green', linestyle='--', alpha=0.5)
ax4.set_ylim(0, 100)

for bar, val in zip(bars, delay_full_product_utils):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val:.1f}%', 
             ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('output/dataset_comparison.png', dpi=150, bbox_inches='tight')
print(f"\n✅ 对比图表已保存到: output/dataset_comparison.png")
plt.show()

# 输出结论
print("\n" + "="*60)
print("结论")
print("="*60)
print(f"\n原始数据 (delay.csv):")
print(f"  - 产能利用率仅 {delay_stats['overall_util']:.1f}%")
print(f"  - 订单量只够约 {delay_stats['total_demand'] / (sum(capacity.values()) * slots_per_day * num_lines):.1f} 天的满负荷生产")
print(f"  - ⚠️ 这就是为什么即使设置5天也有大量生产线空闲的原因！")

print(f"\n满负荷数据 (delay_full.csv):")
print(f"  - 产能利用率达到 {delay_full_stats['overall_util']:.1f}%")
print(f"  - 订单量可以支撑约 {delay_full_stats['total_demand'] / (sum(capacity.values()) * slots_per_day * num_lines):.1f} 天的满负荷生产")
print(f"  - ✅ 适合测试5天的满负荷调度场景")
