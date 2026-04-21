"""
SAYG-Mem 扩展性测试脚本

测试不同Agent数量（10/20/50/100）下的性能表现
验证SAYG-Mem在规模化场景下的优势
"""

import asyncio
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(__file__))

from run_throughput_comparison import (
    clear_environment, 
    generate_comparison_table,
    get_pm_path,
    A_PUBLIC_MEMORY_FILE,
    B_PUBLIC_MEMORY_FILE,
    BFF_BASE_URL
)
from learn_throughput_fixed_time_a import run_throughput_experiment_a
from learn_throughput_fixed_time_b import run_throughput_experiment_b

SCALABILITY_TEST_DIR = os.path.join(os.path.dirname(__file__), "experiment_data", "scalability")


def get_base_roles():
    """获取基础角色列表（10个）"""
    return [
        {"name": "技术架构师", "focus": "强调系统设计、技术选型、架构模式", "perturbation": "请从'如何设计高效可扩展的系统'角度分析", "output_style": "偏向技术深度和架构思路"},
        {"name": "产品经理", "focus": "强调用户需求、产品价值、交互体验", "perturbation": "请从'如何解决用户痛点'角度分析", "output_style": "偏向需求洞察和产品价值"},
        {"name": "数据分析师", "focus": "强调数据驱动、指标量化、实验验证", "perturbation": "请从'如何通过数据验证假设'角度分析", "output_style": "偏向数据支持和量化分析"},
        {"name": "安全专家", "focus": "强调风险控制、安全合规、隐私保护", "perturbation": "请从'如何防范潜在风险'角度分析", "output_style": "偏向安全性和合规性"},
        {"name": "运维工程师", "focus": "强调可靠性、可观测性、故障恢复", "perturbation": "请从'如何保障服务稳定性'角度分析", "output_style": "偏向运维视角和稳定性保障"},
        {"name": "前端工程师", "focus": "强调用户界面、交互体验、性能优化", "perturbation": "请从'如何提升用户体验'角度分析", "output_style": "偏向前端技术和用户体验"},
        {"name": "后端工程师", "focus": "强调系统架构、性能优化、数据库设计", "perturbation": "请从'如何构建高性能后端'角度分析", "output_style": "偏向后端技术和系统设计"},
        {"name": "移动开发工程师", "focus": "强调跨平台开发、性能优化、用户体验", "perturbation": "请从'如何提升移动应用体验'角度分析", "output_style": "偏向移动开发技术和用户体验"},
        {"name": "DevOps工程师", "focus": "强调自动化、持续集成、容器编排", "perturbation": "请从'如何提升开发效率'角度分析", "output_style": "偏向自动化和运维效率"},
        {"name": "QA工程师", "focus": "强调质量保障、测试策略、缺陷管理", "perturbation": "请从'如何确保产品质量'角度分析", "output_style": "偏向质量保障和测试策略"}
    ]


async def run_scalability_test():
    """运行扩展性测试"""
    print("\n" + "=" * 70)
    print("SAYG-Mem 扩展性测试")
    print("=" * 70)
    
    os.makedirs(SCALABILITY_TEST_DIR, exist_ok=True)
    
    test_configs = [
        {"agent_count": 40, "label": "40个Agent"},
    ]
    
    results = []
    
    for config in test_configs:
        agent_count = config["agent_count"]
        label = config["label"]
        
        print(f"\n{'='*70}")
        print(f"扩展性测试 - {label}")
        print(f"{'='*70}")
        
        test_result = {
            "agent_count": agent_count,
            "timestamp": datetime.now().isoformat(),
            "a_group": None,
            "b_group": None
        }
        
        # 运行A组
        print(f"\n--- A组 (SAYG-Mem) ---")
        await clear_environment()
        
        try:
            # 临时修改AGENT_ROLES
            import learn_throughput_fixed_time_a as module_a
            original_roles = module_a.AGENT_ROLES.copy()
            
            base_roles = get_base_roles()
            if agent_count <= 10:
                module_a.AGENT_ROLES = base_roles[:agent_count]
            else:
                extra_count = agent_count - 10
                extra_roles = []
                for i in range(extra_count):
                    extra_roles.append({
                        "name": f"角色{i+1}",
                        "focus": "综合分析",
                        "perturbation": f"请从第{i+1}个角度分析",
                        "output_style": "通用分析风格"
                    })
                module_a.AGENT_ROLES = base_roles + extra_roles
            
            a_report = await run_throughput_experiment_a()
            test_result["a_group"] = a_report
            print(f"\n[A组] {label} 完成: {a_report.get('total_rounds', 0)} 轮")
            
            # 恢复原始roles
            module_a.AGENT_ROLES = original_roles
            
        except Exception as e:
            print(f"[A组] {label} 失败: {e}")
            test_result["a_group"] = {"error": str(e)}
        
        await clear_environment()
        await asyncio.sleep(10)
        
        # 运行B组
        print(f"\n--- B组 (Baseline) ---")
        
        try:
            import learn_throughput_fixed_time_b as module_b
            original_roles = module_b.AGENT_ROLES.copy()
            
            if agent_count <= 10:
                module_b.AGENT_ROLES = base_roles[:agent_count]
            else:
                extra_roles = []
                for i in range(extra_count):
                    extra_roles.append({
                        "name": f"角色{i+1}",
                        "focus": "综合分析",
                        "perturbation": f"请从第{i+1}个角度分析",
                        "output_style": "通用分析风格"
                    })
                module_b.AGENT_ROLES = base_roles + extra_roles
            
            b_report = await run_throughput_experiment_b()
            test_result["b_group"] = b_report
            print(f"\n[B组] {label} 完成: {b_report.get('total_rounds', 0)} 轮")
            
            module_b.AGENT_ROLES = original_roles
            
        except Exception as e:
            print(f"[B组] {label} 失败: {e}")
            test_result["b_group"] = {"error": str(e)}
        
        results.append(test_result)
        
        # 保存中间结果
        result_path = os.path.join(SCALABILITY_TEST_DIR, f"scalability_{agent_count}_agents.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n[{label}] 结果已保存: {result_path}")
        
        await asyncio.sleep(30)
    
    return results


def generate_scalability_report(results: List[Dict]):
    """生成扩展性测试报告"""
    print("\n" + "=" * 70)
    print("扩展性测试结果汇总")
    print("=" * 70)
    
    report = []
    report.append("| Agent数量 | A组轮数 | B组轮数 | 吞吐量提升 | A组空闲% | B组空闲% |")
    report.append("|-----------|---------|---------|-----------|----------|----------|")
    
    for r in results:
        agent_count = r["agent_count"]
        a_rounds = r.get("a_group", {}).get("total_rounds", 0) if r.get("a_group") and "error" not in r.get("a_group", {}) else 0
        b_rounds = r.get("b_group", {}).get("total_rounds", 0) if r.get("b_group") and "error" not in r.get("b_group", {}) else 0
        improvement = f"{a_rounds/b_rounds:.2f}x" if b_rounds > 0 else "N/A"
        
        a_idle = r.get("a_group", {}).get("idle_ratio", 0) * 100 if r.get("a_group") and "error" not in r.get("a_group", {}) else 0
        b_idle = r.get("b_group", {}).get("idle_ratio", 0) * 100 if r.get("b_group") and "error" not in r.get("b_group", {}) else 0
        
        report.append(f"| {agent_count} | {a_rounds} | {b_rounds} | {improvement} | {a_idle:.1f}% | {b_idle:.1f}% |")
    
    report_text = "\n".join(report)
    print(report_text)
    
    # 保存报告
    report_path = os.path.join(SCALABILITY_TEST_DIR, "scalability_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# SAYG-Mem 扩展性测试报告\n\n")
        f.write(f"测试时间: {datetime.now().isoformat()}\n\n")
        f.write(report_text)
        f.write("\n\n## 分析结论\n\n")
        f.write("- 随Agent数量增加，SAYG-Mem的吞吐量优势...\n")
        f.write("- 空闲占比变化趋势...\n")
    
    print(f"\n报告已保存: {report_path}")
    
    return report_text


async def main():
    print("\n" + "=" * 70)
    print("SAYG-Mem 扩展性测试")
    print("测试不同Agent数量下的性能对比")
    print("=" * 70)
    
    results = await run_scalability_test()
    
    generate_scalability_report(results)
    
    # 保存完整结果
    all_results_path = os.path.join(SCALABILITY_TEST_DIR, "scalability_all_results.json")
    with open(all_results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n完整结果已保存: {all_results_path}")
    print("\n✅ 扩展性测试完成")


if __name__ == "__main__":
    asyncio.run(main())
