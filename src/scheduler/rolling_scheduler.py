"""
滚动调度模块

实现每日8点的滚动调度逻辑。
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule import Schedule
from ga.engine import run_ga
from local_search.ils_vns import improve_solution
from ga.decoder import Decoder


class RollingScheduler:
    """
    滚动调度器类
    
    负责每日调度的触发和执行。
    """
    
    def __init__(self, config, order_manager):
        """
        初始化滚动调度器
        
        Args:
            config: 配置对象
            order_manager: 订单管理器
        """
        self.config = config
        self.order_manager = order_manager
        self.current_schedule = None
        self.frozen_slots = []
        
        # 累计统计数据
        self.cumulative_stats = {
            'total_revenue': 0.0,
            'total_cost': 0.0,
            'total_penalty': 0.0,
            'total_profit': 0.0,
            'daily_results': []  # 存储每日结果
        }  # 已冻结的时间段
    
    def run_daily_schedule(self, current_day):
        """
        执行每日调度（每天 8 点触发）
        
        按照设计大纷3.6节滚动调度策略：
        1. 收集所有未完成订单及新订单，形成订单池
        2. 冻结当前时间之前已经执行的调度
        3. 对未来 H 个时间段运行 GA + 局部搜索
        4. 将方案映射回全局时间轴，更新未来生产计划
        
        Args:
            current_day: 当前天数（0-based）
            
        Returns:
            Schedule: 生成的调度方案
        """
        print("\n" + "="*70)
        print(f"第 {current_day + 1} 天调度 - 早上8:00")
        print("="*70)
        
        # 步骤1: 计算当前起始slot
        current_slot = self.order_manager.time_to_slot(current_day, hour=8)
        print(f"📅 当前起始slot: {current_slot} (第{current_day + 1}天早上8点)")
        
        # 步骤2: 准备订单池（只包含已到达且未完成的订单）
        # 根据 release_slot <= current_slot 过滤订单
        orders = self.order_manager.get_eligible_orders(current_slot)
        
        # 统计所有订单和未到达订单
        all_orders = self.order_manager.get_all_orders()
        total_unfinished = sum(1 for o in all_orders if o.remaining > 0)
        future_orders = [o for o in all_orders if o.remaining > 0 and o.release_slot > current_slot]
        
        print(f"📦 订单池统计:")
        print(f"  - 总未完成订单: {total_unfinished} 个")
        print(f"  - 已到达可调度: {len(orders)} 个 (release_slot <= {current_slot})")
        print(f"  - 未来订单: {len(future_orders)} 个 (release_slot > {current_slot})")
        
        if orders:
            release_slots = [o.release_slot for o in orders]
            print(f"  - 订单池release_slot范围: [{min(release_slots)}, {max(release_slots)}]")
        
        if not orders:
            print("⚠️  没有已到达的订单，跳过调度")
            
            # 即使没有订单，也要添加当天的财务数据（全为0），确保索引对齐
            self.cumulative_stats['daily_results'].append({
                'day': current_day + 1,
                'revenue': 0.0,
                'cost': 0.0,
                'penalty': 0.0,
                'profit': 0.0
            })
            
            return None
        
        # 步骤3: 冻结已执行的 slot
        self.freeze_executed_slots(current_slot)
        print(f"🔒 冻结时段数: {len(self.frozen_slots)}")
        
        # 步骤3: 运行优化算法 (GA + 局部搜索)
        planning_horizon = self.config.SLOTS_PER_DAY * 10  # 默认规划 5 天
        optimized_schedule = self.run_optimization(orders, planning_horizon, current_slot)
        
        # 步骤4: 更新当前调度方案
        self.update_schedule(optimized_schedule)
        
        # 步骤5: 执行当天的生产（更新订单状态）并统计当天实际执行的数据
        daily_stats = self.execute_daily_production(current_day)
        
        # 步骤6: 累计统计数据（只累计当天实际执行的部分）
        self.cumulative_stats['daily_results'].append({
            'day': current_day + 1,
            'revenue': daily_stats['revenue'],
            'cost': daily_stats['cost'],
            'penalty': daily_stats['penalty'],
            'profit': daily_stats['profit']
        })
        
        # 打印当天实际业务指标
        orders = self.order_manager.get_all_orders()
        total_orders = len(orders)
        completed_orders = sum(1 for order in orders if order.is_completed())
        
        print("\n" + "="*70)
        print(f"📊 第 {current_day + 1} 天实际业务指标")
        print("="*70)
        print(f"  收入: ¥{daily_stats['revenue']:,.2f} (当天实际生产)")
        print(f"  成本: ¥{daily_stats['cost']:,.2f} (当天人工成本)")
        print(f"  罚款: ¥{daily_stats['penalty']:,.2f} (当天新增罚款)")
        print(f"  利润: ¥{daily_stats['profit']:,.2f}")
        print(f"  截止当天累计完成: {completed_orders}/{total_orders} ({completed_orders/total_orders*100:.1f}%)")
        print("="*70 + "\n")
        
        return optimized_schedule
    
    def freeze_executed_slots(self, current_slot):
        """
        冻结已执行的时间段
        
        将当前时间之前的所有 slot 标记为已冻结，不再修改。
        
        Args:
            current_slot: 当前时间段索引 (1-based)
        """
        # 冻结所有小于 current_slot 的时间段
        self.frozen_slots = list(range(1, current_slot))
    
    def run_optimization(self, orders, planning_horizon, start_slot):
        """
        运行优化算法
        
        调用 GA + 局部搜索获取最优调度方案。
        
        Args:
            orders: 订单列表 (List[Order])
            planning_horizon: 规划时域（slot 数量）
            start_slot: 当前规划窗口在全局时间轴上的起始 slot（1-based）
            
        Returns:
            Schedule: 优化后的调度方案
        """
        print(
            f"\n正在为 {len(orders)} 个订单进行 {planning_horizon} 个时段的优化"
            f"（起始slot={start_slot}）..."
        )
        
        # 阶段1: 运行遗传算法
        print("\n阶段1: 遗传算法")
        ga_best = run_ga(
            orders,
            self.config,
            planning_horizon=planning_horizon,
            start_slot=start_slot,
        )
        
        # 阶段2: 局部搜索改进
        print("\n阶段2: 局部搜索 (ILS/VNS)")
        improved_solution = improve_solution(
            ga_best, orders, self.config, start_slot=start_slot
        )
        
        # 解码为 Schedule 对象
        decoder = Decoder(self.config)
        final_schedule = decoder.decode(
            improved_solution, orders, start_slot=start_slot
        )
        final_schedule.calculate_metrics(orders, self.config.LABOR_COSTS, self.config.PENALTY_RATE)
        
        # 停工保护：预估当日利润为负则当日停工
        if getattr(self.config, "ENABLE_STOPLOSS", False):
            day_start = start_slot
            day_end = start_slot + self.config.SLOTS_PER_DAY - 1
            # 预估当日收入
            order_prices = {o.order_id: o.unit_price for o in orders}
            day_revenue = 0.0
            working_lines_by_slot = {}
            for (order_id, line, slot), qty in final_schedule.allocation.items():
                if day_start <= slot <= day_end and qty > 0:
                    day_revenue += qty * order_prices.get(order_id, 0.0)
                    working_lines_by_slot.setdefault(slot, set()).add(line)
            # 预估当日成本
            day_cost = 0.0
            for slot, lines in working_lines_by_slot.items():
                idx = (slot - 1) % self.config.SLOTS_PER_DAY
                day_cost += self.config.LABOR_COSTS[idx] * len(lines)
            # 预估当日罚款（不改变订单状态）
            current_slot = start_slot
            day_penalty = 0.0
            for o in orders:
                if current_slot >= o.due_slot and o.remaining > 0 and not getattr(o, "penalized", False):
                    day_penalty += o.quantity * o.unit_price * self.config.PENALTY_RATE
            day_profit = day_revenue - day_cost - day_penalty
            if day_profit < 0:
                # 移除当日分配
                keys_to_remove = [k for k in final_schedule.allocation.keys() if day_start <= k[2] <= day_end]
                for k in keys_to_remove:
                    del final_schedule.allocation[k]
                # 重建完成量
                final_schedule.order_completion = {}
                for (order_id, line, slot), qty in final_schedule.allocation.items():
                    if qty > 0:
                        final_schedule.order_completion[order_id] = final_schedule.order_completion.get(order_id, 0) + qty
                # 重新计算指标
                final_schedule.calculate_metrics(orders, self.config.LABOR_COSTS, self.config.PENALTY_RATE)
                print("⚠️ 已触发停工保护：当天预估利润为负，已设置当日停工")
        
        print(f"\n优化完成（算法内部指标，用于优化过程）")
        print(f"GA适应度: ¥{final_schedule.profit:.2f}")
        print(f"  规划期总收入: ¥{final_schedule.revenue:.2f}")
        print(f"  规划期总成本: ¥{final_schedule.cost:.2f}")
        print(f"  规划期总罚款: ¥{final_schedule.penalty:.2f} (未来{planning_horizon}个slot的预估)")
        
        return final_schedule
    
    def update_schedule(self, new_schedule):
        """
        更新当前调度方案
        
        将新的调度方案合并到全局调度中，保留已冻结 slot 的分配。
        
        Args:
            new_schedule: 新的调度方案 (Schedule)
        """
        if self.current_schedule is None:
            # 第一次调度，直接使用新方案
            self.current_schedule = new_schedule
        else:
            # 合并方案：保留冻结 slot，更新未来 slot
            for (order_id, line, slot), qty in new_schedule.allocation.items():
                if slot not in self.frozen_slots:
                    # 只更新未冻结的 slot
                    self.current_schedule.allocation[(order_id, line, slot)] = qty
            
            # 重新计算指标
            orders = self.order_manager.get_all_orders()
            self.current_schedule.calculate_metrics(
                orders, 
                self.config.LABOR_COSTS, 
                self.config.PENALTY_RATE
            )
    
    def get_current_schedule(self):
        """
        获取当前调度方案
        
        Returns:
            Schedule: 当前调度方案
        """
        return self.current_schedule
    
    def execute_daily_production(self, current_day):
        """
        执行当天的生产（模拟一天的生产过程）
        
        将当天规划的所有slot的生产结果更新到订单的remaining中，
        并返回当天实际执行的收入、成本、罚款统计。
        
        Args:
            current_day: 当前天数（0-based）
            
        Returns:
            dict: 当天实际执行的统计数据 {'revenue', 'cost', 'penalty', 'profit'}
        """
        if self.current_schedule is None:
            return {'revenue': 0.0, 'cost': 0.0, 'penalty': 0.0, 'profit': 0.0}
        
        # 计算当天的slot范围（假设每天6个slot）
        slots_per_day = self.config.SLOTS_PER_DAY
        day_start_slot = current_day * slots_per_day + 1
        day_end_slot = (current_day + 1) * slots_per_day
        
        # 统计当天实际执行的数据
        daily_revenue = 0.0
        daily_cost = 0.0
        completed_orders_today = set()
        
        # 执行当天所有slot的生产
        for slot in range(day_start_slot, day_end_slot + 1):
            slot_stats = self.execute_slot(slot)
            daily_revenue += slot_stats['revenue']
            daily_cost += slot_stats['cost']
            completed_orders_today.update(slot_stats['completed_orders'])
        
        # 计算当天的罚款：检查今天之前到期的订单
        # 按"截止时间触发"机制：只罚今天新到期且未完成的订单
        daily_penalty = self.calculate_daily_penalty(current_day)
        
        daily_profit = daily_revenue - daily_cost - daily_penalty
        
        return {
            'revenue': daily_revenue,
            'cost': daily_cost,
            'penalty': daily_penalty,
            'profit': daily_profit
        }
    
    def execute_slot(self, slot):
        """
        执行指定 slot 的生产
        
        更新订单完成量，并冻结该 slot，返回该slot的统计数据。
        
        Args:
            slot: 时间段索引
            
        Returns:
            dict: 该slot的统计数据 {'revenue', 'cost', 'completed_orders'}
        """
        slot_revenue = 0.0
        slot_cost = 0.0
        completed_orders = set()
        
        if self.current_schedule is None:
            return {'revenue': slot_revenue, 'cost': slot_cost, 'completed_orders': completed_orders}
        
        # 统计该slot有哪些产线在工作
        working_lines_set = set()
        
        # 获取该 slot 的所有分配
        for (order_id, line, s), qty in self.current_schedule.allocation.items():
            if s == slot and qty > 0:
                # 更新订单的remaining（减少剩余量）
                order = self.order_manager.get_order(order_id)
                if order:
                    old_remaining = order.remaining
                    new_remaining = max(0, order.remaining - qty)
                    order.remaining = new_remaining
                    
                    # 计算该slot为该订单产生的收入
                    actual_produced = old_remaining - new_remaining
                    slot_revenue += actual_produced * order.unit_price
                    
                    # 检查订单是否完成
                    if new_remaining == 0 and old_remaining > 0:
                        completed_orders.add(order_id)
                        # 记录完成时的时段
                        if order.completed_slot is None:
                            order.completed_slot = slot
                    
                    # 记录该产线在工作
                    working_lines_set.add(line)
        
        # 计算该slot的人工成本（每条工作的产线都要计成本）
        if working_lines_set:
            # slot是1-based，labor_costs是0-based数组
            slot_index = (slot - 1) % self.config.SLOTS_PER_DAY
            slot_cost = self.config.LABOR_COSTS[slot_index] * len(working_lines_set)
        
        # 冻结该 slot
        if slot not in self.frozen_slots:
            self.frozen_slots.append(slot)
        
        return {
            'revenue': slot_revenue,
            'cost': slot_cost,
            'completed_orders': completed_orders
        }
    
    def get_statistics(self):
        """
        获取当前调度的统计信息
        
        Returns:
            dict: 统计信息
        """
        if self.current_schedule is None:
            return {}
        
        orders = self.order_manager.get_all_orders()
        return self.current_schedule.get_statistics(orders)
    
    def get_cumulative_statistics(self):
        """
        获取累计统计信息（多日汇总）
        
        Returns:
            dict: 累计统计信息
        """
        if not self.cumulative_stats['daily_results']:
            return {
                'total_revenue': 0.0,
                'total_cost': 0.0,
                'total_penalty': 0.0,
                'total_profit': 0.0
            }
        
        # 累计所有天的收入、成本、罚款（都是增量，可累加）
        total_revenue = sum(day['revenue'] for day in self.cumulative_stats['daily_results'])
        total_cost = sum(day['cost'] for day in self.cumulative_stats['daily_results'])
        total_penalty = sum(day['penalty'] for day in self.cumulative_stats['daily_results'])
        
        # 总利润 = 总收入 - 总成本 - 总罚款
        total_profit = total_revenue - total_cost - total_penalty
        
        # 验证：总利润应该等于每日利润之和
        profit_sum = sum(day['profit'] for day in self.cumulative_stats['daily_results'])
        assert abs(total_profit - profit_sum) < 0.01, \
            f"利润计算不一致: {total_profit} != {profit_sum}"
        
        # 获取最终订单完成情况
        orders = self.order_manager.get_all_orders()
        completed_orders = sum(1 for order in orders if order.remaining <= 0)
        on_time_orders = sum(1 for order in orders if order.remaining <= 0)  # 简化版
        
        return {
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_penalty': total_penalty,
            'total_profit': total_profit,
            'total_orders': len(orders),
            'completed_orders': completed_orders,
            'on_time_rate': on_time_orders / len(orders) if orders else 0,
            'daily_results': self.cumulative_stats['daily_results']
        }
    
    def calculate_daily_penalty(self, current_day):
        """
        计算当天的罚款（按截止时间触发）
        
        检查今天之前到期的订单：
        - 如果订单未完成且之前没罚过，就罚一次
        - 标记 order.penalized = True 避免重复罚款
        
        注意：due_slot是截止日期当天早上8点，当current_slot >= due_slot时订单已超期
        
        Args:
            current_day: 当前天数（0-based）
            
        Returns:
            float: 当天新增罚款金额
        """
        daily_penalty = 0.0
        orders = self.order_manager.get_all_orders()
        
        # 计算当天早上8点的slot（每天调度的起始时刻）
        current_slot = self.order_manager.time_to_slot(current_day, hour=8)
        
        for order in orders:
            # 检查：订单截止时间 <= 当前时刻（当天早上8点）
            # 由于due_slot是截止日期当天早上8点，所以 current_slot >= due_slot 表示已超期
            if current_slot >= order.due_slot:
                # 检查：订单未完成 且 之前没罚过
                if order.remaining > 0 and not order.penalized:
                    # 罚款 = 订单总金额 × 10%
                    penalty = order.quantity * order.unit_price * self.config.PENALTY_RATE
                    daily_penalty += penalty
                    
                    # 标记已罚款，避免重复
                    order.penalized = True
                    
                    print(f"  ⚠️  订单 {order.order_id} 到期未完成（due_slot={order.due_slot}），罚款 ¥{penalty:.2f}")
        
        return daily_penalty
    
    def calculate_final_penalty(self):
        """
        计算最终的总罚款（用于累计汇总）
        
        遍历所有订单，对于未完成的订单（remaining > 0），
        罚款 = 订单总金额 × 10%
        
        Returns:
            float: 总罚款金额
        """
        total_penalty = 0.0
        orders = self.order_manager.get_all_orders()
        
        for order in orders:
            if order.remaining > 0:
                # 订单未完成，罚款 = 订单总金额 × 罚款比例
                penalty = order.quantity * order.unit_price * self.config.PENALTY_RATE
                total_penalty += penalty
        
        return total_penalty
