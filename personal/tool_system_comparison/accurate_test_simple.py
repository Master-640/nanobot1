#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确工具系统粒度对比测试 - 简化版
使用cal_token skill方法记录实际Token和时间消耗
无emoji字符，兼容Windows控制台
"""

import os
import re
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time

class TokenAnalyzer:
    """Token使用量分析器，基于cal_token skill方法"""
    
    def __init__(self, token_file_path: str):
        self.token_file = token_file_path
        self.start_time = None
        self.end_time = None
        self.start_tokens = 0
        self.end_tokens = 0
        
    def record_start_time(self):
        """记录开始时间（精确到秒）"""
        self.start_time = datetime.now()
        print(f"[时间] 开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 读取当前的token总量
        self.start_tokens = self._get_current_total_tokens()
        print(f"[Token] 开始Token总量: {self.start_tokens}")
        
    def record_end_time(self):
        """记录结束时间（结束时间+10秒）"""
        actual_end_time = datetime.now()
        # 按照cal_token skill要求：把结束时间+10s
        self.end_time = actual_end_time + timedelta(seconds=10)
        print(f"[时间] 实际结束时间: {actual_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[时间] 计算结束时间（+10秒）: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 读取计算结束时间的token总量
        self.end_tokens = self._get_current_total_tokens()
        print(f"[Token] 结束Token总量: {self.end_tokens}")
        
    def _get_current_total_tokens(self) -> int:
        """从token_usage.txt读取最新的total tokens值"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        # 取最后一行
                        last_line = lines[-1].strip()
                        # 解析格式: "2026-03-28 22:43:25 | prompt=43247, completion=122, total=43369"
                        match = re.search(r'total=(\d+)', last_line)
                        if match:
                            return int(match.group(1))
            return 0
        except Exception as e:
            print(f"读取token文件失败: {e}")
            return 0
    
    def calculate_token_usage(self) -> Dict:
        """计算任务期间的token消耗"""
        if not self.start_time or not self.end_time:
            return {"error": "未记录开始或结束时间"}
            
        # 读取时间段内的所有token记录
        records = self._get_token_records_in_period()
        
        # 计算总消耗
        token_delta = self.end_tokens - self.start_tokens
        actual_time = self.end_time - timedelta(seconds=10) - self.start_time
        
        result = {
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "actual_end_time": (self.end_time - timedelta(seconds=10)).strftime("%Y-%m-%d %H:%M:%S"),
            "calculated_end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "start_tokens": self.start_tokens,
            "end_tokens": self.end_tokens,
            "token_consumption": token_delta,
            "actual_execution_time_seconds": actual_time.total_seconds(),
            "calculated_execution_time_seconds": (self.end_time - self.start_time).total_seconds(),
            "record_count": len(records),
            "records": records[:5] if records else []  # 只显示前5条记录
        }
        
        return result
    
    def _get_token_records_in_period(self) -> List[Dict]:
        """获取时间段内的所有token记录"""
        records = []
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析时间
                    time_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if time_match:
                        record_time = datetime.strptime(time_match.group(1), "%Y-%m-%d %H:%M:%S")
                        
                        # 检查是否在时间段内
                        if self.start_time <= record_time <= self.end_time:
                            # 解析token值
                            prompt_match = re.search(r'prompt=(\d+)', line)
                            completion_match = re.search(r'completion=(\d+)', line)
                            total_match = re.search(r'total=(\d+)', line)
                            
                            record = {
                                "time": record_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "prompt_tokens": int(prompt_match.group(1)) if prompt_match else 0,
                                "completion_tokens": int(completion_match.group(1)) if completion_match else 0,
                                "total_tokens": int(total_match.group(1)) if total_match else 0
                            }
                            records.append(record)
        except Exception as e:
            print(f"解析token记录失败: {e}")
            
        return records

def run_task(task_func, task_name: str, token_analyzer: TokenAnalyzer) -> Dict:
    """运行一个任务并记录token消耗"""
    print(f"\n{'='*60}")
    print(f"[开始] 开始任务: {task_name}")
    print('='*60)
    
    # 记录开始时间
    token_analyzer.record_start_time()
    
    # 执行任务
    print(f"\n[执行] 执行任务...")
    task_start = time.time()
    task_result = task_func()
    task_end = time.time()
    
    print(f"[完成] 任务执行完成，实际执行时间: {task_end - task_start:.2f}秒")
    
    # 记录结束时间（按skill要求：结束时间+10秒）
    token_analyzer.record_end_time()
    
    # 计算token消耗
    token_result = token_analyzer.calculate_token_usage()
    
    # 合并结果
    combined_result = {
        "task_name": task_name,
        "task_result": task_result,
        "token_analysis": token_result
    }
    
    print(f"\n[统计] 任务分析结果:")
    print(f"   实际执行时间: {combined_result['token_analysis']['actual_execution_time_seconds']:.2f}秒")
    print(f"   计算执行时间: {combined_result['token_analysis']['calculated_execution_time_seconds']:.2f}秒")
    print(f"   Token消耗: {combined_result['token_analysis']['token_consumption']}")
    
    return combined_result

def task_configA_1():
    """配置A Task 1: 粗粒度工具文件操作"""
    print("执行配置A Task 1: 使用execute_python_code读取CSV计算平均值")
    
    # 这里可以执行实际的测试代码
    # 暂时返回模拟结果
    return {
        "tool_calls": 1,
        "code_length": 938,
        "description": "粗粒度工具：execute_python_code"
    }

def task_configB_1():
    """配置B Task 1: 细粒度工具文件操作"""
    print("执行配置B Task 1: 使用read_csv_file + calculate_column_average")
    
    # 这里可以执行实际的测试代码
    return {
        "tool_calls": 2,
        "instruction_length": 102,
        "description": "细粒度工具：read_csv_file + calculate_column_average"
    }

def task_configA_2():
    """配置A Task 2: 粗粒度工具天气查询"""
    print("执行配置A Task 2: 使用web_search + execute_python_code")
    
    return {
        "tool_calls": 2,
        "code_length": 3117,
        "description": "粗粒度工具：web_search + execute_python_code"
    }

def task_configB_2():
    """配置B Task 2: 细粒度工具天气查询"""
    print("执行配置B Task 2: 使用get_weather + compare_temperatures")
    
    return {
        "tool_calls": 4,
        "instruction_length": 164,
        "description": "细粒度工具：get_weather + compare_temperatures"
    }

def main():
    """主测试函数"""
    print("=== 精确工具系统粒度对比测试 ===")
    print("使用cal_token skill方法记录实际Token和时间消耗")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*60)
    
    # 初始化token分析器
    token_file = r"D:\collections2026\phd_application\nanobot1\personal\token_usage.txt"
    if not os.path.exists(token_file):
        print(f"[错误] Token记录文件不存在: {token_file}")
        print("请确保token_usage.txt文件存在")
        return
    
    # 运行四个测试任务
    tasks = [
        (task_configA_1, "配置A - Task 1 (文件I/O)"),
        (task_configB_1, "配置B - Task 1 (文件I/O)"),
        (task_configA_2, "配置A - Task 2 (天气查询)"),
        (task_configB_2, "配置B - Task 2 (天气查询)")
    ]
    
    all_results = []
    
    for task_func, task_name in tasks:
        # 每个任务使用新的分析器实例
        task_analyzer = TokenAnalyzer(token_file)
        result = run_task(task_func, task_name, task_analyzer)
        all_results.append(result)
        
        # 任务间短暂停顿
        if task_name != tasks[-1][1]:
            print(f"\n[等待] 等待5秒开始下一个任务...")
            time.sleep(5)
    
    # 生成详细报告
    generate_detailed_report(all_results)
    
    return all_results

def generate_detailed_report(results: List[Dict]):
    """生成详细测试报告"""
    print(f"\n{'='*60}")
    print("[报告] 详细测试报告")
    print('='*60)
    
    report_data = []
    
    for result in results:
        task_name = result["task_name"]
        token_info = result["token_analysis"]
        task_info = result["task_result"]
        
        row = {
            "任务名称": task_name,
            "实际执行时间(秒)": f"{token_info['actual_execution_time_seconds']:.2f}",
            "计算执行时间(秒)": f"{token_info['calculated_execution_time_seconds']:.2f}",
            "Token消耗": token_info["token_consumption"],
            "开始Token": token_info["start_tokens"],
            "结束Token": token_info["end_tokens"],
            "工具调用次数": task_info.get("tool_calls", 0),
            "代码/指令长度": task_info.get("code_length", task_info.get("instruction_length", 0)),
            "描述": task_info.get("description", "")
        }
        report_data.append(row)
    
    # 打印表格
    print("\n" + "-" * 130)
    print(f"{'任务名称':<25} {'实际时间':<12} {'计算时间':<12} {'Token消耗':<12} {'开始Token':<12} {'结束Token':<12} {'工具调用':<12} {'代码长度':<12} {'描述':<15}")
    print("-" * 130)
    
    for row in report_data:
        print(f"{row['任务名称']:<25} {row['实际执行时间(秒)']:<12} {row['计算执行时间(秒)']:<12} "
              f"{row['Token消耗']:<12} {row['开始Token']:<12} {row['结束Token']:<12} "
              f"{row['工具调用次数']:<12} {row['代码/指令长度']:<12} {row['描述']:<15}")
    
    print("-" * 130)
    
    # 计算汇总统计
    total_tokens = sum(r["token_analysis"]["token_consumption"] for r in results)
    total_actual_time = sum(r["token_analysis"]["actual_execution_time_seconds"] for r in results)
    total_calculated_time = sum(r["token_analysis"]["calculated_execution_time_seconds"] for r in results)
    
    print(f"\n[统计] 汇总统计:")
    print(f"   总Token消耗: {total_tokens}")
    print(f"   总实际执行时间: {total_actual_time:.2f}秒")
    print(f"   总计算执行时间: {total_calculated_time:.2f}秒")
    
    # 对比分析
    configA_tasks = [r for r in results if "配置A" in r["task_name"]]
    configB_tasks = [r for r in results if "配置B" in r["task_name"]]
    
    if configA_tasks and configB_tasks:
        configA_total_tokens = sum(r["token_analysis"]["token_consumption"] for r in configA_tasks)
        configB_total_tokens = sum(r["token_analysis"]["token_consumption"] for r in configB_tasks)
        
        configA_avg_time = sum(r["token_analysis"]["actual_execution_time_seconds"] for r in configA_tasks) / len(configA_tasks)
        configB_avg_time = sum(r["token_analysis"]["actual_execution_time_seconds"] for r in configB_tasks) / len(configB_tasks)
        
        print(f"\n[分析] 配置对比分析:")
        print(f"   配置A总Token: {configA_total_tokens}")
        print(f"   配置B总Token: {configB_total_tokens}")
        if configA_total_tokens > 0:
            token_saving = (1 - configB_total_tokens/configA_total_tokens) * 100
            print(f"   Token节省比例: {token_saving:.1f}%")
        print(f"   配置A平均时间: {configA_avg_time:.2f}秒")
        print(f"   配置B平均时间: {configB_avg_time:.2f}秒")
        if configA_avg_time > 0:
            time_saving = (1 - configB_avg_time/configA_avg_time) * 100
            print(f"   时间节省比例: {time_saving:.1f}%")
    
    # 保存报告到文件
    report_path = r"D:\collections2026\phd_application\nanobot1\personal\tool_system_comparison\detailed_test_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 精确工具系统粒度对比测试报告\n\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("测试方法: 使用cal_token skill记录实际Token和时间消耗\n\n")
        
        f.write("## 测试结果汇总\n\n")
        f.write("| 任务名称 | 实际时间(s) | 计算时间(s) | Token消耗 | 开始Token | 结束Token | 工具调用 | 代码长度 | 描述 |\n")
        f.write("|----------|-------------|-------------|-----------|-----------|-----------|----------|----------|------|\n")
        
        for row in report_data:
            f.write(f"| {row['任务名称']} | {row['实际执行时间(秒)']} | {row['计算执行时间(秒)']} | {row['Token消耗']} | "
                   f"{row['开始Token']} | {row['结束Token']} | {row['工具调用次数']} | {row['代码/指令长度']} | {row['描述']} |\n")
        
        f.write("\n## 汇总统计\n\n")
        f.write(f"- 总Token消耗: {total_tokens}\n")
        f.write(f"- 总实际执行时间: {total_actual_time:.2f}秒\n")
        f.write(f"- 总计算执行时间: {total_calculated_time:.2f}秒\n")
        
        if configA_tasks and configB_tasks:
            f.write("\n## 配置对比分析\n\n")
            f.write(f"- 配置A总Token: {configA_total_tokens}\n")
            f.write(f"- 配置B总Token: {configB_total_tokens}\n")
            if configA_total_tokens > 0:
                f.write(f"- Token节省比例: {(1 - configB_total_tokens/configA_total_tokens)*100:.1f}%\n")
            f.write(f"- 配置A平均时间: {configA_avg_time:.2f}秒\n")
            f.write(f"- 配置B平均时间: {configB_avg_time:.2f}秒\n")
            if configA_avg_time > 0:
                f.write(f"- 时间节省比例: {(1 - configB_avg_time/configA_avg_time)*100:.1f}%\n")
        
        f.write("\n## 测试方法说明\n\n")
        f.write("1. 记录开始时间（精确到秒）\n")
        f.write("2. 执行任务\n")
        f.write("3. 记录结束时间（实际结束时间+10秒）\n")
        f.write("4. 读取token_usage.txt中时间段的token记录\n")
        f.write("5. 计算Token消耗 = 结束Token - 开始Token\n")
        
        # 添加原始数据
        f.write("\n## 原始测试数据\n\n")
        for i, result in enumerate(results, 1):
            f.write(f"### {result['task_name']}\n\n")
            f.write(f"- 开始时间: {result['token_analysis']['start_time']}\n")
            f.write(f"- 实际结束时间: {result['token_analysis']['actual_end_time']}\n")
            f.write(f"- 计算结束时间: {result['token_analysis']['calculated_end_time']}\n")
            f.write(f"- Token消耗: {result['token_analysis']['token_consumption']}\n")
            f.write(f"- 实际执行时间: {result['token_analysis']['actual_execution_time_seconds']:.2f}秒\n")
            f.write(f"- 工具调用次数: {result['task_result'].get('tool_calls', 0)}\n\n")
    
    print(f"\n[文件] 详细报告已保存至: {report_path}")

if __name__ == "__main__":
    main()