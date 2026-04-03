#!/usr/bin/env python3
"""Parse api_responses.jsonl files and calculate token statistics"""

import json
from pathlib import Path
from collections import defaultdict

def parse_api_responses(file_path):
    """Parse a jsonl file and return token statistics"""
    total_prompt = 0
    total_completion = 0
    total_tokens = 0
    request_count = 0
    cache_hits = 0
    cache_misses = 0

    if not file_path.exists():
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                resp = data.get('response', {})
                usage = resp.get('usage', {})

                total_prompt += usage.get('prompt_tokens', 0)
                total_completion += usage.get('completion_tokens', 0)
                total_tokens += usage.get('total_tokens', 0)
                request_count += 1

                cache_hits += usage.get('prompt_cache_hit_tokens', 0)
                cache_misses += usage.get('prompt_cache_miss_tokens', 0)
            except json.JSONDecodeError:
                continue

    return {
        'total_prompt_tokens': total_prompt,
        'total_completion_tokens': total_completion,
        'total_tokens': total_tokens,
        'request_count': request_count,
        'cache_hits': cache_hits,
        'cache_misses': cache_misses,
        'cache_hit_rate': cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
    }

def main():
    base_path = Path(r'D:\collections2026\phd_application\nanobot1\experiment_docker\results\outputs')

    models = ['deepseek_chat', 'deepseek_reasoner', 'qwen3_max_2026_01_23']
    tasks = ['Task1_Sales', 'Task2_User', 'Task3_Finance', 'Task4_Review']

    results = defaultdict(dict)

    for task in tasks:
        for model in models:
            jsonl_path = base_path / task / model / 'api_responses.jsonl'
            stats = parse_api_responses(jsonl_path)
            if stats:
                results[task][model] = stats

    # Print results
    print("=" * 100)
    print("Token Statistics by Task and Model")
    print("=" * 100)

    for task in tasks:
        print(f"\n### {task}")
        print("-" * 90)
        print(f"{'Model':<30} {'Requests':>10} {'Prompt':>10} {'Completion':>12} {'Total':>10} {'Cache Hits':>12} {'Cache Rate':>12}")
        print("-" * 90)

        for model, stats in results[task].items():
            print(f"{model:<30} {stats['request_count']:>10} {stats['total_prompt_tokens']:>10} "
                  f"{stats['total_completion_tokens']:>12} {stats['total_tokens']:>10} "
                  f"{stats['cache_hits']:>12} {stats['cache_hit_rate']*100:>11.1f}%")

    # Summary by model
    print("\n" + "=" * 100)
    print("Summary by Model (Across All Tasks)")
    print("=" * 100)

    model_summary = defaultdict(lambda: {'total_requests': 0, 'total_prompt': 0, 'total_completion': 0,
                                          'total_tokens': 0, 'total_cache_hits': 0, 'total_cache_misses': 0})

    for task, task_results in results.items():
        for model, stats in task_results.items():
            model_summary[model]['total_requests'] += stats['request_count']
            model_summary[model]['total_prompt'] += stats['total_prompt_tokens']
            model_summary[model]['total_completion'] += stats['total_completion_tokens']
            model_summary[model]['total_tokens'] += stats['total_tokens']
            model_summary[model]['total_cache_hits'] += stats['cache_hits']
            model_summary[model]['total_cache_misses'] += stats['cache_misses']

    print(f"\n{'Model':<30} {'Tasks':>6} {'Requests':>10} {'Prompt':>10} {'Completion':>12} {'Total':>10} {'Cache Rate':>12}")
    print("-" * 90)

    for model, summary in sorted(model_summary.items()):
        cache_rate = summary['total_cache_hits'] / (summary['total_cache_hits'] + summary['total_cache_misses']) if (summary['total_cache_hits'] + summary['total_cache_misses']) > 0 else 0
        print(f"{model:<30} {4:>6} {summary['total_requests']:>10} {summary['total_prompt']:>10} "
              f"{summary['total_completion']:>12} {summary['total_tokens']:>10} {cache_rate*100:>11.1f}%")

    # Save to JSON
    output_file = base_path / 'token_statistics.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dict(results), f, indent=2, ensure_ascii=False)
    print(f"\n✅ Statistics saved to {output_file}")

if __name__ == '__main__':
    main()
