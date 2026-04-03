"""
Docker 容器内运行的脚本
负责：
1. 运行 nanobot onboard
2. 生成 config.json
3. 启动 nanobot agent
4. 发送任务消息
5. 监控完成情况
6. 保存结果
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ_UTC8 = timezone(timedelta(hours=8))


def log(message: str):
    """打印带时间戳的日志"""
    timestamp = datetime.now(TZ_UTC8).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def get_env_with_fallback(key: str, fallback: str = "") -> str:
    """获取环境变量（支持从文件或环境变量读取）"""
    # 优先从环境变量读取
    value = os.environ.get(key)
    if value:
        return value
    #  fallback 到文件
    if fallback:
        return fallback
    raise ValueError(f"Environment variable '{key}' is required but not set")


def run_onboard() -> bool:
    """运行 nanobot onboard"""
    log("Running nanobot onboard...")
    try:
        # 运行 onboard，使用非交互模式
        result = subprocess.run(
            ["nanobot", "onboard"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        log(f"Onboard output: {result.stdout[:200]}")
        return True
    except subprocess.TimeoutExpired:
        log("❌ Onboard timeout")
        return False
    except Exception as e:
        log(f"❌ Onboard failed: {e}")
        return False


def generate_config_json(model: str, api_key: str, provider: str = "dashscope") -> bool:
    """生成 ~/.nanobot/config.json"""
    log(f"Generating config.json for model={model}, provider={provider}")

    api_model_map = {
        "kimi-k2.5": "moonshot-v1-8k",
        "MiniMax-M1": "MiniMax-M1",
        "deepseek-reasoner": "deepseek-reasoner",
    }
    api_model = api_model_map.get(model, model)

    try:
        config_dir = Path.home() / ".nanobot"
        config_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "providers": {
                provider.lower(): {
                    "apiKey": api_key
                }
            },
            "agents": {
                "defaults": {
                    "model": api_model,
                    "provider": provider.lower()
                }
            }
        }

        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        log(f"✅ Config saved to {config_file}")
        log(f"📄 Config content: {json.dumps(config, indent=2)}")
        return True
        
    except Exception as e:
        log(f"❌ Failed to generate config: {e}")
        return False


def get_task_content(task_name: str) -> tuple[str, str]:
    """获取任务内容和数据文件路径"""
    data_dir = Path("/app/experiment_data")
    
    task_map = {
        "Task1_Sales": ("sales.csv", "销售数据分析"),
        "Task2_User": ("user_behavior.csv", "用户行为分析"),
        "Task3_Finance": ("financial.csv", "财务数据清洗"),
        "Task4_Review": ("reviews.csv", "评论情感分析"),
    }
    
    if task_name not in task_map:
        raise ValueError(f"Unknown task: {task_name}")
    
    file_name, task_desc = task_map[task_name]
    csv_file = data_dir / file_name
    
    if not csv_file.exists():
        raise FileNotFoundError(f"Data file not found: {csv_file}")
    
    content = csv_file.read_text(encoding="utf-8")
    
    # 定义任务指令
    task_instructions = {
        "Task1_Sales": """请分析这份销售数据，包括：
1. 计算总销售额和总销售量
2. 按产品类别分析销售表现
3. 识别销售趋势（按月）
4. 比较不同地区的销售情况
5. 分析企业客户和个人客户的购买行为差异

请提供详细的分析报告和关键洞察。""",
        
        "Task2_User": """请分析这份用户行为数据，包括：
1. 计算平均停留时长和点击次数
2. 分析不同页面类型的用户参与度
3. 识别用户活跃时段（上午/下午/晚上）
4. 比较不同设备类型的用户行为
5. 找出用户流失的关键页面

请提供详细的分析报告和优化建议。""",
        
        "Task3_Finance": """请清洗这份财务数据，包括：
1. 填补缺失的金额数据（使用合理方法）
2. 检测并处理异常值（如负数收入）
3. 标准化交易状态（完成/处理中）
4. 按类别和账户汇总收支情况
5. 计算每月净收入

请提供清洗后的数据和分析结果。""",
        
        "Task4_Review": """请分析这份产品评论数据，包括：
1. 计算平均评分
2. 分析评论的情感倾向（正面/负面/中性）
3. 提取关键词和常见主题
4. 识别用户最满意和最不满意的方面
5. 按评分分组分析评论特征

请提供详细的情感分析报告。""",
    }
    
    instruction = task_instructions.get(task_name, "请分析这份数据。")

    task_message = f"""任务：{task_desc}

数据文件：/app/experiment_data/{file_name}

请使用 ReadFile 工具读取数据文件 /app/experiment_data/{file_name}，然后按照以下要求进行分析：

{instruction}

请直接输出分析报告。"""

    return task_message, str(csv_file)


def start_agent_background(task_message: str) -> subprocess.Popen:
    """后台启动 nanobot agent 并直接发送任务"""
    log("Starting nanobot agent with task...")

    env = os.environ.copy()
    env["NANOBOT_WORKSPACE"] = "/root/.nanobot/workspaces"

    process = subprocess.Popen(
        ["nanobot", "agent", "--message", task_message],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    log(f"✅ Agent started with PID {process.pid}")
    return process


def send_task_to_agent(process: subprocess.Popen, task_message: str) -> bool:
    """发送任务消息给 agent（已通过 --message 参数发送）"""
    log("Task was already sent via --message parameter")
    return True


def monitor_agent_completion(
    process: subprocess.Popen,
    token_usage_file: Path,
    output_dir: Path,
    max_runtime: int = 600,
) -> tuple[bool, str]:
    """
    监控 agent 完成情况

    策略：
    1. 等待进程自然结束（agent 处理完任务后会自动退出）
    2. 如果超过 max_runtime 秒则强制退出
    3. 实时输出 agent 日志并统计 token
    """
    log(f"Monitoring agent (max_runtime={max_runtime}s)...")

    output_dir.mkdir(parents=True, exist_ok=True)
    last_mtime = 0
    output_lines = []
    last_token_count = 0
    start_time = time.time()

    while True:
        # 读取 agent 输出
        try:
            line = process.stdout.readline()
            if line:
                output_lines.append(line)
                print(line, end="", flush=True)
        except:
            pass

        # 检查 token_usage.txt 更新并统计，实时保存
        if token_usage_file.exists():
            try:
                current_mtime = token_usage_file.stat().st_mtime
                if current_mtime > last_mtime:
                    last_mtime = current_mtime
                    content = token_usage_file.read_text(encoding="utf-8")
                    current_token_count = len([l for l in content.split("\n") if l.strip().startswith("{")])
                    (output_dir / "token_usage.txt").write_text(content, encoding="utf-8")
                    if current_token_count > last_token_count:
                        last_token_count = current_token_count
                        elapsed = time.time() - start_time
                        log(f"📊 Tokens: {last_token_count} requests, {elapsed:.0f}s elapsed")
            except Exception:
                pass

        # 检查 api_responses.jsonl 更新并保存
        api_response_file = token_usage_file.parent / "api_responses.jsonl"
        if api_response_file.exists():
            try:
                content = api_response_file.read_text(encoding="utf-8")
                if content:
                    (output_dir / "api_responses.jsonl").write_text(content, encoding="utf-8")
            except Exception:
                pass

        # 检查进程是否结束（主要退出条件）
        if process.poll() is not None:
            # 进程已结束，但继续读取剩余输出直到读完
            remaining = []
            try:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    remaining.append(line)
                    print(line, end="", flush=True)
            except:
                pass

            if remaining:
                output_lines.extend(remaining)
                log(f"📝 Collected {len(remaining)} remaining output lines")

            elapsed = time.time() - start_time
            log(f"✅ Agent completed naturally in {elapsed:.1f}s")
            return True, "completed", output_lines

        # 最大运行时间（硬限制）
        elapsed = time.time() - start_time
        if elapsed > max_runtime:
            log(f"⏰ Max runtime reached ({max_runtime}s), terminating...")
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
            return False, "max_runtime", output_lines

        time.sleep(1)


def parse_token_usage(token_file: Path) -> dict:
    """解析 token_usage.txt 文件，返回统计信息"""
    if not token_file.exists():
        return {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "request_count": 0,
            "rounds": []
        }

    content = token_file.read_text(encoding="utf-8")
    total_tokens = 0
    prompt_tokens = 0
    completion_tokens = 0
    request_count = 0
    rounds = []

    for line in content.strip().split("\n"):
        line = line.strip()
        if not line or "prompt=" not in line:
            continue

        import re
        prompt_match = re.search(r"prompt=(\d+)", line)
        comp_match = re.search(r"completion=(\d+)", line)
        total_match = re.search(r"total=(\d+)", line)

        if prompt_match and comp_match:
            pt = int(prompt_match.group(1))
            ct = int(comp_match.group(1))
            tt = int(total_match.group(1)) if total_match else pt + ct
            prompt_tokens += pt
            completion_tokens += ct
            total_tokens += tt
            request_count += 1
            rounds.append({
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "total_tokens": tt
            })

    return {
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "request_count": request_count,
        "rounds": rounds
    }


def save_results(
    session_key: str,
    model: str,
    task_name: str,
    success: bool,
    reason: str,
    output_lines: list[str],
    token_usage_file: Path,
    runtime_seconds: float,
) -> None:
    """保存结果到文件"""
    log(f"Saving results for {session_key}...")

    output_dir = Path("/app/experiment_outputs") / task_name / model.replace("-", "_")
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = output_dir / "agent.log"
    log_file.write_text("".join(output_lines), encoding="utf-8")

    if token_usage_file.exists():
        token_content = token_usage_file.read_text(encoding="utf-8")
        (output_dir / "token_usage.txt").write_text(token_content, encoding="utf-8")

    api_response_file = token_usage_file.parent / "api_responses.jsonl"
    if api_response_file.exists():
        api_content = api_response_file.read_text(encoding="utf-8")
        if api_content:
            (output_dir / "api_responses.jsonl").write_text(api_content, encoding="utf-8")

    token_stats = parse_token_usage(token_usage_file)

    status_file = output_dir / "status.json"
    status = {
        "session_key": session_key,
        "model": model,
        "task_name": task_name,
        "success": success,
        "reason": reason,
        "timestamp": datetime.now(TZ_UTC8).isoformat(),
        "runtime_seconds": runtime_seconds,
        "total_tokens": token_stats["total_tokens"],
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "request_count": token_stats["request_count"],
    }
    status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")

    log(f"✅ Results saved to {output_dir}")
    log(f"📊 Tokens: {token_stats['total_tokens']} (prompt: {token_stats['prompt_tokens']}, completion: {token_stats['completion_tokens']})")
    log(f"⏱️  Runtime: {runtime_seconds:.1f}s")


def main():
    """主函数"""
    log("="*80)
    log("Nanobot Experiment Container Runner")
    log("="*80)

    start_time = time.time()

    # 清理旧的 workspace，确保干净的启动环境
    workspace_path = Path("/root/.nanobot/workspaces")
    if workspace_path.exists():
        import shutil
        shutil.rmtree(workspace_path, ignore_errors=True)
        log("✅ Cleaned old workspace")

    # 获取环境变量
    session_key = get_env_with_fallback("SESSION_KEY")
    model = get_env_with_fallback("NANOBOT_MODEL")
    task_name = get_env_with_fallback("TASK_NAME")
    
    # 根据模型类型读取对应的 API key
    api_key = ""
    if "qwen" in model.lower():
        api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    elif "deepseek" in model.lower():
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    elif "kimi" in model.lower():
        api_key = os.environ.get("KIMI_API_KEY", "")
    elif "minimax" in model.lower():
        api_key = os.environ.get("MINIMAX_API_KEY", "")
    
    # 如果 API key 为空，尝试从 config.json 读取
    if not api_key:
        log("Warning: API key not set in environment, will use config.json")
    
    log(f"Session: {session_key}")
    log(f"Model: {model}")
    log(f"Task: {task_name}")
    log(f"API Key: {'✅ Set' if api_key else '❌ Not set'}")
    
    # 1. 运行 onboard
    if not run_onboard():
        log("❌ Onboard failed, exiting")
        sys.exit(1)
    
    # 2. 生成 config.json
    # provider name 必须匹配 registry.py 里的 ProviderSpec.name
    # "moonshot" provider 的 keywords 是 ("moonshot", "kimi")，所以 kimi 模型会匹配到 moonshot
    provider = "dashscope" if "qwen" in model.lower() else \
               "deepseek" if "deepseek" in model.lower() else \
               "moonshot" if "kimi" in model.lower() else \
               "minimax" if "minimax" in model.lower() else "dashscope"

    log(f"Provider detected: {provider}")
    log(f"API Key length: {len(api_key) if api_key else 0}")

    if not api_key:
        log("❌ FATAL: API key is empty! Cannot generate config.")
        log(f"Environment KIMI_API_KEY = '{os.environ.get('KIMI_API_KEY', 'NOT_SET')}'")
        sys.exit(1)

    if not generate_config_json(model, api_key, provider):
        log("❌ Config generation failed, exiting")
        sys.exit(1)
    
    # 3. 获取任务内容
    try:
        task_message, data_file = get_task_content(task_name)
        log(f"✅ Task loaded: {task_name}")
    except Exception as e:
        log(f"❌ Failed to load task: {e}")
        sys.exit(1)
    
    # 4. 启动 agent（直接传入任务消息）
    agent_process = start_agent_background(task_message)

    # 5. 监控完成
    token_usage_file = Path("/root/.nanobot/workspaces/personal/token_usage.txt")
    output_dir = Path("/app/experiment_outputs") / task_name / model.replace("-", "_")
    success, reason, output_lines = monitor_agent_completion(
        agent_process,
        token_usage_file,
        output_dir,
        max_runtime=600,
    )

    # 6. 保存结果
    runtime_seconds = time.time() - start_time
    save_results(
        session_key=session_key,
        model=model,
        task_name=task_name,
        success=success,
        reason=reason,
        output_lines=output_lines,
        token_usage_file=token_usage_file,
        runtime_seconds=runtime_seconds,
    )

    # 7. 退出
    if success:
        log("✅ Experiment completed successfully")
        sys.exit(0)
    else:
        log(f"⚠️ Experiment ended: {reason}")
        agent_process.kill()
        sys.exit(1)


if __name__ == "__main__":
    main()
