"""
为CSV文件添加release_slot列
"""
import csv

# 更新delay_full.csv
input_file = 'data/delay_full.csv'
output_file = 'data/delay_full_new.csv'

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# 为每个订单分配release_slot
# 策略：根据due_slot分配，让订单在截止日期之前的某个时间到达
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    fieldnames = ['order_id', 'product', 'quantity', 'release_slot', 'due_slot', 'unit_price']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    for row in rows:
        due_slot = int(row['due_slot'])
        # release_slot设置为due_slot之前的某个时间
        # 例如：due_slot=6的订单，release_slot在1-3之间
        #      due_slot=12的订单，release_slot在7-9之间
        if due_slot <= 6:
            release_slot = max(1, due_slot - 5)
        elif due_slot <= 12:
            release_slot = max(1, due_slot - 5)
        elif due_slot <= 18:
            release_slot = max(7, due_slot - 5)
        elif due_slot <= 24:
            release_slot = max(13, due_slot - 5)
        else:
            release_slot = max(19, due_slot - 5)
        
        writer.writerow({
            'order_id': row['order_id'],
            'product': row['product'],
            'quantity': row['quantity'],
            'release_slot': release_slot,
            'due_slot': row['due_slot'],
            'unit_price': row['unit_price']
        })

print(f"✅ 已更新 {output_file}")
print("前5行预览：")
with open(output_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 6:
            print(line.strip())
