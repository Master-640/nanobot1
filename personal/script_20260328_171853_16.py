# -*- coding: utf-8 -*-
"""
Kimi K2.5 Task 4 - 简化版批量重命名脚本
用户偏好：Python代码 + 中文注释
"""

import os
import glob
from datetime import datetime

def batch_rename_files():
    """批量重命名文件"""
    base_dir = r"D:\collections2026\phd_application\nanobot1\personal"
    
    # 定义重命名规则
    rules = [
        ("*.csv", "task4_data_"),
        ("*.txt", "task4_text_"), 
        ("*.md", "task4_doc_")
    ]
    
    renamed_count = 0
    
    for pattern, prefix in rules:
        files = glob.glob(os.path.join(base_dir, pattern))
        for filepath in files:
            if os.path.isfile(filepath):
                filename = os.path.basename(filepath)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                new_name = f"{prefix}{timestamp}_{renamed_count+1}{ext}"
                new_path = os.path.join(base_dir, new_name)
                
                if not os.path.exists(new_path):
                    os.rename(filepath, new_path)
                    print("Renamed: {} -> {}".format(filename, new_name))
                    renamed_count += 1
    
    print("Task 4 completed! Total renamed: {} files".format(renamed_count))
    return renamed_count

if __name__ == "__main__":
    batch_rename_files()