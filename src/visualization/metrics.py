"""
指标可视化模块

展示调度方案的关键性能指标。
"""
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置中文字体，避免乱码
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号


class MetricsVisualizer:
    """
    指标可视化器类
    
    生成各类性能指标的可视化图表。
    """
    
    def __init__(self):
        """初始化指标可视化器"""
        self.colors = {
            'revenue': '#4CAF50',
            'cost': '#FF9800',
            'penalty': '#F44336',
            'profit': '#2196F3'
        }
    
    def plot_profit_breakdown(self, stats, output_path=None):
        """
        绘制利润分解图
        
        展示总收入、总成本、总罚款和总利润。
        
        Args:
            stats: 累计统计数据（dict）或调度方案（Schedule对象）
            output_path: 输出文件路径（可选）
        """
        if stats is None:
            print("没有数据可绘制")
            return
        
        # 兼容两种输入：dict（累计统计）或Schedule对象
        if isinstance(stats, dict):
            revenue = stats.get('total_revenue', 0)
            cost = stats.get('total_cost', 0)
            penalty = stats.get('total_penalty', 0)
            profit = stats.get('total_profit', 0)
        else:
            # Schedule对象
            revenue = stats.revenue
            cost = stats.cost
            penalty = stats.penalty
            profit = stats.profit
        
        # 数据
        categories = ['收入', '成本', '罚款', '利润']
        values = [revenue, cost, penalty, profit]
        colors = [self.colors['revenue'], self.colors['cost'], 
                 self.colors['penalty'], self.colors['profit']]
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(categories, values, color=colors, alpha=0.8, edgecolor='black')
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.2f}',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('金额 (元)', fontsize=12, fontweight='bold')
        ax.set_title('利润分解图', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"利润分解图已保存至 {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_order_completion_rate(self, orders, stats, output_path=None):
        """
        绘制订单完成率统计
        
        Args:
            orders: 订单列表
            stats: 累计统计数据（dict）或调度方案（Schedule对象）
            output_path: 输出文件路径（可选）
        """
        if stats is None or not orders:
            print("没有数据可绘制")
            return
        
        # 统计完成情况（基于订单的实际状态）
        completed_count = 0
        partial_count = 0
        not_started_count = 0
        
        for order in orders:
            if order.is_completed():
                completed_count += 1
            elif order.remaining < order.quantity:
                partial_count += 1
            else:
                not_started_count += 1
        
        # 创建饼图
        fig, ax = plt.subplots(figsize=(8, 8))
        
        sizes = [completed_count, partial_count, not_started_count]
        labels = ['已完成', '部分完成', '未开始']
        colors = ['#4CAF50', '#FF9800', '#F44336']
        explode = (0.1, 0, 0)
        
        ax.pie(sizes, explode=explode, labels=labels, colors=colors,
              autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')
        ax.set_title('订单完成状态', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"订单完成图已保存至 {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_line_utilization(self, schedule, num_lines=3, output_path=None):
        """
        绘制生产线利用率
        
        Args:
            schedule: 调度方案
            num_lines: 生产线数量
            output_path: 输出文件路径（可选）
        """
        if schedule is None:
            print("No schedule to plot.")
            return
        
        # 统计每条产线的工作slot数
        line_working_slots = {line: set() for line in range(1, num_lines + 1)}
        total_slots = 0
        
        for (order_id, line, slot), qty in schedule.allocation.items():
            if qty > 0:
                line_working_slots[line].add(slot)
                total_slots = max(total_slots, slot)
        
        # 计算利用率
        utilization = []
        for line in range(1, num_lines + 1):
            if total_slots > 0:
                util = len(line_working_slots[line]) / total_slots * 100
            else:
                util = 0
            utilization.append(util)
        
        # 创建柱状图
        fig, ax = plt.subplots(figsize=(10, 6))
        
        lines = [f'产线{i}' for i in range(1, num_lines + 1)]
        x_pos = np.arange(len(lines))
        
        bars = ax.bar(x_pos, utilization, color='#2196F3', alpha=0.8, edgecolor='black')
        
        # 添加数值标签
        for bar, util in zip(bars, utilization):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{util:.1f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_xlabel('生产线', fontsize=12, fontweight='bold')
        ax.set_ylabel('利用率 (%)', fontsize=12, fontweight='bold')
        ax.set_title('生产线利用率', fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(lines)
        ax.set_ylim(0, 110)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"产线利用率图已保存至 {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def print_metrics(self, schedule, orders):
        """
        打印关键指标到控制台
        
        Args:
            schedule: 调度方案
            orders: 订单列表
        """
        if schedule is None:
            print("没有可用的调度方案")
            return
        
        stats = schedule.get_statistics(orders)
        
        print("\n" + "="*60)
        print("调度指标")
        print("="*60)
        print(f"\n财务指标:")
        print(f"  总收入:        ¥{schedule.revenue:,.2f}")
        print(f"  总成本:        ¥{schedule.cost:,.2f}")
        print(f"  总罚款:        ¥{schedule.penalty:,.2f}")
        print(f"  总利润:        ¥{schedule.profit:,.2f}")
        
        print(f"\n订单指标:")
        print(f"  总订单数:      {stats['total_orders']}")
        print(f"  完成订单数:    {stats['completed_orders']}")
        print(f"  按期完成率:    {stats['on_time_rate']*100:.1f}%")
        print(f"  平均完成率:    {stats['avg_completion_rate']*100:.1f}%")
        
        print(f"\n生产指标:")
        print(f"  工作时段数:    {stats['total_working_slots']}")
        print("="*60 + "\n")
    
    def generate_report(self, stats, orders, output_dir='output', schedule=None):
        """
        生成综合报告（所有图表）
        
        Args:
            stats: 累计统计数据（dict）
            orders: 订单列表
            output_dir: 输出目录
            schedule: 调度方案（用于产线利用率图，可选）
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n正在生成综合报告至 {output_dir}/...")
        
        # 生成各种图表
        self.plot_profit_breakdown(stats, f"{output_dir}/profit_breakdown.png")
        self.plot_order_completion_rate(orders, stats, f"{output_dir}/order_completion.png")
        
        # 产线利用率图需要Schedule对象
        if schedule is not None:
            self.plot_line_utilization(schedule, output_path=f"{output_dir}/line_utilization.png")
        
        print(f"报告生成完成!\n")
