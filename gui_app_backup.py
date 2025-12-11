"""
智能制造生产调度系统 - GUI界面

基于Streamlit构建的交互式GUI，提供配置管理、订单上传、调度运行和结果可视化功能。
"""
import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import json

# 设置路径
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / 'src'))

from src.service import load_default_config, load_orders, run_schedule
from src.visualization.gantt import GanttChart
from src.visualization.metrics import MetricsVisualizer

# 页面配置
st.set_page_config(
    page_title="智能制造生产调度系统",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session_state
if 'config' not in st.session_state:
    st.session_state.config = load_default_config()
if 'orders' not in st.session_state:
    st.session_state.orders = None
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = None
if 'simulation_result' not in st.session_state:
    st.session_state.simulation_result = None  # 完整模拟结果
if 'current_day' not in st.session_state:
    st.session_state.current_day = 0  # 当前查看的天数（0-based）
if 'num_days' not in st.session_state:
    st.session_state.num_days = 3  # 模拟天数
if 'output_dir' not in st.session_state:
    st.session_state.output_dir = str(ROOT / 'output')
    os.makedirs(st.session_state.output_dir, exist_ok=True)

# 标题
st.title("🏭 智能制造生产调度系统")
st.markdown("---")

# 侧边栏 - 快速配置
with st.sidebar:
    st.header("⚙️ 快速配置")
    
    # GA参数
    st.subheader("遗传算法参数")
    pop_size = st.number_input("种群规模", min_value=10, max_value=100, value=st.session_state.config.POPULATION_SIZE, step=10)
    max_gen = st.number_input("最大迭代次数", min_value=10, max_value=200, value=st.session_state.config.MAX_GENERATIONS, step=10)
    crossover_rate = st.slider("交叉概率", 0.0, 1.0, st.session_state.config.CROSSOVER_RATE, 0.05)
    mutation_rate = st.slider("变异概率", 0.0, 1.0, st.session_state.config.MUTATION_RATE, 0.05)
    elite_size = st.number_input("精英个体数", min_value=1, max_value=10, value=st.session_state.config.ELITE_SIZE, step=1)
    
    # 局部搜索参数
    st.subheader("局部搜索参数")
    max_ls = st.number_input("最大迭代次数", min_value=10, max_value=100, value=st.session_state.config.MAX_LS_ITERATIONS, step=10)
    
    # 应用配置按钮
    if st.button("💾 应用配置", use_container_width=True):
        st.session_state.config.POPULATION_SIZE = pop_size
        st.session_state.config.MAX_GENERATIONS = max_gen
        st.session_state.config.CROSSOVER_RATE = crossover_rate
        st.session_state.config.MUTATION_RATE = mutation_rate
        st.session_state.config.ELITE_SIZE = elite_size
        st.session_state.config.MAX_LS_ITERATIONS = max_ls
        st.success("✅ 配置已更新")
    
    # 重置配置按钮
    if st.button("🔄 重置为默认", use_container_width=True):
        st.session_state.config = load_default_config()
        st.rerun()

# 主内容区域 - 使用Tab
tab1, tab2, tab3, tab4 = st.tabs(["📋 配置详情", "📦 订单管理", "🚀 调度运行", "📊 结果分析"])

# Tab 1: 配置详情
with tab1:
    st.header("📋 系统配置详情")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("生产线配置")
        st.write(f"**生产线数量:** {st.session_state.config.NUM_LINES}")
        st.write(f"**产品种类:** {st.session_state.config.NUM_PRODUCTS}")
        st.write(f"**每天时间段数:** {st.session_state.config.SLOTS_PER_DAY}")
        
        st.subheader("产能配置")
        capacity_df = pd.DataFrame([
            {"产品ID": k, "产能(单位/slot)": v} 
            for k, v in st.session_state.config.CAPACITY.items()
        ])
        st.dataframe(capacity_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("遗传算法参数")
        st.write(f"**种群规模:** {st.session_state.config.POPULATION_SIZE}")
        st.write(f"**最大迭代次数:** {st.session_state.config.MAX_GENERATIONS}")
        st.write(f"**交叉概率:** {st.session_state.config.CROSSOVER_RATE}")
        st.write(f"**变异概率:** {st.session_state.config.MUTATION_RATE}")
        st.write(f"**精英个体数:** {st.session_state.config.ELITE_SIZE}")
        
        st.subheader("局部搜索参数")
        st.write(f"**最大迭代次数:** {st.session_state.config.MAX_LS_ITERATIONS}")
        
        st.subheader("成本参数")
        st.write(f"**违约罚款比例:** {st.session_state.config.PENALTY_RATE * 100}%")
    
    # 导出配置
    st.subheader("配置导入/导出")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        config_dict = {
            "POPULATION_SIZE": st.session_state.config.POPULATION_SIZE,
            "MAX_GENERATIONS": st.session_state.config.MAX_GENERATIONS,
            "CROSSOVER_RATE": st.session_state.config.CROSSOVER_RATE,
            "MUTATION_RATE": st.session_state.config.MUTATION_RATE,
            "ELITE_SIZE": st.session_state.config.ELITE_SIZE,
            "MAX_LS_ITERATIONS": st.session_state.config.MAX_LS_ITERATIONS,
            "CAPACITY": st.session_state.config.CAPACITY,
        }
        config_json = json.dumps(config_dict, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 导出配置(JSON)",
            data=config_json,
            file_name="config.json",
            mime="application/json",
            use_container_width=True
        )

# Tab 2: 订单管理
with tab2:
    st.header("📦 订单管理")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("上传订单CSV")
        uploaded_file = st.file_uploader("选择CSV文件", type=['csv'])
        
        if uploaded_file is not None:
            try:
                # 保存上传的文件
                temp_path = ROOT / 'data' / 'temp_orders.csv'
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # 加载订单
                st.session_state.orders = load_orders(str(temp_path))
                st.success(f"✅ 已加载 {len(st.session_state.orders.get_all_orders())} 个订单")
            except Exception as e:
                st.error(f"❌ 加载失败: {str(e)}")
    
    with col2:
        st.subheader("使用示例数据")
        if st.button("📂 加载小规模示例", use_container_width=True):
            sample_path = ROOT / 'data' / 'sample_orders_small.csv'
            st.session_state.orders = load_orders(str(sample_path))
            st.success(f"✅ 已加载示例订单")
            st.rerun()
        
        if st.button("📂 加载中等规模示例", use_container_width=True):
            sample_path = ROOT / 'data' / 'sample_orders_medium.csv'
            st.session_state.orders = load_orders(str(sample_path))
            st.success(f"✅ 已加载示例订单")
            st.rerun()
    
    # 显示订单信息
    if st.session_state.orders is not None:
        st.markdown("---")
        st.subheader("📋 订单概览")
        
        # 提示信息
        if st.session_state.scheduler is not None:
            st.info("ℹ️ 显示的是上次调度运行后的订单状态。再次运行调度时，所有订单会自动重置。")
        
        orders = st.session_state.orders.get_all_orders()
        
        # 统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总订单数", len(orders))
        with col2:
            pending = st.session_state.orders.get_pending_count()
            st.metric("待处理订单", pending)
        with col3:
            completed = sum(1 for o in orders if o.is_completed())
            st.metric("已完成订单", completed)
        with col4:
            completion_rate = (completed / len(orders) * 100) if len(orders) > 0 else 0
            st.metric("完成率", f"{completion_rate:.1f}%")
        
        # 订单详情表格
        st.subheader("订单详情")
        order_data = []
        for order in orders[:20]:  # 只显示前20个
            order_data.append({
                "订单ID": order.order_id,
                "产品ID": order.product,
                "数量": order.quantity,
                "截止时段": order.due_slot,
                "收入": f"¥{order.quantity * order.unit_price:,.2f}",
                "状态": "✅ 已完成" if order.is_completed() else "⏳ 待处理"
            })
        
        if order_data:
            st.dataframe(pd.DataFrame(order_data), use_container_width=True, hide_index=True)
            if len(orders) > 20:
                st.info(f"ℹ️ 仅显示前20个订单，共{len(orders)}个订单")

# Tab 3: 调度运行
with tab3:
    st.header("🚀 调度运行")
    
    if st.session_state.orders is None:
        st.warning("⚠️ 请先在【订单管理】标签页加载订单数据")
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("运行参数")
            num_days = st.number_input(
                "模拟天数", 
                min_value=1, 
                max_value=10, 
                value=3, 
                step=1,
                help="设置要模拟的生产天数"
            )
            
            if st.button("▶️ 运行调度", type="primary", use_container_width=True):
                with st.spinner("🔄 正在运行调度算法..."):
                    try:
                        # 运行调度
                        scheduler, stats = run_schedule(
                            st.session_state.config,
                            st.session_state.orders,
                            num_days
                        )
                        
                        # 保存结果
                        st.session_state.scheduler = scheduler
                        st.session_state.stats = stats
                        
                        # 生成可视化
                        final_schedule = scheduler.get_current_schedule()
                        orders = st.session_state.orders.get_all_orders()
                        
                        if final_schedule:
                            # 生成甘特图
                            gantt = GanttChart()
                            gantt.plot_schedule(
                                final_schedule,
                                orders,
                                num_lines=3,
                                max_slots=30,
                                output_path=f"{st.session_state.output_dir}/gantt_chart.png"
                            )
                            
                            # 生成指标图表
                            metrics_viz = MetricsVisualizer()
                            metrics_viz.generate_report(
                                stats,
                                orders,
                                st.session_state.output_dir,
                                final_schedule
                            )
                        
                        st.success("✅ 调度完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 调度失败: {str(e)}")
        
        with col2:
            st.subheader("运行状态")
            
            if st.session_state.stats is not None:
                stats = st.session_state.stats
                
                # 关键指标卡片
                st.markdown("### 💰 财务指标")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.metric("总收入", f"¥{stats['total_revenue']:,.0f}")
                with col_m2:
                    st.metric("总成本", f"¥{stats['total_cost']:,.0f}")
                with col_m3:
                    st.metric("总罚款", f"¥{stats['total_penalty']:,.0f}")
                with col_m4:
                    profit_color = "normal" if stats['total_profit'] >= 0 else "inverse"
                    st.metric("总利润", f"¥{stats['total_profit']:,.0f}")
                
                # 订单指标
                st.markdown("### 📦 订单指标")
                col_o1, col_o2, col_o3 = st.columns(3)
                
                with col_o1:
                    st.metric("总订单数", stats['total_orders'])
                with col_o2:
                    st.metric("完成订单数", stats['completed_orders'])
                with col_o3:
                    completion_rate = stats['completed_orders'] / stats['total_orders'] * 100
                    st.metric("完成率", f"{completion_rate:.1f}%")
                
                # 每日明细
                st.markdown("### 📅 每日明细")
                daily_data = []
                for day_result in stats['daily_results']:
                    daily_data.append({
                        "天数": f"第{day_result['day']}天",
                        "收入": f"¥{day_result['revenue']:,.2f}",
                        "成本": f"¥{day_result['cost']:,.2f}",
                        "罚款": f"¥{day_result['penalty']:,.2f}",
                        "利润": f"¥{day_result['profit']:,.2f}"
                    })
                
                st.dataframe(pd.DataFrame(daily_data), use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ 点击【运行调度】按钮开始调度")

# Tab 4: 结果分析
with tab4:
    st.header("📊 结果分析与可视化")
    
    if st.session_state.scheduler is None or st.session_state.stats is None:
        st.warning("⚠️ 请先在【调度运行】标签页运行调度")
    else:
        # 甘特图
        st.subheader("📈 生产甘特图")
        gantt_path = Path(st.session_state.output_dir) / "gantt_chart.png"
        if gantt_path.exists():
            st.image(str(gantt_path), use_column_width=True)
        else:
            st.warning("甘特图未生成")
        
        st.markdown("---")
        
        # 指标图表
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 利润分解")
            profit_path = Path(st.session_state.output_dir) / "profit_breakdown.png"
            if profit_path.exists():
                st.image(str(profit_path), use_column_width=True)
        
        with col2:
            st.subheader("📦 订单完成情况")
            order_path = Path(st.session_state.output_dir) / "order_completion.png"
            if order_path.exists():
                st.image(str(order_path), use_column_width=True)
        
        st.markdown("---")
        
        # 产线利用率
        st.subheader("🏭 产线利用率")
        util_path = Path(st.session_state.output_dir) / "line_utilization.png"
        if util_path.exists():
            st.image(str(util_path), use_column_width=True)
        
        st.markdown("---")
        
        # 下载按钮
        st.subheader("📥 下载结果")
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        
        with col_d1:
            if gantt_path.exists():
                with open(gantt_path, 'rb') as f:
                    st.download_button(
                        "下载甘特图",
                        f,
                        file_name="gantt_chart.png",
                        mime="image/png",
                        use_container_width=True
                    )
        
        with col_d2:
            if profit_path.exists():
                with open(profit_path, 'rb') as f:
                    st.download_button(
                        "下载利润图",
                        f,
                        file_name="profit_breakdown.png",
                        mime="image/png",
                        use_container_width=True
                    )
        
        with col_d3:
            if order_path.exists():
                with open(order_path, 'rb') as f:
                    st.download_button(
                        "下载订单图",
                        f,
                        file_name="order_completion.png",
                        mime="image/png",
                        use_container_width=True
                    )
        
        with col_d4:
            if util_path.exists():
                with open(util_path, 'rb') as f:
                    st.download_button(
                        "下载利用率图",
                        f,
                        file_name="line_utilization.png",
                        mime="image/png",
                        use_container_width=True
                    )

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    智能制造生产调度系统 v1.0 | 基于遗传算法与局部搜索的混合优化
    </div>
    """,
    unsafe_allow_html=True
)
