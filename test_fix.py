"""
测试订单20是否能被正确调度
"""
import sys
sys.path.append('src')

from config import Config
from scheduler.order_manager import OrderManager
from scheduler.rolling_scheduler import RollingScheduler

# 加载配置和订单
config = Config()
order_manager = OrderManager()
order_manager.load_orders_from_csv('data/sample_orders_small.csv')

# 创建调度器
scheduler = RollingScheduler(config, order_manager)

# 只运行第1天的调度
print("\n" + "="*70)
print("测试第1天调度")
print("="*70)
schedule = scheduler.run_daily_schedule(current_day=0)

# 检查订单20是否被分配
if schedule:
    order_20_allocated = False
    total_allocated = 0
    
    for (order_id, line, slot), qty in schedule.allocation.items():
        if order_id == 20 and qty > 0:
            order_20_allocated = True
            total_allocated += qty
            print(f"✅ 订单20在产线{line}的slot{slot}分配了{qty}单位")
    
    if order_20_allocated:
        print(f"\n✅ 成功！订单20总共分配了 {total_allocated} 单位")
    else:
        print("\n❌ 失败！订单20没有被分配任何产能")
    
    # 显示所有订单的分配情况
    print("\n所有订单分配统计：")
    order_stats = {}
    for (order_id, line, slot), qty in schedule.allocation.items():
        if order_id not in order_stats:
            order_stats[order_id] = 0
        order_stats[order_id] += qty
    
    for order_id in sorted(order_stats.keys()):
        order = order_manager.get_order(order_id)
        print(f"  订单{order_id}: 分配 {order_stats[order_id]}/{order.quantity} ({order_stats[order_id]/order.quantity*100:.1f}%)")
else:
    print("❌ 调度失败，没有生成方案")
