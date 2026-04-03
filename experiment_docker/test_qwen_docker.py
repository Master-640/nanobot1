#!/usr/bin/env python3
"""测试 Qwen3 Max prompt_token_details - Docker内测试版"""

import os
import requests
import json

DASHSCOPE_KEY = "sk-91fe1c9c529b46bb88dc200a2e97b2b6"

url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DASHSCOPE_KEY}"
}

data = {
    "model": "qwen3-max-2026-01-23",
    "messages": [{"role": "user", "content": "你好，请简单介绍一下自己"}]
}

print("=" * 60)
print("测试 Qwen3 Max prompt_token_details (Docker内)")
print("=" * 60)

try:
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

    if "usage" in result:
        usage = result["usage"]
        print("\n--- Usage Details ---")
        print(f"prompt_tokens: {usage.get('prompt_tokens')}")
        print(f"completion_tokens: {usage.get('completion_tokens')}")
        print(f"total_tokens: {usage.get('total_tokens')}")
        print(f"prompt_tokens_details: {usage.get('prompt_tokens_details')}")
        if usage.get('prompt_tokens_details'):
            print(f"  - cached_tokens: {usage['prompt_tokens_details'].get('cached_tokens')}")
            print("  ✅ Cache details available!")
        else:
            print("  ❌ prompt_tokens_details is null")
except Exception as e:
    print(f"❌ 请求失败: {e}")
