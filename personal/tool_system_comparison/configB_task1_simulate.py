#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置B（细粒度工具）模拟测试 - Task 1

模拟使用专用工具完成任务
工具接口：
1. read_csv_file(path: str) -> List[Dict]
2. calculate_column_average(data: List[Dict], column: str) -> float
"""

import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any

def read_csv_file(path: str) -> List[Dict[str, Any]]:
    """模拟细粒度工具：读取CSV文件返回数据"""
    print(f"[read_csv_file] 读取文件: {path}")
    
    try:
        if not os.path.exists(path):
            return {"error": f"文件不存在: {path}"}
        
        df = pd.read_csv(path)
        data = df.to_dict('records')
        
        return {
            "success": True,
            "file_path": path,
            "row_count": len(df),
            "columns": list(df.columns),
            "data": data[:5],  # 只返回前5行作为示例
            "message": f"成功读取{len(df)}行数据"
        }
    except Exception as e:
        return {"error": f"读取文件失败: {str(e)}"}

def calculate_column_average(data: List[Dict[str, Any]], column: str) -> Dict[str, Any]:
    """模拟细粒度工具：计算指定列的平均值"""
    print(f"[calculate_column_average] 计算列 '{column}' 的平均值")
    
    try:
        if not data:
            return {"error": "数据为空"}
        
        # 提取指定列的值
        values = []
        missing_count = 0
        
        for row in data:
            if column in row:
                try:
                    value = float(row[column])
                    values.append(value)
                except (ValueError, TypeError):
                    missing_count += 1
            else:
                missing_count += 1
        
        if not values:
            return {"error": f"列 '{column}' 没有有效的数值数据"}
        
        # 计算平均值
        average = sum(values) / len(values)
        
        return {
            "success": True,
            "column": column,
            "average": average,
            "count": len(values),
            "missing": missing_count,
            "min": min(values),
            "max": max(values),
            "sum": sum(values),
            "message": f"成功计算平均值，基于{len(values)}个有效值"
        }
    except Exception as e:
        return {"error": f"计算平均值失败: {str(e)}"}

def task1_with_configB():
    """配置B下的Task 1测试"""
    print("=== 配置B（细粒度工具）Task 1测试开始 ===")
    print("任务：读取data.csv文件，计算value列的平均值")
    print("工具：read_csv_file + calculate_column_average (专用工具)")
    print("-" * 50)
    
    # 工具调用流程
    file_path = r'D:\collections2026\phd_application\nanobot1\personal\tool_system_comparison\data.csv'
    
    # 第一步：读取CSV文件
    print("第一步：调用read_csv_file工具读取文件")
    start_time = datetime.now()
    
    read_result = read_csv_file(file_path)
    read_time = datetime.now()
    
    if "error" in read_result:
        print(f"读取文件失败: {read_result['error']}")
        return None
    
    print(f"读取成功: {read_result['message']}")
    print(f"读取时间: {(read_time - start_time).total_seconds():.2f}秒")
    
    # 第二步：计算平均值
    print("\n第二步：调用calculate_column_average工具计算平均值")
    
    # 注意：实际系统中read_csv_file可能返回完整数据，这里我们模拟
    # 重新读取完整数据用于计算
    df = pd.read_csv(file_path)
    full_data = df.to_dict('records')
    
    calc_result = calculate_column_average(full_data, 'value')
    end_time = datetime.now()
    
    calc_time = (end_time - read_time).total_seconds()
    total_time = (end_time - start_time).total_seconds()
    
    if "error" in calc_result:
        print(f"计算平均值失败: {calc_result['error']}")
    else:
        print("\n计算成功！")
        print(f"列名: {calc_result['column']}")
        print(f"平均值: {calc_result['average']:.2f}")
        print(f"基于数据量: {calc_result['count']}个值")
        print(f"最小值: {calc_result['min']}")
        print(f"最大值: {calc_result['max']}")
        print(f"总和: {calc_result['sum']}")
        print(f"缺失值: {calc_result['missing']}")
    
    print(f"\n计算时间: {calc_time:.2f}秒")
    print(f"总执行时间: {total_time:.2f}秒")
    
    # 模拟LLM需要发送的指令
    llm_instructions = [
        "调用工具：read_csv_file，参数：path='data.csv'",
        "调用工具：calculate_column_average，参数：data=读取结果, column='value'",
        "输出：计算结果"
    ]
    
    print("\n模拟LLM需要发送的指令:")
    for i, instr in enumerate(llm_instructions, 1):
        print(f"{i}. {instr}")
    
    total_instruction_length = sum(len(instr) for instr in llm_instructions)
    
    return {
        'tool_calls': 2,
        'instruction_length': total_instruction_length,
        'execution_time': total_time,
        'read_time': (read_time - start_time).total_seconds(),
        'calc_time': calc_time,
        'result_quality': '直接、准确的计算结果',
        'has_error_handling': '工具内置错误处理',
        'data_returned': read_result.get('row_count', 0)
    }

if __name__ == "__main__":
    result = task1_with_configB()
    if result:
        print("\n=== 测试结果总结 ===")
        print(f"工具调用次数: {result['tool_calls']}")
        print(f"指令总长度: {result['instruction_length']}字符")
        print(f"总执行时间: {result['execution_time']:.2f}秒")
        print(f"文件读取时间: {result['read_time']:.2f}秒")
        print(f"计算时间: {result['calc_time']:.2f}秒")
        print(f"返回数据行数: {result['data_returned']}")
        print(f"结果质量: {result['result_quality']}")
        print(f"错误处理: {result['has_error_handling']}")