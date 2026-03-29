#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置B（细粒度工具）模拟测试 - Task 2

模拟使用专用工具完成任务：
1. get_weather(city: str) -> Dict - 获取指定城市天气
2. compare_temperatures(city_temps: Dict[str, float]) -> Dict - 比较温度
"""

import json
from datetime import datetime
from typing import Dict, List

def get_weather(city: str) -> Dict[str, any]:
    """模拟细粒度工具：获取指定城市的天气信息"""
    print(f"[get_weather] 获取城市天气: {city}")
    
    # 模拟天气数据
    weather_data = {
        "北京": {
            "city": "北京",
            "temperature": 20,
            "temperature_unit": "°C",
            "humidity": 30,
            "humidity_unit": "%",
            "wind_speed": 13,
            "wind_speed_unit": "km/h",
            "wind_direction": "↑",
            "condition": "阴天",
            "condition_emoji": "☁️",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "message": f"成功获取{city}天气信息"
        },
        "上海": {
            "city": "上海",
            "temperature": 18,
            "temperature_unit": "°C",
            "humidity": 49,
            "humidity_unit": "%",
            "wind_speed": 15,
            "wind_speed_unit": "km/h",
            "wind_direction": "↖",
            "condition": "多云",
            "condition_emoji": "⛅",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "message": f"成功获取{city}天气信息"
        },
        "深圳": {
            "city": "深圳",
            "temperature": 25,
            "temperature_unit": "°C",
            "humidity": 83,
            "humidity_unit": "%",
            "wind_speed": 12,
            "wind_speed_unit": "km/h",
            "wind_direction": "↖",
            "condition": "多云",
            "condition_emoji": "⛅",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "message": f"成功获取{city}天气信息"
        }
    }
    
    if city in weather_data:
        return weather_data[city]
    else:
        return {
            "city": city,
            "success": False,
            "message": f"未找到{city}的天气信息",
            "error": "城市不在支持列表中"
        }

def compare_temperatures(city_temps: Dict[str, float]) -> Dict[str, any]:
    """模拟细粒度工具：比较多个城市的温度"""
    print(f"[compare_temperatures] 比较{len(city_temps)}个城市的温度")
    
    if not city_temps:
        return {
            "success": False,
            "message": "没有温度数据可比较",
            "error": "输入数据为空"
        }
    
    try:
        # 找出最高和最低温度
        hottest_city = max(city_temps.items(), key=lambda x: x[1])
        coldest_city = min(city_temps.items(), key=lambda x: x[1])
        
        # 计算温差
        temperature_range = hottest_city[1] - coldest_city[1]
        
        # 温度排序
        sorted_temps = sorted(city_temps.items(), key=lambda x: x[1], reverse=True)
        
        # 生成比较结果
        comparison = {
            "success": True,
            "city_count": len(city_temps),
            "hottest": {
                "city": hottest_city[0],
                "temperature": hottest_city[1],
                "unit": "°C"
            },
            "coldest": {
                "city": coldest_city[0],
                "temperature": coldest_city[1],
                "unit": "°C"
            },
            "temperature_range": temperature_range,
            "sorted_temperatures": [
                {"city": city, "temperature": temp, "unit": "°C"}
                for city, temp in sorted_temps
            ],
            "summary": f"{hottest_city[0]}最热({hottest_city[1]}°C)，{coldest_city[0]}最冷({coldest_city[1]}°C)，温差{temperature_range}°C",
            "analysis": "基于提供的温度数据进行的比较",
            "timestamp": datetime.now().isoformat()
        }
        
        return comparison
    except Exception as e:
        return {
            "success": False,
            "message": f"比较温度时出错: {str(e)}",
            "error": str(e)
        }

def task2_with_configB():
    """配置B下的Task 2测试"""
    print("=== 配置B（细粒度工具）Task 2测试开始 ===")
    print("任务：获取北京、上海、深圳三个城市的当前天气信息并比较温度")
    print("工具：get_weather + compare_temperatures (专用工具)")
    print("-" * 50)
    
    start_time = datetime.now()
    tool_calls = 0
    weather_results = []
    city_temperatures = {}
    
    # 第一步：获取三个城市的天气信息
    cities = ["北京", "上海", "深圳"]
    
    print("第一步：依次调用get_weather工具获取三个城市天气")
    for city in cities:
        weather_result = get_weather(city)
        tool_calls += 1
        
        if weather_result.get("success"):
            print(f"  {city}: {weather_result['temperature']}°C, {weather_result['condition']}")
            weather_results.append(weather_result)
            city_temperatures[city] = weather_result["temperature"]
        else:
            print(f"  {city}: 获取失败 - {weather_result.get('message', '未知错误')}")
    
    get_weather_time = datetime.now()
    print(f"获取天气完成，耗时: {(get_weather_time - start_time).total_seconds():.2f}秒")
    
    # 第二步：比较温度
    print("\n第二步：调用compare_temperatures工具比较温度")
    if city_temperatures:
        comparison_result = compare_temperatures(city_temperatures)
        tool_calls += 1
        
        end_time = datetime.now()
        compare_time = (end_time - get_weather_time).total_seconds()
        total_time = (end_time - start_time).total_seconds()
        
        if comparison_result.get("success"):
            print("\n温度比较结果:")
            print(f"  最热城市: {comparison_result['hottest']['city']} ({comparison_result['hottest']['temperature']}°C)")
            print(f"  最冷城市: {comparison_result['coldest']['city']} ({comparison_result['coldest']['temperature']}°C)")
            print(f"  温差: {comparison_result['temperature_range']}°C")
            
            print("\n温度排序:")
            for i, item in enumerate(comparison_result["sorted_temperatures"], 1):
                print(f"  {i}. {item['city']}: {item['temperature']}°C")
            
            print(f"\n总结: {comparison_result['summary']}")
        else:
            print(f"比较失败: {comparison_result.get('message', '未知错误')}")
        
        print(f"\n比较时间: {compare_time:.2f}秒")
        print(f"总执行时间: {total_time:.2f}秒")
    else:
        print("没有有效的温度数据可比较")
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
    
    # 模拟LLM需要发送的指令
    llm_instructions = [
        "调用工具：get_weather，参数：city='北京'",
        "调用工具：get_weather，参数：city='上海'",
        "调用工具：get_weather，参数：city='深圳'",
        "调用工具：compare_temperatures，参数：city_temps={'北京':温度1, '上海':温度2, '深圳':温度3}",
        "输出：比较结果"
    ]
    
    print("\n模拟LLM需要发送的指令:")
    for i, instr in enumerate(llm_instructions, 1):
        print(f"{i}. {instr}")
    
    total_instruction_length = sum(len(instr) for instr in llm_instructions)
    
    return {
        'tool_calls': tool_calls,
        'instruction_length': total_instruction_length,
        'execution_time': total_time,
        'get_weather_time': (get_weather_time - start_time).total_seconds(),
        'compare_time': compare_time if 'compare_time' in locals() else 0,
        'cities_processed': len(cities),
        'successful_weather_calls': len(weather_results),
        'result_quality': '直接、准确的天气信息和温度比较',
        'has_error_handling': '工具内置错误处理',
        'output_format': '结构化的JSON数据'
    }

if __name__ == "__main__":
    result = task2_with_configB()
    print("\n=== 测试结果总结 ===")
    print(f"工具调用次数: {result['tool_calls']}")
    print(f"指令总长度: {result['instruction_length']}字符")
    print(f"总执行时间: {result['execution_time']:.2f}秒")
    print(f"获取天气时间: {result['get_weather_time']:.2f}秒")
    print(f"比较时间: {result.get('compare_time', 0):.2f}秒")
    print(f"处理城市数量: {result['cities_processed']}")
    print(f"成功获取天气: {result['successful_weather_calls']}")
    print(f"结果质量: {result['result_quality']}")
    print(f"错误处理: {result['has_error_handling']}")
    print(f"输出格式: {result['output_format']}")