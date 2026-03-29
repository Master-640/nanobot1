#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置A（粗粒度工具）模拟测试 - Task 2

模拟使用通用工具完成任务：
1. web_search - 通用网络搜索
2. execute_python_code - 执行任意Python代码
"""

import json
from datetime import datetime
from typing import Dict, List

def web_search(query: str, count: int = 3) -> List[Dict[str, str]]:
    """模拟粗粒度工具：通用网络搜索"""
    print(f"[web_search] 搜索查询: '{query}'")
    
    # 模拟搜索结果
    if "北京 天气" in query or "weather" in query.lower():
        results = [
            {
                "title": "北京天气 - 当前温度 +20°C",
                "url": "https://example.com/beijing-weather",
                "snippet": "北京: ☁️ +20°C 30% ↑13km/h 阴天，温度20°C，湿度30%，风速13km/h"
            },
            {
                "title": "上海天气 - 当前温度 +18°C",
                "url": "https://example.com/shanghai-weather",
                "snippet": "上海: ⛅ +18°C 49% ↖15km/h 多云，温度18°C，湿度49%，风速15km/h"
            },
            {
                "title": "深圳天气 - 当前温度 +25°C",
                "url": "https://example.com/shenzhen-weather",
                "snippet": "深圳: ⛅ +25°C 83% ↖12km/h 多云，温度25°C，湿度83%，风速12km/h"
            }
        ]
    else:
        results = [
            {
                "title": f"搜索结果: {query}",
                "url": "https://example.com/search",
                "snippet": f"关于'{query}'的搜索结果"
            }
        ]
    
    return {
        "query": query,
        "count": len(results),
        "results": results,
        "message": f"找到{len(results)}个相关结果"
    }

def execute_python_code(code: str) -> str:
    """模拟粗粒度工具：执行任意Python代码"""
    print(f"[execute_python_code] 代码长度: {len(code)} 字符")
    
    try:
        # 模拟解析天气信息并比较的代码执行
        if "parse_weather" in code or "compare_temperatures" in code:
            # 模拟解析和比较天气数据
            weather_data = [
                {"city": "北京", "temperature": 20, "humidity": 30, "wind_speed": 13, "condition": "阴天"},
                {"city": "上海", "temperature": 18, "humidity": 49, "wind_speed": 15, "condition": "多云"},
                {"city": "深圳", "temperature": 25, "humidity": 83, "wind_speed": 12, "condition": "多云"}
            ]
            
            # 找出温度最高的城市
            hottest_city = max(weather_data, key=lambda x: x["temperature"])
            
            result = {
                "weather_data": weather_data,
                "hottest_city": hottest_city["city"],
                "hottest_temperature": hottest_city["temperature"],
                "comparison": f"深圳温度最高({hottest_city['temperature']}°C)，比北京高{25-20}°C，比上海高{25-18}°C",
                "summary": "深圳最暖和，北京最干燥，上海风速最大"
            }
            
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return "错误：代码未正确实现天气数据解析和比较功能"
    except Exception as e:
        return f"代码执行错误: {str(e)}"

def task2_with_configA():
    """配置A下的Task 2测试"""
    print("=== 配置A（粗粒度工具）Task 2测试开始 ===")
    print("任务：获取北京、上海、深圳三个城市的当前天气信息并比较温度")
    print("工具：web_search + execute_python_code (通用工具)")
    print("-" * 50)
    
    start_time = datetime.now()
    
    # 第一步：搜索天气信息
    print("第一步：调用web_search工具搜索天气信息")
    search_query = "北京 上海 深圳 当前天气 温度"
    search_result = web_search(search_query)
    
    search_time = datetime.now()
    print(f"搜索到{search_result['count']}个结果")
    for i, result in enumerate(search_result["results"], 1):
        print(f"  {i}. {result['snippet'][:50]}...")
    
    # LLM可能会生成的代码（模拟自由发挥）
    python_code = '''
import re
import json

def parse_weather_from_search_results(search_results):
    """从搜索结果中解析天气信息"""
    weather_data = []
    
    for result in search_results:
        snippet = result.get("snippet", "")
        
        # 尝试匹配城市和温度
        city_pattern = r"(北京|上海|深圳):\s*([☀️☁️⛅🌧️]+)?\s*([+-]?\d+)°C"
        match = re.search(city_pattern, snippet)
        
        if match:
            city = match.group(1)
            temperature = int(match.group(3))
            
            # 解析其他信息
            humidity_match = re.search(r'(\d+)%', snippet)
            humidity = int(humidity_match.group(1)) if humidity_match else 0
            
            wind_match = re.search(r'([↖↑↗→↘↓↙←]+)(\d+)km/h', snippet)
            wind_speed = int(wind_match.group(2)) if wind_match else 0
            
            condition_match = re.search(r':\s*([☀️☁️⛅🌧️]+)', snippet)
            condition = condition_match.group(1) if condition_match else "未知"
            
            weather_data.append({
                "city": city,
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "condition": condition,
                "raw_snippet": snippet[:100]
            })
    
    return weather_data

def compare_temperatures(weather_data):
    """比较不同城市的温度"""
    if not weather_data:
        return {"error": "没有天气数据"}
    
    # 按温度排序
    sorted_data = sorted(weather_data, key=lambda x: x["temperature"], reverse=True)
    
    hottest = sorted_data[0]
    coldest = sorted_data[-1]
    
    comparison = {
        "hottest_city": hottest["city"],
        "hottest_temperature": hottest["temperature"],
        "coldest_city": coldest["city"],
        "coldest_temperature": coldest["temperature"],
        "temperature_range": hottest["temperature"] - coldest["temperature"],
        "all_cities": [{"city": w["city"], "temp": w["temperature"]} for w in weather_data],
        "summary": f"{hottest['city']}最热({hottest['temperature']}°C)，{coldest['city']}最冷({coldest['temperature']}°C)，温差{hottest['temperature'] - coldest['temperature']}°C"
    }
    
    return comparison

# 从搜索结果解析天气
search_results = ''' + json.dumps(search_result["results"]) + '''
weather_data = parse_weather_from_search_results(search_results)

if weather_data:
    print("解析到的天气数据:")
    for data in weather_data:
        print(f"  {data['city']}: {data['temperature']}°C, 湿度{data['humidity']}%, 风速{data['wind_speed']}km/h")
    
    comparison = compare_temperatures(weather_data)
    print("\\n温度比较结果:")
    print(f"  最热城市: {comparison['hottest_city']} ({comparison['hottest_temperature']}°C)")
    print(f"  最冷城市: {comparison['coldest_city']} ({comparison['coldest_temperature']}°C)")
    print(f"  温差: {comparison['temperature_range']}°C")
    print(f"  总结: {comparison['summary']}")
else:
    print("未能解析到有效的天气数据")
'''
    
    print(f"\n第二步：调用execute_python_code工具解析和比较天气数据")
    print(f"生成的代码长度: {len(python_code)}字符")
    
    # 模拟工具调用
    parse_result = execute_python_code(python_code)
    end_time = datetime.now()
    
    execution_time = (end_time - start_time).total_seconds()
    parse_time = (end_time - search_time).total_seconds()
    
    print("\n解析和比较结果:")
    print(parse_result)
    
    print(f"\n搜索时间: {(search_time - start_time).total_seconds():.2f}秒")
    print(f"解析时间: {parse_time:.2f}秒")
    print(f"总执行时间: {execution_time:.2f}秒")
    print(f"生成的代码长度: {len(python_code)}字符")
    print(f"代码复杂度: 包含正则解析、错误处理、数据格式化")
    
    return {
        'tool_calls': 2,
        'code_length': len(python_code),
        'execution_time': execution_time,
        'search_time': (search_time - start_time).total_seconds(),
        'parse_time': parse_time,
        'has_error_handling': True,
        'has_regex_parsing': True,
        'result_quality': '包含详细解析和比较结果'
    }

if __name__ == "__main__":
    result = task2_with_configA()
    print("\n=== 测试结果总结 ===")
    print(f"工具调用次数: {result['tool_calls']}")
    print(f"代码长度: {result['code_length']}字符")
    print(f"总执行时间: {result['execution_time']:.2f}秒")
    print(f"搜索时间: {result['search_time']:.2f}秒")
    print(f"解析时间: {result['parse_time']:.2f}秒")
    print(f"包含错误处理: {result['has_error_handling']}")
    print(f"使用正则解析: {result['has_regex_parsing']}")
    print(f"结果质量: {result['result_quality']}")