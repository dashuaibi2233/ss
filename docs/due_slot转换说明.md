# due_slot 转换说明

## 业务规则

**所有订单的截止时间统一到截止日期当天早上8点**

无论CSV中的 `due_slot` 是第几天的哪个时段，都会被转换为该天结束后的下一天早上8点。

## 转换公式

```python
adjusted_due_slot = ((original_due_slot - 1) // 6 + 1) * 6 + 1
```

### 公式解释

1. `(original_due_slot - 1) // 6`: 计算截止日期是第几天（0-based）
2. `+ 1`: 转换为1-based的天数
3. `* 6 + 1`: 计算下一天的第一个slot（早上8点）

## 转换示例

假设每天6个slot（slot 1-6是第1天，slot 7-12是第2天...）

| 原始due_slot | 所在时段 | 所在天 | 转换后 | 说明 |
|-------------|---------|-------|--------|------|
| 1 | 8:00-12:00 | 第1天 | 7 | 统一到第2天早上8点 |
| 2 | 12:00-16:00 | 第1天 | 7 | 统一到第2天早上8点 |
| 3 | 16:00-20:00 | 第1天 | 7 | 统一到第2天早上8点 |
| 4 | 20:00-24:00 | 第1天 | 7 | 统一到第2天早上8点 |
| 5 | 0:00-4:00 | 第1天 | 7 | 统一到第2天早上8点 |
| 6 | 4:00-8:00 | 第1天 | 7 | 统一到第2天早上8点 |
| 7 | 8:00-12:00 | 第2天 | 13 | 统一到第3天早上8点 |
| 8 | 12:00-16:00 | 第2天 | 13 | 统一到第3天早上8点 |
| ... | ... | ... | ... | ... |
| 12 | 4:00-8:00 | 第2天 | 13 | 统一到第3天早上8点 |
| 13 | 8:00-12:00 | 第3天 | 19 | 统一到第4天早上8点 |
| 18 | 4:00-8:00 | 第3天 | 19 | 统一到第4天早上8点 |
| 24 | 4:00-8:00 | 第4天 | 25 | 统一到第5天早上8点 |
| 30 | 4:00-8:00 | 第5天 | 31 | 统一到第6天早上8点 |
| 36 | 4:00-8:00 | 第6天 | 37 | 统一到第7天早上8点 |

## 实际案例（sample_orders_small.csv）

### 订单1和订单2
```csv
1,2,220,1,6,70
2,1,150,1,6,50
```

- **原始due_slot**: 6（第1天 4:00-8:00）
- **转换后**: 7（第2天早上8点）
- **可生产时段**: slot 1-6
- **截止时间**: 第2天早上8点之前必须完成

### 订单3和订单4
```csv
3,3,180,3,12,60
4,2,300,3,12,68
```

- **原始due_slot**: 12（第2天 4:00-8:00）
- **转换后**: 13（第3天早上8点）
- **可生产时段**: slot 3-12
- **截止时间**: 第3天早上8点之前必须完成

### 订单7
```csv
7,1,260,7,18,52
```

- **原始due_slot**: 18（第3天 4:00-8:00）
- **转换后**: 19（第4天早上8点）
- **可生产时段**: slot 7-18
- **截止时间**: 第4天早上8点之前必须完成

## 代码实现

### order_manager.py

```python
def load_orders_from_csv(self, filepath, adjust_due_slot=True):
    """
    从 CSV 文件加载订单
    
    Args:
        filepath: CSV文件路径
        adjust_due_slot: 是否调整due_slot到截止日期当天早上8点（默认True）
    """
    # 读取原始due_slot
    original_due_slot = int(row['due_slot'])
    
    # 调整due_slot：统一到截止日期当天早上8点
    if adjust_due_slot:
        # 计算截止日期是第几天（0-based）
        due_day = (original_due_slot - 1) // 6
        # 调整到下一天早上8点（即下一天的第一个slot）
        adjusted_due_slot = (due_day + 1) * 6 + 1
    else:
        adjusted_due_slot = original_due_slot
```

## 使用方法

### 默认行为（自动转换）
```python
om = OrderManager()
om.load_orders_from_csv('data/sample_orders_small.csv')  # adjust_due_slot=True（默认）
```

### 禁用转换（使用原始值）
```python
om = OrderManager()
om.load_orders_from_csv('data/sample_orders_small.csv', adjust_due_slot=False)
```

## 转换日志

加载订单时会打印转换信息：

```
加载 sample_orders_small.csv...
  订单1: due_slot 6 -> 7
  订单2: due_slot 6 -> 7
  订单3: due_slot 12 -> 13
  订单4: due_slot 12 -> 13
  ...
从 data/sample_orders_small.csv 加载了 20 个订单
```

## 验证测试

运行测试脚本验证转换逻辑：

```bash
python test_due_slot_adjustment.py
```

测试结果：
- ✅ 所有订单的 due_slot 转换正确
- ✅ 转换公式验证通过
- ✅ 订单生产时间窗口 [release_slot, due_slot) 正确

## 注意事项

1. **时间窗口**: 订单的生产时间窗口为 `[release_slot, due_slot)`（左闭右开）
2. **罚款判定**: 当 `current_slot >= due_slot` 时，订单超期
3. **默认开启**: `adjust_due_slot=True` 是默认行为，符合业务规则
4. **兼容性**: 可以通过 `adjust_due_slot=False` 禁用转换，使用CSV中的原始值
