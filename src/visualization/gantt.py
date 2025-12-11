"""
甘特图可视化模块

生成生产调度的甘特图。
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置中文字体，避免乱码
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号


class GanttChart:
    """
    甘特图生成器类
    
    根据调度方案生成可视化的甘特图。
    """
    
    def __init__(self):
        """初始化甘特图生成器"""
        # 默认产品颜色映射
        self.color_map = {
            0: '#CCCCCC',  # 空闲 - 灰色
            1: '#FF6B6B',  # 产品1 - 红色
            2: '#4ECDC4',  # 产品2 - 青色
            3: '#FFE66D',  # 产品3 - 黄色
        }
        self.product_names = {
            0: 'Idle',
            1: 'Product 1',
            2: 'Product 2',
            3: 'Product 3',
        }
    
    def plot_schedule(self, schedule, orders, num_lines=3, max_slots=30, output_path=None):
        """
        绘制调度甘特图
        
        横轴为时间段，纵轴为产线编号，不同颜色表示不同产品。
        
        Args:
            schedule: 调度方案 (Schedule对象)
            orders: 订单列表 (List[Order])
            num_lines: 生产线数量，默认3
            max_slots: 显示的最大slot数，默认30
            output_path: 输出文件路径（可选）
        """
        if schedule is None or not schedule.allocation:
            print("没有调度方案可绘制")
            return
        
        # 创建订单字典
        order_dict = {order.order_id: order for order in orders}
        
        # 获取所有slot
        all_slots = set()
        for (order_id, line, slot), qty in schedule.allocation.items():
            if qty > 0:
                all_slots.add(slot)
        
        if not all_slots:
            print("没有分配可绘制")
            return
        
        min_slot = min(all_slots)
        max_slot = min(max(all_slots), min_slot + max_slots - 1)
        slots_to_plot = range(min_slot, max_slot + 1)
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(16, 6))
        
        # 为每条产线绘制甘特图
        for line in range(1, num_lines + 1):
            for slot in slots_to_plot:
                # 获取该(line, slot)的产品类型
                product = schedule.get_slot_product(line, slot, orders)
                
                if product != 0:  # 非空闲
                    # 绘制矩形
                    rect = mpatches.Rectangle(
                        (slot - 0.4, line - 0.4),
                        0.8, 0.8,
                        facecolor=self.color_map[product],
                        edgecolor='black',
                        linewidth=1
                    )
                    ax.add_patch(rect)
                    
                    # 添加文本标签（产品编号）
                    ax.text(slot, line, f'P{product}',
                           ha='center', va='center',
                           fontsize=8, fontweight='bold')
        
        # 设置坐标轴
        ax.set_xlim(min_slot - 0.5, max_slot + 0.5)
        ax.set_ylim(0.5, num_lines + 0.5)
        ax.set_xlabel('时间段', fontsize=12, fontweight='bold')
        ax.set_ylabel('生产线', fontsize=12, fontweight='bold')
        ax.set_title('生产调度甘特图', fontsize=14, fontweight='bold')
        
        # 设置刻度
        ax.set_xticks(list(slots_to_plot))
        ax.set_yticks(range(1, num_lines + 1))
        ax.set_yticklabels([f'产线{i}' for i in range(1, num_lines + 1)])
        
        # 添加网格
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 添加图例
        legend_patches = []
        for product_id in [1, 2, 3]:
            patch = mpatches.Patch(
                color=self.color_map[product_id],
                label=self.product_names[product_id]
            )
            legend_patches.append(patch)
        ax.legend(handles=legend_patches, loc='upper right', fontsize=10)
        
        plt.tight_layout()
        
        # 保存或显示
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"甘特图已保存至 {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_line_schedule(self, line, schedule, orders, max_slots=30, output_path=None):
        """
        绘制单条生产线的甘特图
        
        Args:
            line: 生产线编号
            schedule: 调度方案
            orders: 订单列表
            max_slots: 显示的最大slot数
            output_path: 输出文件路径（可选）
        """
        if schedule is None:
            print("没有调度方案可绘制")
            return
        
        # 获取该产线的调度
        line_schedule = schedule.get_line_schedule(line)
        
        if not line_schedule:
            print(f"产线 {line} 没有调度")
            return
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(14, 4))
        
        # 绘制每个slot
        for slot, allocations in line_schedule.items():
            if slot > max_slots:
                continue
            
            # 获取产品类型
            order_dict = {order.order_id: order for order in orders}
            if allocations:
                order_id, qty = allocations[0]
                product = order_dict[order_id].product
                
                rect = mpatches.Rectangle(
                    (slot - 0.4, 0.6),
                    0.8, 0.8,
                    facecolor=self.color_map[product],
                    edgecolor='black',
                    linewidth=1
                )
                ax.add_patch(rect)
                ax.text(slot, 1, f'P{product}\nO{order_id}',
                       ha='center', va='center',
                       fontsize=8)
        
        ax.set_xlim(0.5, max_slots + 0.5)
        ax.set_ylim(0, 2)
        ax.set_xlabel('时间段', fontsize=12)
        ax.set_title(f'产线 {line} 调度方案', fontsize=14, fontweight='bold')
        ax.set_yticks([])
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()
    
    def customize_colors(self, color_map):
        """
        自定义产品颜色映射
        
        Args:
            color_map: 颜色映射字典 {product_id: color}
        """
        self.color_map.update(color_map)
