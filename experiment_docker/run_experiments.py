#!/usr/bin/env python3
"""
宿主机运行的实验调度脚本
负责：
1. 构建 Docker 镜像
2. 创建 16 个容器（4 任务 × 4 模型）
3. 并发控制（最多 4 个同时运行）
4. 等待所有容器完成
5. 收集结果并生成报告
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


# 实验配置
TASKS = [
    ("Task1_Sales", "sales.csv"),
    ("Task2_User", "user_behavior.csv"),
    ("Task3_Finance", "financial.csv"),
    ("Task4_Review", "reviews.csv"),
]

MODELS = [
    ("deepseek-chat", "deepseek", "DEEPSEEK_API_KEY"),
    ("qwen3-max", "dashscope", "DASHSCOPE_API_KEY"),
    ("kimi-k2.5", "moonshot", "KIMI_API_KEY"),
    ("MiniMax-M1", "minimax", "MINIMAX_API_KEY"),
]

MAX_CONCURRENT = 4
TIMEOUT_SECONDS = 1800  # 30 分钟超时

IMAGE_NAME = "nanobot-experiment"
DATA_DIR = Path(__file__).parent / "shared" / "data"
OUTPUT_DIR = Path(__file__).parent / "results" / "outputs"


def log(message: str):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def build_docker_image() -> bool:
    """构建 Docker 镜像"""
    log(f"Building Docker image: {IMAGE_NAME}")
    
    dockerfile = Path(__file__).parent / "Dockerfile"
    context = Path(__file__).parent.parent
    
    try:
        subprocess.run([
            "docker", "build",
            "-t", IMAGE_NAME,
            "-f", str(dockerfile),
            str(context),
        ], check=True)
        log("✅ Image built successfully")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Image build failed: {e}")
        return False


def run_single_experiment(
    task_name: str,
    model: str,
    provider: str,
    api_key_env: str,
) -> dict:
    """运行单个实验（一个容器）"""
    session_key = f"{task_name}_{model.replace('-', '_')}"
    container_name = f"nanobot_{session_key}"
    
    log(f"🚀 Starting container: {container_name}")
    
    # 获取 API key
    api_key_value = ""
    try:
        # 从环境变量读取
        import os
        api_key_value = os.environ.get(api_key_env, "")
    except:
        pass
    
    # 准备 docker run 命令
    cmd = [
        "docker", "run",
        "--name", container_name,
        "--rm",  # 自动删除容器
        "-e", f"SESSION_KEY={session_key}",
        "-e", f"NANOBOT_MODEL={model}",
        "-e", f"TASK_NAME={task_name}",
        "-e", f"{api_key_env}={api_key_value}",
        "-v", f"{DATA_DIR}:/app/experiment_data:ro",  # 只读挂载数据
        "-v", f"{OUTPUT_DIR}:/app/experiment_outputs",
        IMAGE_NAME,
    ]
    
    start_time = time.time()
    
    try:
        # 运行容器
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        
        execution_time = time.time() - start_time
        success = result.returncode == 0
        
        log(f"{'✅' if success else '❌'} Container {container_name} finished in {execution_time:.1f}s")
        
        return {
            "session_key": session_key,
            "task_name": task_name,
            "model": model,
            "success": success,
            "execution_time": execution_time,
            "exit_code": result.returncode,
            "stdout": result.stdout if result.stdout else "",
            "stderr": result.stderr if result.stderr else "",
        }
        
    except subprocess.TimeoutExpired:
        # 超时，强制停止
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        log(f"⏰ Container {container_name} timeout after {TIMEOUT_SECONDS}s")
        
        return {
            "session_key": session_key,
            "task_name": task_name,
            "model": model,
            "success": False,
            "execution_time": TIMEOUT_SECONDS,
            "exit_code": -1,
            "error": "timeout",
        }


def run_all_experiments():
    """运行所有实验（并发控制）"""
    log("="*80)
    log("LLM Backend Comparison Experiments")
    log("="*80)
    log(f"Tasks: {len(TASKS)} ({', '.join([t[0] for t in TASKS])})")
    log(f"Models: {len(MODELS)} ({', '.join([m[0] for m in MODELS])})")
    log(f"Total experiments: {len(TASKS) * len(MODELS)}")
    log(f"Max concurrent: {MAX_CONCURRENT}")
    log(f"Timeout: {TIMEOUT_SECONDS}s")
    log("="*80)
    
    # 检查镜像是否存在（跳过构建）
    import subprocess
    result = subprocess.run(["docker", "images", "-q", "nanobot-experiment"], capture_output=True, text=True)
    if not result.stdout.strip():
        log("⚠️  Image nanobot-experiment not found, trying to build...")
        if not build_docker_image():
            log("❌ Failed to build image, exiting")
            sys.exit(1)
    else:
        log("✅ Using existing image: nanobot-experiment")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 准备所有实验
    experiments = []
    for task_name, _ in TASKS:
        for model, provider, api_key_env in MODELS:
            experiments.append((task_name, model, provider, api_key_env))
    
    # 并发执行
    results = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        futures = {
            executor.submit(run_single_experiment, *exp): exp
            for exp in experiments
        }
        
        for future in as_completed(futures):
            task_name, model, _, _ = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                log(f"❌ Experiment {task_name}_{model} failed: {e}")
                results.append({
                    "task_name": task_name,
                    "model": model,
                    "success": False,
                    "error": str(e),
                })
    
    # 保存结果
    save_results(results)
    
    # 生成报告
    generate_report(results)
    
    return results


def save_results(results: list[dict]):
    """保存结果到 JSON 文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = Path(__file__).parent / "results" / f"container_results_{timestamp}.json"
    
    # 保存完整结果
    result_file.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "successful": sum(1 for r in results if r.get("success", False)),
        "results": results,
    }, indent=2, ensure_ascii=False))
    
    log(f"✅ Results saved to {result_file}")


def generate_report(results: list[dict]):
    """生成简单的文本报告"""
    log("\n" + "="*80)
    log("Experiment Report")
    log("="*80)
    
    # 按模型分组
    model_groups = {}
    for r in results:
        model = r.get("model", "unknown")
        model_groups.setdefault(model, []).append(r)
    
    for model, model_results in model_groups.items():
        success_count = sum(1 for r in model_results if r.get("success", False))
        total_time = sum(r.get("execution_time", 0) for r in model_results if r.get("success", False))
        avg_time = total_time / len(model_results) if model_results else 0
        
        log(f"\n{model}:")
        log(f"  Success: {success_count}/{len(model_results)}")
        log(f"  Avg Time: {avg_time:.1f}s")
        
        for r in model_results:
            status = "✅" if r.get("success", False) else "❌"
            log(f"  {status} {r.get('task_name', 'unknown')}: {r.get('execution_time', 0):.1f}s")
    
    log("\n" + "="*80)


if __name__ == "__main__":
    run_all_experiments()
