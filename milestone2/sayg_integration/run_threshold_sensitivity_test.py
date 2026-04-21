"""
SAYG-Mem 参数敏感性实验
测试 merge_threshold 和 merge_interval 对系统性能的影响

实验设计：
- 第一阶段：固定 interval=60s，测 threshold ∈ {5, 20, 50}
- 第二阶段：固定最优 threshold，测 interval ∈ {30s, 60s, 120s}

预计：5组 × 5分钟 = 25分钟

使用方式：
1. 先启动 BFF 服务: ./run_km_system.sh
2. 然后运行本脚本: python run_threshold_sensitivity_test.py
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BFF_BASE_URL = "http://localhost:8000"
EXPERIMENT_DIR = Path(__file__).parent / "experiment_data" / "threshold_sensitivity"
TIME_BUDGET = 150
AGENT_COUNT = 10

EXPERIMENT_CONFIGS = [
    {"threshold": 5, "interval": 60, "label": "激进(5,60s)", "stage": 1},
    {"threshold": 20, "interval": 60, "label": "均衡(20,60s)", "stage": 1},
    {"threshold": 50, "interval": 60, "label": "保守(50,120s)", "stage": 1},
    {"threshold": 20, "interval": 30, "label": "短间隔(20,30s)", "stage": 2},
    {"threshold": 20, "interval": 120, "label": "长间隔(20,120s)", "stage": 2},
]


def run_docker_command(cmd: list) -> tuple:
    """运行docker命令"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def stop_consolidator() -> bool:
    """停止Consolidator容器"""
    print("[Docker] 停止 Consolidator 容器...")
    returncode, stdout, stderr = run_docker_command(["docker", "ps", "-q", "--filter", "name=consolidator_"])
    if stdout.strip():
        returncode, stdout, stderr = run_docker_command(["docker", "stop"] + stdout.strip().split())
        if returncode == 0:
            print("[Docker] Consolidator 已停止")
            return True
    return True


def cleanup_all_agents() -> bool:
    """清理所有Agent容器"""
    print("[Docker] 清理 Agent 容器...")
    returncode, stdout, stderr = run_docker_command(["docker", "ps", "-q", "--filter", "name=nanobot_conv_"])
    if stdout.strip():
        returncode, stdout, stderr = run_docker_command(["docker", "stop"] + stdout.strip().split())
        run_docker_command(["docker", "rm"] + stdout.strip().split())
    print("[Docker] Agent 容器已清理")
    return True


def clear_public_memory():
    """清空PublicMemory"""
    pm_path = Path("d:/collections2026/phd_application/nanobot1/milestone2/data/public_memory/public_memory.jsonl")
    if pm_path.exists():
        pm_path.unlink()
        print(f"[清理] 已清空 PublicMemory: {pm_path}")


def restart_bff_with_config(threshold: int, interval: int) -> bool:
    """使用新配置重启BFF服务"""
    print(f"\n[配置] KM - threshold={threshold}, interval={interval}s")

    stop_consolidator()
    cleanup_all_agents()
    time.sleep(3)

    os.environ["KM_MERGE_THRESHOLD"] = str(threshold)
    os.environ["KM_MERGE_INTERVAL"] = str(interval)

    clear_public_memory()
    time.sleep(2)

    return True


async def wait_for_bff():
    """等待BFF服务就绪"""
    print("[等待] BFF 服务...")
    for i in range(30):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{BFF_BASE_URL}/health")
                if resp.status_code == 200:
                    print("[等待] BFF 就绪")
                    return True
        except:
            pass
        await asyncio.sleep(2)
    return False


async def wait_for_km():
    """等待KM就绪"""
    print("[等待] KM 服务...")
    for i in range(30):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{BFF_BASE_URL}/knowledge-manager/stats")
                if resp.status_code == 200:
                    stats = resp.json()
                    print(f"[等待] KM 就绪 - 阈值：{stats.get('merge_threshold', '?')}条，间隔：{stats.get('merge_interval', '?')}秒")
                    return True
        except:
            pass
        await asyncio.sleep(2)
    return False


async def run_single_experiment(label: str) -> dict:
    """运行单组实验"""
    print(f"\n{'='*60}")
    print(f"[实验] {label}")
    print(f"{'='*60}")

    sys.path.insert(0, str(Path(__file__).parent))
    from sayg_integration.learn_throughput_fixed_time_a import run_throughput_experiment_a

    result = await run_throughput_experiment_a()
    return result


def analyze_results(results: list) -> dict:
    """分析实验结果"""
    analysis = {"stage1": [], "stage2": [], "best": None, "best_sar": 0}

    for r in results:
        config = r["config"]
        result = r.get("result", {})
        pm_count = result.get("public_memory_count", 0)
        actual_time = result.get("actual_time", TIME_BUDGET)
        sar = pm_count / actual_time if actual_time > 0 else 0

        entry = {
            "label": config["label"],
            "threshold": config["threshold"],
            "interval": config["interval"],
            "pm_count": pm_count,
            "actual_time": actual_time,
            "sar": sar,
        }

        if config["stage"] == 1:
            analysis["stage1"].append(entry)
        else:
            analysis["stage2"].append(entry)

        if sar > analysis["best_sar"]:
            analysis["best_sar"] = sar
            analysis["best"] = entry

    return analysis


def generate_report(analysis: dict) -> str:
    """生成Markdown报告"""
    lines = []
    lines.append("# SAYG-Mem 参数敏感性实验报告\n")
    lines.append(f"**实验时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**实验配置**: {AGENT_COUNT} Agent, {TIME_BUDGET}s 时间预算\n\n")

    lines.append("## 第一阶段：阈值敏感性（固定 interval=60s）\n\n")
    lines.append("| 配置 | threshold | interval | PublicMemory | SAR(条/秒) |\n")
    lines.append("|:---|:---|:---|:---|:---|\n")
    for e in analysis["stage1"]:
        sar_str = f"{e['sar']:.4f}" if e['sar'] > 0 else "N/A"
        lines.append(f"| {e['label']} | {e['threshold']} | {e['interval']}s | {e['pm_count']} | {sar_str} |\n")

    lines.append("\n## 第二阶段：间隔敏感性（固定 threshold=20）\n\n")
    lines.append("| 配置 | threshold | interval | PublicMemory | SAR(条/秒) |\n")
    lines.append("|:---|:---|:---|:---|:---|\n")
    for e in analysis["stage2"]:
        sar_str = f"{e['sar']:.4f}" if e['sar'] > 0 else "N/A"
        lines.append(f"| {e['label']} | {e['threshold']} | {e['interval']}s | {e['pm_count']} | {sar_str} |\n")

    if analysis["best"]:
        best = analysis["best"]
        lines.append("\n## 结论\n\n")
        lines.append(f"**最佳配置**: merge_threshold={best['threshold']}, merge_interval={best['interval']}s\n")
        lines.append(f"**最佳SAR**: {best['sar']:.4f} 条/秒\n")
        lines.append(f"**PublicMemory产出**: {best['pm_count']} 条\n")

    return "".join(lines)


async def main():
    print("\n" + "="*70)
    print("SAYG-Mem 参数敏感性实验")
    print("="*70)
    print(f"实验配置: {len(EXPERIMENT_CONFIGS)} 组")
    print(f"预计时间: {len(EXPERIMENT_CONFIGS) * 6} 分钟\n")

    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for i, config in enumerate(EXPERIMENT_CONFIGS):
        print(f"\n[进度] 第 {i+1}/{len(EXPERIMENT_CONFIGS)} 组")

        restart_bff_with_config(config["threshold"], config["interval"])

        await asyncio.sleep(5)

        if not await wait_for_bff():
            print("[错误] BFF 服务未就绪")
            continue

        await wait_for_km()

        exp_result = await run_single_experiment(config["label"])

        results.append({
            "config": config,
            "result": exp_result,
        })

        cleanup_all_agents()
        await asyncio.sleep(10)

    print("\n" + "="*70)
    print("分析结果...")
    print("="*70)

    analysis = analyze_results(results)
    report = generate_report(analysis)
    print(report)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = EXPERIMENT_DIR / f"results_{timestamp}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "analysis": analysis}, f, ensure_ascii=False, indent=2)

    report_path = EXPERIMENT_DIR / f"report_{timestamp}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n[完成] 结果: {results_path}")
    print(f"[完成] 报告: {report_path}")


if __name__ == "__main__":
    import httpx
    asyncio.run(main())