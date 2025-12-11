"""
测试解码器的release_slot约束
验证订单只能在 release_slot <= t <= due_slot 的时间窗口内被分配产能
"""
import sys
sys.path.append('src')

from models.order import Order
from models.chromosome import Chromosome
from ga.decoder import Decoder
from config import Config

print("="*70)
print("测试解码器的 release_slot 约束")
print("="*70)

# 初始化配置
config = Config()
decoder = Decoder(config)

# 创建测试订单
# 订单1: release_slot=1, due_slot=6 (可以在slot 1-5生产，必须在slot 6之前完成)
# 订单2: release_slot=7, due_slot=12 (只能在slot 7-11生产，必须在slot 12之前完成)
# 订单3: release_slot=13, due_slot=18 (只能在slot 13-17生产，必须在slot 18之前完成)
orders = [
    Order(order_id=1, product=1, quantity=100, due_slot=6, unit_price=50.0, release_slot=1),
    Order(order_id=2, product=2, quantity=120, due_slot=12, unit_price=60.0, release_slot=7),
    Order(order_id=3, product=3, quantity=90, due_slot=18, unit_price=55.0, release_slot=13),
]

print("\n测试订单：")
for order in orders:
    print(f"  {order}")
    print(f"    时间窗口: slot {order.release_slot} ~ {order.due_slot}")

# 创建染色体
# Gene1: 18个slot (3条线 × 6个slot)，每个slot指定产品类型
# 前6个slot生产产品1，中间6个slot生产产品2，后6个slot生产产品3
gene1 = [1] * 6 + [2] * 6 + [3] * 6  # 3条线 × 6个slot = 18个基因位

# Gene2: 订单优先级
gene2 = [0, 1, 2]  # 按顺序处理订单1, 2, 3

chromosome = Chromosome(gene1=gene1, gene2=gene2)

print("\n染色体配置：")
print(f"  Gene1长度: {len(gene1)}")
print(f"  Gene1内容: {gene1}")
print(f"  Gene2: {gene2}")

# 解码
print("\n开始解码...")
schedule = decoder.decode(chromosome, orders, start_slot=1)

print("\n解码结果：")
print(f"  分配记录数: {len(schedule.allocation)}")

# 检查每个订单的分配情况
for order in orders:
    print(f"\n订单 {order.order_id} (产品{order.product}, 时间窗口: slot {order.release_slot}-{order.due_slot}):")
    order_allocations = [(line, slot, qty) for (oid, line, slot), qty in schedule.allocation.items() if oid == order.order_id]
    
    if order_allocations:
        order_allocations.sort(key=lambda x: x[1])  # 按slot排序
        for line, slot, qty in order_allocations:
            # 验证约束
            in_window = order.release_slot <= slot < order.due_slot
            status = "✅" if in_window else "❌"
            print(f"  {status} Line {line}, Slot {slot}: {qty} 单位")
            if not in_window:
                print(f"      警告：slot {slot} 不在时间窗口 [{order.release_slot}, {order.due_slot}) 内！")
        
        total_allocated = sum(qty for _, _, qty in order_allocations)
        print(f"  总分配: {total_allocated}/{order.quantity} 单位")
    else:
        print(f"  ⚠️  未分配任何产能")

# 验证约束
print("\n" + "="*70)
print("约束验证：")
print("="*70)

all_valid = True
for order in orders:
    order_allocations = [(line, slot, qty) for (oid, line, slot), qty in schedule.allocation.items() if oid == order.order_id]
    
    for line, slot, qty in order_allocations:
        if not (order.release_slot <= slot < order.due_slot):
            print(f"❌ 订单 {order.order_id}: slot {slot} 违反约束 [{order.release_slot}, {order.due_slot})")
            all_valid = False

if all_valid:
    print("✅ 所有分配都满足 release_slot <= t < due_slot 约束！")
else:
    print("❌ 发现违反约束的分配！")

print("\n" + "="*70)
if all_valid:
    print("✅ 测试通过！解码器正确实现了 release_slot 和 due_slot 约束。")
    print("   订单只能在 [release_slot, due_slot) 时间窗口内生产。")
else:
    print("❌ 测试失败！解码器未正确实现约束。")
print("="*70)
