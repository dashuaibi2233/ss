"""
代码质量检查脚本
检查常见的逻辑问题和潜在bug
"""
import sys
import os

# 添加路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("="*70)
print("代码质量检查")
print("="*70)

issues = []

# 检查1: 导入测试
print("\n1. 检查模块导入...")
try:
    from src.ga.engine import GAEngine, run_ga
    from src.ga.operators import GeneticOperators
    from src.ga.decoder import Decoder
    from src.ga.fitness import FitnessEvaluator, evaluate_chromosome
    from src.scheduler.rolling_scheduler import RollingScheduler
    from src.scheduler.order_manager import OrderManager
    from src.local_search.ils_vns import LocalSearch, improve_solution
    from src.models.chromosome import Chromosome
    from src.models.order import Order
    from src.models.schedule import Schedule
    from src.config import Config
    print("   ✅ 所有模块导入成功")
except Exception as e:
    issues.append(f"模块导入失败: {e}")
    print(f"   ❌ 模块导入失败: {e}")

# 检查2: 配置对象测试
print("\n2. 检查配置对象...")
try:
    config = Config()
    assert config.NUM_LINES == 3, "生产线数量应为3"
    assert config.NUM_PRODUCTS == 3, "产品种类应为3"
    assert config.SLOTS_PER_DAY == 6, "每天时间段应为6"
    assert len(config.CAPACITY) == 3, "产能配置应包含3种产品"
    assert config.POPULATION_SIZE > 0, "种群规模应大于0"
    assert config.MAX_GENERATIONS > 0, "最大迭代次数应大于0"
    print("   ✅ 配置对象正常")
except AssertionError as e:
    issues.append(f"配置对象错误: {e}")
    print(f"   ❌ 配置对象错误: {e}")
except Exception as e:
    issues.append(f"配置对象异常: {e}")
    print(f"   ❌ 配置对象异常: {e}")

# 检查3: 订单管理器测试
print("\n3. 检查订单管理器...")
try:
    order_manager = OrderManager()
    
    # 创建测试订单
    test_order = Order(
        order_id=1,
        product=1,
        quantity=100,
        due_slot=6,
        unit_price=50.0
    )
    
    order_manager.add_order(test_order)
    assert order_manager.get_order_count() == 1, "订单数量应为1"
    assert len(order_manager.get_pending_orders()) == 1, "待处理订单应为1"
    
    retrieved_order = order_manager.get_order(1)
    assert retrieved_order is not None, "应能获取订单"
    assert retrieved_order.order_id == 1, "订单ID应匹配"
    
    print("   ✅ 订单管理器正常")
except AssertionError as e:
    issues.append(f"订单管理器错误: {e}")
    print(f"   ❌ 订单管理器错误: {e}")
except Exception as e:
    issues.append(f"订单管理器异常: {e}")
    print(f"   ❌ 订单管理器异常: {e}")

# 检查4: 染色体编码测试
print("\n4. 检查染色体编码...")
try:
    gene1 = [1, 2, 3, 0, 1, 2] * 3  # 3条线 × 6个slot
    gene2 = [0, 1, 2, 3, 4]  # 5个订单
    
    chromosome = Chromosome(gene1=gene1, gene2=gene2)
    assert len(chromosome.gene1) == 18, "Gene1长度应为18"
    assert len(chromosome.gene2) == 5, "Gene2长度应为5"
    
    # 测试复制
    copy_chr = chromosome.copy()
    assert copy_chr.gene1 == chromosome.gene1, "复制后Gene1应相同"
    assert copy_chr.gene2 == chromosome.gene2, "复制后Gene2应相同"
    assert copy_chr is not chromosome, "复制应创建新对象"
    
    print("   ✅ 染色体编码正常")
except AssertionError as e:
    issues.append(f"染色体编码错误: {e}")
    print(f"   ❌ 染色体编码错误: {e}")
except Exception as e:
    issues.append(f"染色体编码异常: {e}")
    print(f"   ❌ 染色体编码异常: {e}")

# 检查5: 遗传操作算子测试
print("\n5. 检查遗传操作算子...")
try:
    config = Config()
    
    # 创建测试染色体
    chr1 = Chromosome(gene1=[1, 2, 3, 0] * 5, gene2=[0, 1, 2, 3, 4])
    chr2 = Chromosome(gene1=[3, 2, 1, 0] * 5, gene2=[4, 3, 2, 1, 0])
    chr1.fitness = 100
    chr2.fitness = 200
    
    # 测试选择
    population = [chr1, chr2]
    selected = GeneticOperators.tournament_selection(population, tournament_size=2)
    assert selected is not None, "应能选择个体"
    
    # 测试交叉
    child1_g1, child2_g1 = GeneticOperators.crossover_gene1(chr1, chr2)
    assert len(child1_g1) == len(chr1.gene1), "交叉后Gene1长度应保持"
    
    child1_g2, child2_g2 = GeneticOperators.crossover_gene2(chr1, chr2)
    assert len(child1_g2) == len(chr1.gene2), "交叉后Gene2长度应保持"
    assert set(child1_g2) == set(chr1.gene2), "交叉后Gene2应包含所有订单"
    
    # 测试变异
    test_chr = chr1.copy()
    GeneticOperators.mutate_gene1(test_chr, mutation_rate=0.5, num_products=3)
    GeneticOperators.mutate_gene2(test_chr, mutation_rate=0.5)
    
    print("   ✅ 遗传操作算子正常")
except AssertionError as e:
    issues.append(f"遗传操作算子错误: {e}")
    print(f"   ❌ 遗传操作算子错误: {e}")
except Exception as e:
    issues.append(f"遗传操作算子异常: {e}")
    print(f"   ❌ 遗传操作算子异常: {e}")

# 检查6: 解码器测试
print("\n6. 检查解码器...")
try:
    config = Config()
    decoder = Decoder(config)
    
    # 创建测试数据
    orders = [
        Order(order_id=1, product=1, quantity=50, due_slot=6, unit_price=50.0),
        Order(order_id=2, product=2, quantity=60, due_slot=12, unit_price=60.0),
    ]
    
    gene1 = [1, 2, 0] * 6  # 3条线 × 6个slot
    gene2 = [0, 1]
    chromosome = Chromosome(gene1=gene1, gene2=gene2)
    
    # 测试解码
    schedule = decoder.decode(chromosome, orders, start_slot=1)
    assert schedule is not None, "应能生成调度方案"
    # 检查schedule的类型
    schedule_type = type(schedule).__name__
    assert schedule_type == 'Schedule', f"应返回Schedule对象，实际返回: {schedule_type}"
    
    print("   ✅ 解码器正常")
except AssertionError as e:
    issues.append(f"解码器错误: {e}")
    print(f"   ❌ 解码器错误: {e}")
except Exception as e:
    issues.append(f"解码器异常: {e}")
    print(f"   ❌ 解码器异常: {e}")

# 检查7: 适应度评估测试
print("\n7. 检查适应度评估...")
try:
    config = Config()
    
    orders = [
        Order(order_id=1, product=1, quantity=50, due_slot=6, unit_price=50.0),
        Order(order_id=2, product=2, quantity=60, due_slot=12, unit_price=60.0),
    ]
    
    gene1 = [1, 2, 0] * 6
    gene2 = [0, 1]
    chromosome = Chromosome(gene1=gene1, gene2=gene2)
    
    # 测试适应度计算
    fitness = evaluate_chromosome(chromosome, orders, config, start_slot=1)
    assert isinstance(fitness, (int, float)), "适应度应为数值"
    
    print(f"   ✅ 适应度评估正常 (示例适应度: {fitness:.2f})")
except AssertionError as e:
    issues.append(f"适应度评估错误: {e}")
    print(f"   ❌ 适应度评估错误: {e}")
except Exception as e:
    issues.append(f"适应度评估异常: {e}")
    print(f"   ❌ 适应度评估异常: {e}")

# 检查8: 局部搜索测试
print("\n8. 检查局部搜索...")
try:
    config = Config()
    config.MAX_LS_ITERATIONS = 5  # 减少迭代次数用于测试
    
    orders = [
        Order(order_id=1, product=1, quantity=50, due_slot=6, unit_price=50.0),
        Order(order_id=2, product=2, quantity=60, due_slot=12, unit_price=60.0),
    ]
    
    gene1 = [1, 2, 0] * 6
    gene2 = [0, 1]
    initial_solution = Chromosome(gene1=gene1, gene2=gene2)
    initial_solution.fitness = evaluate_chromosome(initial_solution, orders, config, start_slot=1)
    
    # 测试局部搜索
    local_search = LocalSearch(config)
    improved = local_search.optimize(initial_solution, orders, start_slot=1)
    
    assert improved is not None, "应返回改进解"
    assert hasattr(improved, 'fitness'), "改进解应有适应度"
    
    print(f"   ✅ 局部搜索正常 (初始: {initial_solution.fitness:.2f}, 改进后: {improved.fitness:.2f})")
except AssertionError as e:
    issues.append(f"局部搜索错误: {e}")
    print(f"   ❌ 局部搜索错误: {e}")
except Exception as e:
    issues.append(f"局部搜索异常: {e}")
    print(f"   ❌ 局部搜索异常: {e}")

# 总结
print("\n" + "="*70)
print("检查结果总结")
print("="*70)

if not issues:
    print("✅ 所有检查通过！代码质量良好。")
else:
    print(f"❌ 发现 {len(issues)} 个问题:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")

print("\n建议:")
print("  1. 使用 delay_full.csv 进行满负荷测试")
print("  2. 运行完整的调度模拟验证系统功能")
print("  3. 检查GUI应用的Streamlit版本兼容性")
print("="*70)
