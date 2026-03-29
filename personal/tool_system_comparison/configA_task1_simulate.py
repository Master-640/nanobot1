#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置A（粗粒度工具）模拟测试 - Task 1

模拟使用通用工具execute_python_code完成任务
工具接口：execute_python_code(code: str) -> str
"""

import pandas as pd
import os
from datetime import datetime

def execute_python_code(code: str) -> str:
    """模拟粗粒度工具：执行任意Python代码"""
    print(f"[execute_python_code] 代码长度: {len(code)} 字符")
    
    try:
        # 在实际系统中，这会在沙箱中执行代码
        # 这里我们模拟执行效果
        if "read_csv" in code and "value" in code:
            # 模拟读取CSV并计算平均值
            data_path = r'D:\collections2026\phd_application\nanobot1\personal\tool_system_comparison\data.csv'
            df = pd.read_csv(data_path)
            average = df['value'].mean()
            
            result = f"""
            代码执行成功！
            
            读取文件: {data_path}
            数据行数: {len(df)}
            value列平均值: {average:.2f}
            
            数据预览:
            {df.head().to_string()}
            """
            return result
        else:
            return "错误：代码未正确实现读取CSV和计算平均值功能"
    except Exception as e:
        return f"代码执行错误: {str(e)}"

def task1_with_configA():
    """配置A下的Task 1测试"""
    print("=== 配置A（粗粒度工具）Task 1测试开始 ===")
    print("任务：读取data.csv文件，计算value列的平均值")
    print("工具：execute_python_code (通用代码执行工具)")
    print("-" * 50)
    
    # LLM可能会生成的代码（模拟自由发挥）
    python_code = '''
import pandas as pd
import os

def calculate_average_from_csv(file_path):
    """读取CSV文件并计算value列的平均值"""
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return f"文件不存在: {file_path}"
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 检查value列是否存在
        if 'value' not in df.columns:
            return f"CSV文件中没有'value'列，可用列: {list(df.columns)}"
        
        # 计算平均值
        average = df['value'].mean()
        
        # 返回结果
        result = {
            'file_path': file_path,
            'row_count': len(df),
            'average_value': average,
            'data_preview': df.head().to_dict()
        }
        return result
    except Exception as e:
        return f"处理文件时出错: {str(e)}"

# 执行计算
data_file = r'D:\\collections2026\\phd_application\\nanobot1\\personal\\tool_system_comparison\\data.csv'
result = calculate_average_from_csv(data_file)
print(result)
'''
    
    print("模拟LLM生成的代码:")
    print("-" * 30)
    print(python_code[:500] + "..." if len(python_code) > 500 else python_code)
    print("-" * 30)
    
    # 模拟工具调用
    start_time = datetime.now()
    print("调用execute_python_code工具...")
    result = execute_python_code(python_code)
    end_time = datetime.now()
    
    execution_time = (end_time - start_time).total_seconds()
    
    print("\n工具执行结果:")
    print(result)
    print(f"\n执行时间: {execution_time:.2f}秒")
    print(f"生成的代码长度: {len(python_code)}字符")
    print(f"代码复杂度: 包含错误处理、类型检查、格式返回")
    
    return {
        'tool_calls': 1,
        'code_length': len(python_code),
        'execution_time': execution_time,
        'has_error_handling': True,
        'has_file_check': True,
        'result_quality': '完整包含数据预览和错误处理'
    }

if __name__ == "__main__":
    result = task1_with_configA()
    print("\n=== 测试结果总结 ===")
    print(f"工具调用次数: {result['tool_calls']}")
    print(f"代码长度: {result['code_length']}字符")
    print(f"执行时间: {result['execution_time']:.2f}秒")
    print(f"包含错误处理: {result['has_error_handling']}")
    print(f"包含文件检查: {result['has_file_check']}")
    print(f"结果质量: {result['result_quality']}")