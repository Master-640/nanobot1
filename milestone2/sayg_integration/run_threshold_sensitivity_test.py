"""
SAYG-Mem 参数敏感性实验
测试 merge_threshold 和 merge_interval 对系统性能的影响

实验设计：3×3 九组实验
- threshold ∈ {5, 20, 50}
- interval ∈ {30s, 60s, 120s}

预计：9组 × 5分钟 = ~45分钟

实验流程：
1. 设置环境变量
2. 启动BFF服务（用新环境变量）
3. 运行实验
4. 清理
5. 重复...
"""

import asyncio
import os
import sys
import json
import time
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import httpx

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from learn_throughput_fixed_time_a import run_throughput_experiment_a
from run_throughput_comparison import get_pm_path

BFF_BASE_URL = os.environ.get("BFF_BASE_URL", "http://localhost:8000")
EXPERIMENT_DIR = os.path.join(os.path.dirname(__file__), "experiment_data", "threshold_sensitivity")
BASE_DIR = os.path.dirname(__file__)
TIME_BUDGET = 150
AGENT_COUNT = 10

EXPERIMENT_CONFIGS = [
    {"threshold": 5, "interval": 30, "label": "激进-短(5,30s)", "stage": 1},
    {"threshold": 20, "interval": 120, "label": "均衡-长(20,120s)", "stage": 2},
    {"threshold": 50, "interval": 30, "label": "保守-短(50,30s)", "stage": 3},
    {"threshold": 50, "interval": 60, "label": "保守-中(50,60s)", "stage": 3},
    {"threshold": 50, "interval": 120, "label": "保守-长(50,120s)", "stage": 3},
]


def set_km_env(threshold: int, interval: int):
    """设置KM相关环境变量"""
    os.environ["KM_MERGE_THRESHOLD"] = str(threshold)
    os.environ["KM_MERGE_INTERVAL"] = str(interval)
    print(f"  [环境] KM_MERGE_THRESHOLD={threshold}")
    print(f"  [环境] KM_MERGE_INTERVAL={interval}s")


def stop_and_remove_container(name_pattern: str) -> bool:
    """停止并删除匹配名称模式的容器"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", f"--filter=name={name_pattern}"],
            capture_output=True, text=True
        )
        container_ids = result.stdout.strip().split()
        if container_ids:
            subprocess.run(["docker", "stop"] + container_ids, capture_output=True, timeout=30)
            subprocess.run(["docker", "rm"] + container_ids, capture_output=True, timeout=30)
            return True
    except Exception as e:
        print(f"  [Docker] 清理容器异常: {e}")
    return True


def stop_existing_bff():
    """停止可能正在运行的BFF进程"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter=name=bff"],
            capture_output=True, text=True
        )
        bff_ids = result.stdout.strip().split()
        if bff_ids:
            subprocess.run(["docker", "stop"] + bff_ids, capture_output=True, timeout=30)
            subprocess.run(["docker", "rm"] + bff_ids, capture_output=True, timeout=30)
            print("  [BFF] 已停止现有BFF容器")
    except Exception as e:
        print(f"  [BFF] 容器停止失败: {e}")

    try:
        result = subprocess.run(
            ["bash", "-c", "pgrep -f 'bff.bff_service' 2>/dev/null || true"],
            capture_output=True, text=True
        )
        bff_pids = result.stdout.strip().split()
        if bff_pids:
            subprocess.run(["bash", "-c", "pkill -f 'bff.bff_service' 2>/dev/null || true"])
            print("  [BFF] 已停止现有BFF进程")
    except Exception as e:
        pass


def clear_public_memory():
    """清空PublicMemory"""
    pm_path = get_pm_path()
    if os.path.exists(pm_path):
        os.remove(pm_path)
        print(f"  [清理] 已清空 PublicMemory")


def prepare_experiment_config(threshold: int, interval: int) -> bool:
    """准备实验配置"""
    print(f"\n[配置] threshold={threshold}, interval={interval}s")

    set_km_env(threshold, interval)

    print("  [BFF] 停止现有BFF进程...")
    stop_existing_bff()

    print("  [清理] 停止所有容器...")
    stop_and_remove_container("nanobot_km_")
    stop_and_remove_container("consolidator_")
    stop_and_remove_container("nanobot_conv_")

    time.sleep(2)
    clear_public_memory()
    time.sleep(1)
    return True


def stop_bff():
    """停止BFF服务"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter=name=bff"],
            capture_output=True, text=True
        )
        bff_ids = result.stdout.strip().split()
        if bff_ids:
            subprocess.run(["docker", "stop"] + bff_ids, capture_output=True, timeout=30)
            subprocess.run(["docker", "rm"] + bff_ids, capture_output=True, timeout=30)
            print("  [BFF] 已停止")
    except Exception as e:
        print(f"  [BFF] 停止失败: {e}")


def start_bff_process(threshold: int, interval: int) -> subprocess.Popen:
    """启动BFF服务（使用指定的环境变量）"""
    print("  [BFF] 启动中...")

    env = os.environ.copy()
    env["KM_MERGE_THRESHOLD"] = str(threshold)
    env["KM_MERGE_INTERVAL"] = str(interval)

    script_dir = Path(__file__).parent.parent
    bff_module = script_dir / "bff" / "bff_service.py"

    cmd = [sys.executable, str(bff_module)]

    exp_dir = script_dir / "experiment_data" / "threshold_sensitivity"
    exp_dir.mkdir(parents=True, exist_ok=True)
    log_file = open(exp_dir / f"bff_{threshold}_{interval}.log", "w")

    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=str(script_dir)
    )

    return process


async def wait_for_bff_ready(timeout: int = 60) -> bool:
    """等待BFF服务就绪"""
    print("  [BFF] 等待服务就绪...")
    for i in range(timeout // 2):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{BFF_BASE_URL}/health")
                if resp.status_code == 200:
                    print("  [BFF] 服务就绪")
                    return True
        except:
            pass
        await asyncio.sleep(2)
    print("  [BFF] 服务超时")
    return False


async def verify_km_config() -> dict:
    """验证KM配置"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BFF_BASE_URL}/knowledge-manager/stats")
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    return {"merge_threshold": "?", "merge_interval": "?"}


async def run_single_experiment(label: str, threshold: int, interval: int) -> dict:
    """运行单组实验"""
    print(f"\n{'='*60}")
    print(f"[实验] {label}")
    print(f"{'='*60}")

    prepare_experiment_config(threshold, interval)

    print("  [BFF] 启动BFF服务（使用新环境变量）...")
    bff_process = start_bff_process(threshold, interval)

    try:
        if not await wait_for_bff_ready():
            return {"error": "BFF未就绪", "label": label}

        await asyncio.sleep(2)

        km_stats = await verify_km_config()
        actual_threshold = km_stats.get('merge_threshold', '?')
        actual_interval = km_stats.get('merge_interval', '?')
        print(f"  [KM配置] threshold={actual_threshold}, interval={actual_interval}s")

        if str(actual_threshold) != str(threshold) or str(actual_interval) != str(interval):
            print(f"  [警告] KM配置不匹配，期望 threshold={threshold}, interval={interval}")

        report = await run_throughput_experiment_a(output_filename=f"{threshold}_{interval}")
        return report

    finally:
        print("  [BFF] 停止BFF服务...")
        bff_process.terminate()
        try:
            bff_process.wait(timeout=10)
        except:
            bff_process.kill()

        print("  [清理] 清理残留容器...")
        stop_and_remove_container("nanobot_conv_")
        stop_and_remove_container("consolidator_")
        time.sleep(2)


def analyze_results(results: list) -> dict:
    """分析实验结果"""
    analysis = {"stage1": [], "stage2": [], "stage3": [], "best": None, "best_sar": 0}

    for r in results:
        if "error" in r:
            continue

        pm_count = r.get("public_memory_count", 0)
        actual_time = r.get("actual_time", TIME_BUDGET)
        sar = pm_count / actual_time if actual_time > 0 else 0

        entry = {
            "label": r.get("label", f"({r.get('merge_threshold', 0)},{r.get('merge_interval', 60)})"),
            "threshold": r.get("merge_threshold", 0),
            "interval": r.get("merge_interval", 60),
            "pm_count": pm_count,
            "sar": sar,
        }

        stage = r.get("stage", 2)
        if stage == 1:
            analysis["stage1"].append(entry)
        elif stage == 2:
            analysis["stage2"].append(entry)
        else:
            analysis["stage3"].append(entry)

        if sar > analysis["best_sar"]:
            analysis["best_sar"] = sar
            analysis["best"] = entry

    return analysis


def generate_report(analysis: dict, results: list) -> str:
    """生成Markdown报告"""
    lines = []
    lines.append("# SAYG-Mem 参数敏感性实验报告\n")
    lines.append(f"**实验时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**实验配置**: {AGENT_COUNT} Agent, {TIME_BUDGET}s 时间预算\n\n")

    stage_names = {1: "激进阈值(5)", 2: "均衡阈值(20)", 3: "保守阈值(50)"}

    for stage_idx in [1, 2, 3]:
        stage_key = f"stage{stage_idx}"
        if analysis[stage_key]:
            fixed_th = 5 if stage_idx == 1 else 20 if stage_idx == 2 else 50
            lines.append(f"## 第{stage_idx}阶段：{stage_names.get(stage_idx, '')}（固定threshold={fixed_th}，变化interval）\n\n")
            lines.append("| 配置 | threshold | interval | PublicMemory | SAR(条/秒) |\n")
            lines.append("|:---|:---|:---|:---|:---|\n")
            for e in analysis[stage_key]:
                lines.append(f"| {e['label']} | {e['threshold']} | {e['interval']}s | {e['pm_count']} | {e['sar']:.4f} |\n")
            lines.append("\n")

    if analysis["best"]:
        best = analysis["best"]
        lines.append("## 结论\n\n")
        lines.append(f"**最佳配置**: merge_threshold={best['threshold']}, merge_interval={best['interval']}s\n")
        lines.append(f"**最佳SAR**: {best['sar']:.4f} 条/秒\n")
        lines.append(f"**PublicMemory产出**: {best['pm_count']} 条\n")

    lines.append("\n## 原始数据\n\n")
    lines.append("```\n")
    for r in results:
        if "error" in r:
            lines.append(f"{r.get('label', '?')}: ERROR - {r['error']}\n")
        else:
            lines.append(f"{r.get('label', '?')}: PM={r.get('public_memory_count', 0)}, SAR={r.get('sar', 0):.4f}\n")
    lines.append("```\n")

    return "".join(lines)


async def main():
    print("\n" + "="*70)
    print("SAYG-Mem 参数敏感性实验")
    print("="*70)
    print(f"实验配置: {len(EXPERIMENT_CONFIGS)} 组")
    print(f"预计时间: ~{len(EXPERIMENT_CONFIGS) * 6} 分钟\n")

    EXPERIMENT_DIR = Path(__file__).parent / "experiment_data" / "threshold_sensitivity"
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for i, config in enumerate(EXPERIMENT_CONFIGS):
        print(f"\n[进度] 第 {i+1}/{len(EXPERIMENT_CONFIGS)} 组: {config['label']}")

        result = await run_single_experiment(
            config["label"],
            config["threshold"],
            config["interval"]
        )

        result["label"] = config["label"]
        result["merge_threshold"] = config["threshold"]
        result["merge_interval"] = config["interval"]
        result["stage"] = config["stage"]

        results.append(result)

        pm = result.get("public_memory_count", "N/A")
        sar = result.get("public_memory_count", 0) / TIME_BUDGET if isinstance(result.get("public_memory_count"), int) else "N/A"
        print(f"\n[结果] {config['label']}: PM={pm}, SAR={sar:.4f}" if isinstance(sar, float) else f"\n[结果] {config['label']}: PM={pm}")

        await asyncio.sleep(5)

    print("\n" + "="*70)
    print("分析结果...")
    print("="*70)

    analysis = analyze_results(results)
    report = generate_report(analysis, results)
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
    asyncio.run(main())