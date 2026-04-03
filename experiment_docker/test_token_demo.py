#!/usr/bin/env python3
"""验证 _write_usage_to_file 功能的测试脚本"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# 模拟 nanobot 的目录结构
# 假设我们在 /app/nanobot/providers/openai_compat_provider.py

# 设置环境变量模拟 Docker 环境
os.environ["NANOBOT_WORKSPACE"] = "/root/.nanobot/workspaces"

# 模拟 _write_usage_to_file 函数
def _write_usage_to_file(usage: dict[str, int]) -> None:
    """Write token usage to token_usage.txt file (per-session JSON format)."""
    try:
        workspace_env = os.environ.get("NANOBOT_WORKSPACE")
        if workspace_env:
            personal_dir = Path(workspace_env) / "personal"
        else:
            # fallback
            personal_dir = Path.home() / ".nanobot" / "personal"
        personal_dir.mkdir(parents=True, exist_ok=True)

        # 模拟 session_key 为空的情况
        session_key = None
        if session_key:
            log_dir = personal_dir / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"session_{session_key}_token_usage.txt"
        else:
            log_file = personal_dir / "token_usage.txt"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = usage.get("prompt_tokens", 0)
        completion = usage.get("completion_tokens", 0)
        total = usage.get("total_tokens", prompt + completion)

        record = {
            "timestamp": timestamp,
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": total,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"✅ 写入成功: {log_file}")
        print(f"   内容: {record}")
    except Exception as e:
        print(f"❌ 写入失败: {e}")


def _read_usage_file(log_file: Path) -> dict:
    """读取并解析 token_usage.txt"""
    if not log_file.exists():
        return {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "request_count": 0, "rounds": []}

    content = log_file.read_text(encoding="utf-8")
    total_tokens = 0
    prompt_tokens = 0
    completion_tokens = 0
    request_count = 0
    rounds = []

    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            pt = record.get("prompt_tokens", 0)
            ct = record.get("completion_tokens", 0)
            tt = record.get("total_tokens", pt + ct)
            prompt_tokens += pt
            completion_tokens += ct
            total_tokens += tt
            request_count += 1
            rounds.append({"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt})
        except json.JSONDecodeError:
            continue

    return {
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "request_count": request_count,
        "rounds": rounds
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Token Usage Write Demo")
    print("=" * 60)
    print()

    # 模拟 DeepSeek API 返回的 usage 格式（OpenAI 兼容）
    # 非流式响应
    test_usages = [
        {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500},
        {"prompt_tokens": 2000, "completion_tokens": 800, "total_tokens": 2800},
        {"prompt_tokens": 1500, "completion_tokens": 600, "total_tokens": 2100},
    ]

    for i, usage in enumerate(test_usages, 1):
        print(f"调用 {i}:")
        _write_usage_to_file(usage)
        print()

    # 读取验证
    workspace = Path(os.environ["NANOBOT_WORKSPACE"])
    token_file = workspace / "personal" / "token_usage.txt"

    print("=" * 60)
    print("读取验证:")
    print(f"文件位置: {token_file}")
    print()

    stats = _read_usage_file(token_file)
    print(f"总 prompt_tokens: {stats['prompt_tokens']}")
    print(f"总 completion_tokens: {stats['completion_tokens']}")
    print(f"总 total_tokens: {stats['total_tokens']}")
    print(f"请求次数: {stats['request_count']}")
    print()
    print("逐条记录:")
    for i, r in enumerate(stats['rounds'], 1):
        print(f"  {i}. prompt={r['prompt_tokens']}, completion={r['completion_tokens']}, total={r['total_tokens']}")