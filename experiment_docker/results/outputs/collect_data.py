#!/usr/bin/env python3
"""Collect all experiment data for analysis"""

import json
from pathlib import Path
from collections import defaultdict

def collect_all_data():
    base_path = Path(r'D:\collections2026\phd_application\nanobot1\experiment_docker\results\outputs')
    
    models = ['deepseek_chat', 'deepseek_reasoner', 'qwen3_max_2026_01_23']
    tasks = ['Task1_Sales', 'Task2_User', 'Task3_Finance', 'Task4_Review']
    
    all_data = defaultdict(dict)
    
    for task in tasks:
        for model in models:
            # 1. Get status data
            status_path = base_path / task / model / 'status.json'
            if status_path.exists():
                with open(status_path, 'r', encoding='utf-8') as f:
                    status = json.load(f)
            else:
                status = {}
            
            # 2. Get token data from token_statistics.json
            token_stats_path = base_path / 'token_statistics.json'
            token_data = {}
            if token_stats_path.exists():
                with open(token_stats_path, 'r', encoding='utf-8') as f:
                    token_stats = json.load(f)
                if task in token_stats and model in token_stats[task]:
                    token_data = token_stats[task][model]
            
            # 3. Combine data
            all_data[task][model] = {
                'status': status,
                'tokens': token_data,
                'success': status.get('success', False),
                'runtime_seconds': status.get('runtime_seconds', 0),
                'total_tokens': token_data.get('total_tokens', 0),
                'prompt_tokens': token_data.get('total_prompt_tokens', 0),
                'completion_tokens': token_data.get('total_completion_tokens', 0),
                'request_count': token_data.get('request_count', 0),
                'cache_hit_rate': token_data.get('cache_hit_rate', 0)
            }
    
    return dict(all_data)

def calculate_summary(data):
    """Calculate summary statistics"""
    summary = defaultdict(lambda: {
        'total_tasks': 0,
        'successful_tasks': 0,
        'total_runtime': 0,
        'total_tokens': 0,
        'total_prompt_tokens': 0,
        'total_completion_tokens': 0,
        'total_requests': 0,
        'avg_cache_hit_rate': 0
    })
    
    for task, task_data in data.items():
        for model, model_data in task_data.items():
            summary[model]['total_tasks'] += 1
            if model_data.get('success'):
                summary[model]['successful_tasks'] += 1
            summary[model]['total_runtime'] += model_data.get('runtime_seconds', 0)
            summary[model]['total_tokens'] += model_data.get('total_tokens', 0)
            summary[model]['total_prompt_tokens'] += model_data.get('prompt_tokens', 0)
            summary[model]['total_completion_tokens'] += model_data.get('completion_tokens', 0)
            summary[model]['total_requests'] += model_data.get('request_count', 0)
            summary[model]['avg_cache_hit_rate'] += model_data.get('cache_hit_rate', 0)
    
    # Calculate averages
    for model in summary:
        if summary[model]['total_tasks'] > 0:
            summary[model]['success_rate'] = summary[model]['successful_tasks'] / summary[model]['total_tasks']
            summary[model]['avg_runtime_per_task'] = summary[model]['total_runtime'] / summary[model]['total_tasks']
            summary[model]['avg_tokens_per_task'] = summary[model]['total_tokens'] / summary[model]['total_tasks']
            summary[model]['avg_cache_hit_rate'] = summary[model]['avg_cache_hit_rate'] / summary[model]['total_tasks']
    
    return dict(summary)

def main():
    print("Collecting experiment data...")
    
    # Collect all data
    all_data = collect_all_data()
    
    # Calculate summary
    summary = calculate_summary(all_data)
    
    # Save detailed data
    output_file = base_path / 'experiment_data_detailed.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"Detailed data saved to {output_file}")
    
    # Save summary
    summary_file = base_path / 'experiment_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Summary data saved to {summary_file}")
    
    # Print summary table
    print("\n" + "="*120)
    print("EXPERIMENT SUMMARY")
    print("="*120)
    print(f"{'Model':<25} {'Tasks':>6} {'Success':>8} {'Rate':>8} {'Avg Time(s)':>12} {'Avg Tokens':>12} {'Cache Rate':>12}")
    print("-"*120)
    
    for model, stats in sorted(summary.items()):
        print(f"{model:<25} {stats['total_tasks']:>6} {stats['successful_tasks']:>8} "
              f"{stats.get('success_rate', 0)*100:>7.1f}% {stats.get('avg_runtime_per_task', 0):>11.1f} "
              f"{stats.get('avg_tokens_per_task', 0):>11.0f} {stats.get('avg_cache_hit_rate', 0)*100:>11.1f}%")
    
    # Print task details
    print("\n" + "="*120)
    print("TASK DETAILS")
    print("="*120)
    
    for task in ['Task1_Sales', 'Task2_User', 'Task3_Finance', 'Task4_Review']:
        print(f"\n### {task}")
        print("-"*100)
        print(f"{'Model':<25} {'Success':>8} {'Time(s)':>10} {'Tokens':>10} {'Prompt':>10} {'Completion':>12} {'Cache':>10}")
        print("-"*100)
        
        if task in all_data:
            for model, data in all_data[task].items():
                print(f"{model:<25} {str(data.get('success', False)):>8} {data.get('runtime_seconds', 0):>10.1f} "
                      f"{data.get('total_tokens', 0):>10} {data.get('prompt_tokens', 0):>10} "
                      f"{data.get('completion_tokens', 0):>12} {data.get('cache_hit_rate', 0)*100:>9.1f}%")

if __name__ == '__main__':
    base_path = Path(r'D:\collections2026\phd_application\nanobot1\experiment_docker\results\outputs')
    main()