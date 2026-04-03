#!/usr/bin/env python3
"""测试 Qwen3 Max 原生端点 - 检查 prompt_tokens_details"""

import os
import requests
import json

DASHSCOPE_KEY = "sk-91fe1c9c529b46bb88dc200a2e97b2b6"

print("=" * 60)
print("测试 Qwen3 Max 原生端点 prompt_tokens_details")
print("=" * 60)

# 1. Native endpoint
native_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DASHSCOPE_KEY}"
}

data = {
    "model": "qwen3-max-2026-01-23",
    "input": {
        "messages": [
            {"role": "user", "content": "你好，请简单介绍一下自己"}
        ]
    },
    "parameters": {
        "result_format": "message"
    }
}

print("\n📡 发送请求到原生端点...")
print(f"URL: {native_url}")

try:
    resp = requests.post(native_url, headers=headers, json=data, timeout=30)
    print(f"Status: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print("\n📦 完整响应:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 检查 usage
        if "output" in result and "usage" in result["output"]:
            usage = result["output"]["usage"]
            print("\n--- Usage Details ---")
            print(f"prompt_tokens: {usage.get('prompt_tokens')}")
            print(f"completion_tokens: {usage.get('completion_tokens')}")
            print(f"total_tokens: {usage.get('total_tokens')}")
            if "prompt_tokens_details" in usage:
                print(f"prompt_tokens_details: {usage.get('prompt_tokens_details')}")
                if usage.get('prompt_tokens_details') and 'cached_tokens' in usage['prompt_tokens_details']:
                    print("  ✅ Cache details available!")
                    print(f"  - cached_tokens: {usage['prompt_tokens_details'].get('cached_tokens')}")
                else:
                    print("  ❌ prompt_tokens_details is null or no cached_tokens")
            else:
                print("  ⚠️ No prompt_tokens_details field in usage")
        else:
            print("  ⚠️ No usage field in output")
    else:
        print(f"Error: {resp.text}")

except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n" + "=" * 60)
print("对比: Compatible Mode 端点")
print("=" * 60)

# 2. Compatible endpoint (for comparison)
compat_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
compat_data = {
    "model": "qwen3-max-2026-01-23",
    "messages": [{"role": "user", "content": "你好，请简单介绍一下自己"}]
}

print(f"\n📡 发送请求到 Compatible 端点...")
print(f"URL: {compat_url}")

try:
    resp = requests.post(compat_url, headers=headers, json=compat_data, timeout=30)
    print(f"Status: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print("\n📦 完整响应:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if "usage" in result:
            usage = result["usage"]
            print("\n--- Usage Details ---")
            print(f"prompt_tokens: {usage.get('prompt_tokens')}")
            print(f"completion_tokens: {usage.get('completion_tokens')}")
            print(f"total_tokens: {usage.get('total_tokens')}")
            print(f"prompt_tokens_details: {usage.get('prompt_tokens_details')}")
            if usage.get('prompt_tokens_details'):
                print("  ✅ Cache details available!")
            else:
                print("  ❌ prompt_tokens_details is null")
    else:
        print(f"Error: {resp.text}")

except Exception as e:
    print(f"❌ 请求失败: {e}")
