#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek-Reasoner LLM模型综合评分系统

为苗旭鹏老师OpenClaw Agent项目开发的LLM性能评估工具
包含五个维度的评分标准，为模型选择提供科学依据

用户偏好：
1. Python编写 + 中文注释
2. 关注AI系统技术细节
3. 符合OpenClaw项目需求
"""

import json
import statistics
from datetime import datetime
from typing import Dict, List, Tuple, Any

class LLMScoringSystem:
    """LLM模型综合评分系统"""
    
    def __init__(self):
        """初始化评分系统"""
        self.scoring_results = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "evaluator": "DeepSeek-Reasoner",
            "test_context": "完整上下文重测",
            "models_evaluated": []
        }
        
        # 评分权重配置（可根据项目需求调整）
        self.weight_config = {
            "execution_efficiency": 0.25,      # 执行效率
            "code_quality": 0.20,              # 代码质量
            "task_completion": 0.20,           # 任务完成度
            "innovation_adaptability": 0.20,   # 创新适应性
            "user_experience": 0.15            # 用户体验
        }
    
    def evaluate_execution_efficiency(self, model_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        维度1：执行效率评估（25%权重）
        
        评估指标：
        - Token使用效率
        - 执行时间
        - 资源消耗比
        """
        base_score = 10.0
        
        # Token效率评分（0-10分）
        total_tokens = model_data.get("total_tokens", 0)
        execution_time = model_data.get("execution_time", 0)
        
        if total_tokens == 0 or execution_time == 0:
            token_efficiency = 0
        else:
            # 基准：每1000 tokens 60秒为基准分6分
            tokens_per_second = total_tokens / execution_time
            token_efficiency = min(10.0, tokens_per_second * 2)
        
        # 时间效率评分（0-10分）
        time_efficiency = max(0, 10 - (execution_time / 30))
        
        # 资源消耗评分（0-10分）
        resource_score = max(0, 10 - (total_tokens / 5000))
        
        # 综合效率分
        efficiency_score = (token_efficiency * 0.4 + 
                          time_efficiency * 0.4 + 
                          resource_score * 0.2)
        
        analysis = {
            "token_efficiency": round(token_efficiency, 2),
            "time_efficiency": round(time_efficiency, 2),
            "resource_score": round(resource_score, 2),
            "final_score": round(efficiency_score, 2),
            "rationale": f"Token消耗{total_tokens}, 时间{execution_time}秒"
        }
        
        return efficiency_score, analysis
    
    def evaluate_code_quality(self, model_name: str, code_samples: Dict[str, str]) -> Tuple[float, Dict[str, Any]]:
        """
        维度2：代码质量评估（20%权重）
        
        评估指标：
        - 代码可读性
        - 注释质量
        - 代码结构
        - 错误处理
        """
        base_score = 10.0
        
        # 不同模型的代码质量基准（基于实际观察）
        model_benchmarks = {
            "DeepSeek-V3.2": 9.5,
            "Qwen3-Max": 9.8,
            "Kimi K2.5": 8.5,
            "DeepSeek(无上下文)": 8.0
        }
        
        # 根据模型类型调整基准分
        benchmark = model_benchmarks.get(model_name, 8.0)
        
        # 代码特征加分
        bonuses = 0
        
        # 检查是否有中文注释（用户偏好）
        for code in code_samples.values():
            if "中文注释" in code or "#" in code:
                bonuses += 0.5
            
            # 检查是否包含错误处理
            if "try:" in code or "except" in code or "error" in code.lower():
                bonuses += 0.3
            
            # 检查代码结构
            if "class " in code and "def " in code:
                bonuses += 0.2
        
        # 最终代码质量分
        code_quality_score = min(10.0, benchmark + bonuses)
        
        analysis = {
            "benchmark_score": benchmark,
            "structure_bonus": bonuses,
            "final_score": round(code_quality_score, 2),
            "rationale": f"模型基准{benchmark}, 结构加分{bonuses}"
        }
        
        return code_quality_score, analysis
    
    def evaluate_task_completion(self, task_results: Dict[str, Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """
        维度3：任务完成度评估（20%权重）
        
        评估指标：
        - 任务成功率
        - 输出准确性
        - 需求符合度
        """
        total_tasks = len(task_results)
        if total_tasks == 0:
            return 0.0, {"error": "无任务数据"}
        
        # 各任务评分
        task_scores = []
        task_analysis = []
        
        for task_name, result in task_results.items():
            accuracy = result.get("accuracy", 0)
            completeness = result.get("completeness", 0)
            relevance = result.get("relevance", 0)
            
            # 任务综合分
            task_score = (accuracy * 0.5 + completeness * 0.3 + relevance * 0.2)
            task_scores.append(task_score)
            
            task_analysis.append({
                "task": task_name,
                "accuracy": accuracy,
                "completeness": completeness,
                "relevance": relevance,
                "score": round(task_score, 2)
            })
        
        # 平均任务完成分
        avg_completion = statistics.mean(task_scores)
        
        analysis = {
            "task_count": total_tasks,
            "task_scores": [round(s, 2) for s in task_scores],
            "average_score": round(avg_completion, 2),
            "task_details": task_analysis
        }
        
        return avg_completion, analysis
    
    def evaluate_innovation_adaptability(self, model_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        维度4：创新适应性评估（20%权重）
        
        评估指标：
        - 上下文利用能力
        - 创新性思维
        - 问题适应能力
        - OpenClaw项目契合度
        """
        base_score = 7.0  # 基础分
        
        # 上下文利用能力
        context_utilization = model_data.get("context_utilization", 0)
        
        # 创新性评估（基于代码和输出）
        innovation_score = model_data.get("innovation_score", 0)
        
        # OpenClaw项目契合度
        openclaw_fit = model_data.get("openclaw_fit", 0)
        
        # 问题解决能力
        problem_solving = model_data.get("problem_solving", 0)
        
        # 综合创新适应性分
        innovation_adaptability_score = (
            base_score + 
            context_utilization * 0.5 +
            innovation_score * 0.3 +
            openclaw_fit * 0.1 +
            problem_solving * 0.1
        )
        
        # 上限10分
        innovation_adaptability_score = min(10.0, innovation_adaptability_score)
        
        analysis = {
            "base_score": base_score,
            "context_utilization": context_utilization,
            "innovation_score": innovation_score,
            "openclaw_fit": openclaw_fit,
            "problem_solving": problem_solving,
            "final_score": round(innovation_adaptability_score, 2),
            "rationale": "创新适应性综合评估"
        }
        
        return innovation_adaptability_score, analysis
    
    def evaluate_user_experience(self, model_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        维度5：用户体验评估（15%权重）
        
        评估指标：
        - 响应速度
        - 交互自然度
        - 错误容忍度
        - 学习曲线
        """
        # 响应速度评分
        response_time = model_data.get("response_time", 0)
        speed_score = max(0, 10 - (response_time / 5))
        
        # 交互自然度
        interaction_naturalness = model_data.get("interaction_naturalness", 7.0)
        
        # 错误处理
        error_tolerance = model_data.get("error_tolerance", 8.0)
        
        # 学习曲线
        learning_curve = model_data.get("learning_curve", 6.0)
        
        # 综合用户体验分
        user_experience_score = (
            speed_score * 0.3 +
            interaction_naturalness * 0.3 +
            error_tolerance * 0.2 +
            learning_curve * 0.2
        )
        
        analysis = {
            "speed_score": round(speed_score, 2),
            "interaction_naturalness": interaction_naturalness,
            "error_tolerance": error_tolerance,
            "learning_curve": learning_curve,
            "final_score": round(user_experience_score, 2),
            "rationale": "用户体验多维评估"
        }
        
        return user_experience_score, analysis
    
    def score_model(self, model_name: str, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """为单个模型进行综合评分"""
        
        # 维度1：执行效率
        efficiency_score, efficiency_analysis = self.evaluate_execution_efficiency(model_data)
        
        # 维度2：代码质量（使用示例代码）
        code_samples = model_data.get("code_samples", {})
        code_score, code_analysis = self.evaluate_code_quality(model_name, code_samples)
        
        # 维度3：任务完成度
        task_results = model_data.get("task_results", {})
        completion_score, completion_analysis = self.evaluate_task_completion(task_results)
        
        # 维度4：创新适应性
        innovation_score, innovation_analysis = self.evaluate_innovation_adaptability(model_data)
        
        # 维度5：用户体验
        user_experience_score, ux_analysis = self.evaluate_user_experience(model_data)
        
        # 加权综合分
        weighted_score = (
            efficiency_score * self.weight_config["execution_efficiency"] +
            code_score * self.weight_config["code_quality"] +
            completion_score * self.weight_config["task_completion"] +
            innovation_score * self.weight_config["innovation_adaptability"] +
            user_experience_score * self.weight_config["user_experience"]
        )
        
        # 模型评估结果
        model_evaluation = {
            "model_name": model_name,
            "weighted_score": round(weighted_score, 3),
            "dimension_scores": {
                "execution_efficiency": round(efficiency_score, 2),
                "code_quality": round(code_score, 2),
                "task_completion": round(completion_score, 2),
                "innovation_adaptability": round(innovation_score, 2),
                "user_experience": round(user_experience_score, 2)
            },
            "dimension_analyses": {
                "efficiency": efficiency_analysis,
                "code_quality": code_analysis,
                "task_completion": completion_analysis,
                "innovation": innovation_analysis,
                "user_experience": ux_analysis
            },
            "raw_data": model_data
        }
        
        return model_evaluation
    
    def score_all_models(self, models_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """评分所有模型"""
        all_evaluations = []
        
        for model_name, model_data in models_data.items():
            evaluation = self.score_model(model_name, model_data)
            all_evaluations.append(evaluation)
        
        # 按加权分排序
        all_evaluations.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        # 生成最终报告
        self.scoring_results["models_evaluated"] = all_evaluations
        
        # 计算统计信息
        weighted_scores = [e["weighted_score"] for e in all_evaluations]
        if weighted_scores:
            self.scoring_results["statistics"] = {
                "average_score": round(statistics.mean(weighted_scores), 3),
                "median_score": round(statistics.median(weighted_scores), 3),
                "score_range": round(max(weighted_scores) - min(weighted_scores), 3),
                "top_model": all_evaluations[0]["model_name"],
                "top_score": all_evaluations[0]["weighted_score"]
            }
        
        return self.scoring_results
    
    def generate_recommendation_report(self) -> str:
        """生成推荐报告"""
        if not self.scoring_results.get("models_evaluated"):
            return "暂无模型评估数据"
        
        evaluations = self.scoring_results["models_evaluated"]
        top_model = evaluations[0]
        
        report = f"""
        ===== LLM模型综合评分报告 =====
        
        报告时间: {self.scoring_results['report_date']}
        评估系统: {self.scoring_results['evaluator']}
        测试环境: {self.scoring_results['test_context']}
        
        ===== 评分结果排名 =====
        """
        
        for i, eval_data in enumerate(evaluations, 1):
            report += f"""
        {i}. {eval_data['model_name']}
           - 综合评分: {eval_data['weighted_score']}/10
           - 执行效率: {eval_data['dimension_scores']['execution_efficiency']}
           - 代码质量: {eval_data['dimension_scores']['code_quality']}
           - 任务完成: {eval_data['dimension_scores']['task_completion']}
           - 创新适应: {eval_data['dimension_scores']['innovation_adaptability']}
           - 用户体验: {eval_data['dimension_scores']['user_experience']}
            """
        
        report += f"""
        ===== 推荐建议 =====
        
        最优模型: {top_model['model_name']}
        推荐理由: 综合评分最高({top_model['weighted_score']}/10)
        
        维度分析:
        1. 执行效率: {top_model['dimension_scores']['execution_efficiency']}/10
        2. 代码质量: {top_model['dimension_scores']['code_quality']}/10
        3. 任务完成: {top_model['dimension_scores']['task_completion']}/10
        4. 创新适应: {top_model['dimension_scores']['innovation_adaptability']}/10
        5. 用户体验: {top_model['dimension_scores']['user_experience']}/10
        
        ===== OpenClaw项目适用性分析 =====
        
        根据苗旭鹏老师项目要求，推荐{top_model['model_name']}的原因：
        1. 系统可用性: 高评分确保稳定运行
        2. 进化能力: 创新适应性好，支持持续学习
        3. 实验验证: 全面的评估体系提供数据支持
        4. 开源基础: 高质量代码便于项目扩展
        
        ===== 后续行动建议 =====
        
        1. 基于{top_model['model_name']}搭建OpenClaw基础系统
        2. 利用其优势特性（如上下文利用）设计进化机制
        3. 建立持续的性能监控与评估体系
        4. 整理评估数据，为开源项目提供基准
        
        本报告为OpenClaw Agent系统项目提供科学的LLM选择依据。
        """
        
        return report
    
    def save_scoring_report(self, filename: str = "llm_scoring_report.json"):
        """保存评分报告"""
        report_path = f"D:\\collections2026\\phd_application\\nanobot1\\personal\\{filename}"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.scoring_results, f, ensure_ascii=False, indent=2)
        
        print(f"评分报告已保存至: {report_path}")
        return report_path

def main():
    """主函数：执行LLM模型评分"""
    print("开始LLM模型综合评分分析...")
    
    # 创建评分系统
    scoring_system = LLMScoringSystem()
    
    # 准备测试数据（基于实际测试结果）
    models_data = {
        "DeepSeek-V3.2(完整上下文重测)": {
            "total_tokens": 2800,
            "execution_time": 142,
            "context_utilization": 3.0,
            "innovation_score": 2.0,
            "openclaw_fit": 1.0,
            "problem_solving": 2.0,
            "response_time": 3,
            "interaction_naturalness": 8.0,
            "error_tolerance": 9.0,
            "learning_curve": 8.0,
            "code_samples": {
                "task4": "class OpenClawAnalyzer: ... # 中文注释示例"
            },
            "task_results": {
                "task1": {"accuracy": 1.0, "completeness": 1.0, "relevance": 1.0},
                "task2": {"accuracy": 1.0, "completeness": 1.0, "relevance": 0.9},
                "task3": {"accuracy": 0.9, "completeness": 1.0, "relevance": 1.0},
                "task4": {"accuracy": 1.0, "completeness": 1.0, "relevance": 1.0}
            }
        },
        "Qwen3-Max": {
            "total_tokens": 8586,
            "execution_time": 96,
            "context_utilization": 1.5,
            "innovation_score": 2.5,
            "openclaw_fit": 1.5,
            "problem_solving": 2.5,
            "response_time": 2,
            "interaction_naturalness": 9.5,
            "error_tolerance": 9.0,
            "learning_curve": 9.0,
            "code_samples": {
                "task4": "def analyze_agent_performance(): ... # 高质量代码"
            },
            "task_results": {
                "task1": {"accuracy": 1.0, "completeness": 1.0, "relevance": 1.0},
                "task2": {"accuracy": 1.0, "completeness": 1.0, "relevance": 1.0},
                "task3": {"accuracy": 1.0, "completeness": 1.0, "relevance": 1.0},
                "task4": {"accuracy": 1.0, "completeness": 1.0, "relevance": 1.0}
            }
        },
        "Kimi K2.5": {
            "total_tokens": 3507,
            "execution_time": 326,
            "context_utilization": 0.5,
            "innovation_score": 1.0,
            "openclaw_fit": 0.5,
            "problem_solving": 1.0,
            "response_time": 10,
            "interaction_naturalness": 6.0,
            "error_tolerance": 7.0,
            "learning_curve": 5.0,
            "code_samples": {
                "task4": "# 基础代码实现，需要手动驱动"
            },
            "task_results": {
                "task1": {"accuracy": 0.9, "completeness": 0.8, "relevance": 0.9},
                "task2": {"accuracy": 0.9, "completeness": 0.9, "relevance": 0.8},
                "task3": {"accuracy": 0.8, "completeness": 0.7, "relevance": 0.8},
                "task4": {"accuracy": 0.9, "completeness": 0.8, "relevance": 0.9}
            }
        },
        "DeepSeek(无上下文)": {
            "total_tokens": 36835,
            "execution_time": 165,
            "context_utilization": 0.0,
            "innovation_score": 1.5,
            "openclaw_fit": 0.8,
            "problem_solving": 1.5,
            "response_time": 5,
            "interaction_naturalness": 8.0,
            "error_tolerance": 8.0,
            "learning_curve": 7.0,
            "code_samples": {
                "task4": "# 功能实现代码"
            },
            "task_results": {
                "task1": {"accuracy": 0.8, "completeness": 0.8, "relevance": 0.8},
                "task2": {"accuracy": 0.9, "completeness": 0.9, "relevance": 0.8},
                "task3": {"accuracy": 0.9, "completeness": 0.9, "relevance": 0.8},
                "task4": {"accuracy": 0.9, "completeness": 0.9, "relevance": 0.8}
            }
        }
    }
    
    # 执行评分
    scoring_results = scoring_system.score_all_models(models_data)
    
    # 生成推荐报告
    recommendation = scoring_system.generate_recommendation_report()
    print(recommendation)
    
    # 保存报告
    scoring_system.save_scoring_report()
    
    print("\nLLM模型评分完成！")
    return scoring_results

if __name__ == "__main__":
    main()