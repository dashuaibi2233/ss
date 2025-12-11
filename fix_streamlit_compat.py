"""
修复Streamlit兼容性问题
将 use_container_width=True 替换为 width="stretch"
"""
import re

# 读取文件
with open('gui_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 use_container_width=True
content = content.replace('use_container_width=True', 'width="stretch"')

# 写回文件
with open('gui_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已修复Streamlit兼容性问题")
print("   替换: use_container_width=True -> width=\"stretch\"")
