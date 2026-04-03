import json
import os

# 读取详细数据
with open(r'D:\collections2026\phd_application\nanobot1\experiment_docker\results\outputs\experiment_data_detailed.json', 'r', encoding='utf-8') as f:
    detailed_data = json.load(f)

# 读取汇总数据
with open(r'D:\collections2026\phd_application\nanobot1\experiment_docker\results\outputs\experiment_summary.json', 'r', encoding='utf-8') as f:
    summary_data = json.load(f)

# 读取token统计
with open(r'D:\collections2026\phd_application\nanobot1\experiment_docker\results\outputs\token_statistics.json', 'r', encoding='utf-8') as f:
    token_data = json.load(f)

print("=== 实验数据分析报告 ===")
print(f"数据收集时间: 2026-04-02")
print(f"实验任务数: 4个 (Task1_Sales, Task2_User, Task3_Finance, Task4_Review)")
print(f"参与模型: {len(summary_data)}个")
print()

# 分析每个模型的性能
print("=== 各模型性能对比 ===")
for model, stats in summary_data.items():
    print(f"\n[模型] {model}:")
    print(f"  成功率: {stats['success_rate']*100:.1f}% ({stats['successful_tasks']}/{stats['total_tasks']})")
    print(f"  总运行时间: {stats['total_runtime']:.1f}秒")
    print(f"  平均每任务时间: {stats['avg_runtime_per_task']:.1f}秒")
    print(f"  总Token消耗: {stats['total_tokens']:,}")
    print(f"  平均每任务Token: {stats['avg_tokens_per_task']:,}")
    print(f"  Prompt Token占比: {stats['total_prompt_tokens']/stats['total_tokens']*100:.1f}%")
    print(f"  Completion Token占比: {stats['total_completion_tokens']/stats['total_tokens']*100:.1f}%")
    if 'avg_cache_hit_rate' in stats:
        print(f"  平均缓存命中率: {stats['avg_cache_hit_rate']*100:.1f}%")

print("\n=== 任务复杂度分析 ===")
for task_name in token_data.keys():
    print(f"\n[任务] {task_name}:")
    for model in token_data[task_name].keys():
        tokens = token_data[task_name][model]['total_tokens']
        prompt = token_data[task_name][model]['total_prompt_tokens']
        completion = token_data[task_name][model]['total_completion_tokens']
        print(f"  {model}: {tokens:,} tokens (Prompt: {prompt:,}, Completion: {completion:,})")

print("\n=== 性能排名 ===")

# 按速度排名
speed_ranking = sorted(summary_data.items(), key=lambda x: x[1]['avg_runtime_per_task'])
print("[速度] 排名 (平均每任务时间):")
for i, (model, stats) in enumerate(speed_ranking, 1):
    print(f"  {i}. {model}: {stats['avg_runtime_per_task']:.1f}秒")

# 按Token效率排名
token_ranking = sorted(summary_data.items(), key=lambda x: x[1]['avg_tokens_per_task'])
print("\n[Token效率] 排名 (平均每任务Token):")
for i, (model, stats) in enumerate(token_ranking, 1):
    print(f"  {i}. {model}: {stats['avg_tokens_per_task']:,} tokens")

# 按缓存命中率排名
cache_models = [m for m in summary_data.keys() if 'avg_cache_hit_rate' in summary_data[m]]
if cache_models:
    cache_ranking = sorted(cache_models, key=lambda x: summary_data[x]['avg_cache_hit_rate'], reverse=True)
    print("\n[缓存命中率] 排名:")
    for i, model in enumerate(cache_ranking, 1):
        rate = summary_data[model]['avg_cache_hit_rate'] * 100
        print(f"  {i}. {model}: {rate:.1f}%")

print("\n=== 关键发现 ===")

# 计算Qwen3-max-2026-01-23相对于DeepSeek-chat的优势
qwen_time = summary_data['qwen3_max_2026_01_23']['avg_runtime_per_task']
deepseek_time = summary_data['deepseek_chat']['avg_runtime_per_task']
time_saving = (deepseek_time - qwen_time) / deepseek_time * 100

qwen_tokens = summary_data['qwen3_max_2026_01_23']['avg_tokens_per_task']
deepseek_tokens = summary_data['deepseek_chat']['avg_tokens_per_task']
token_saving = (deepseek_tokens - qwen_tokens) / deepseek_tokens * 100

print(f"1. Qwen3-max-2026-01-23 速度优势: 比DeepSeek-chat快 {time_saving:.1f}%")
print(f"2. Qwen3-max-2026-01-23 Token效率优势: 比DeepSeek-chat节省 {token_saving:.1f}% tokens")
print(f"3. DeepSeek-chat 缓存优势: {summary_data['deepseek_chat']['avg_cache_hit_rate']*100:.1f}%命中率")
print(f"4. DeepSeek-reasoner 推理能力: 适合复杂任务，但Token消耗最高")
print(f"5. 任务复杂度梯度: Task3_Finance > Task1_Sales > Task4_Review > Task2_User")