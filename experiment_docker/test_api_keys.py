#!/usr/bin/env python3
"""验证 Kimi 和 MiniMax API Key 是否有效"""

import requests
import json

KIMI_KEY = "sk-7cCePvSuePzAtih1RK39usAeanWDlrkNR2P8U3oYAcR1CFBH"
MINIMAX_KEY = "sk-api-C6nEBNXTL060zsjHvdlo522KvNeU7Shk-EKsgvouTgJqjn2Dx0MgMAVQGg9CaYxMOGMaOm_Em-DwFDMtd2zu4EzTTDvmExKUi1Pgc5-vsM3hm1--sv_dKHs"

def test_kimi():
    print("=" * 60)
    print("测试 Kimi API")
    print("=" * 60)
    url = "https://api.moonshot.cn/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KIMI_KEY}"
    }
    data = {
        "model": "moonshot-v1-8k",
        "messages": [{"role": "user", "content": "你好"}]
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        if resp.status_code == 200:
            print("✅ Kimi API Key 有效!")
        else:
            print("❌ Kimi API Key 无效")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_minimax():
    print("\n" + "=" * 60)
    print("测试 MiniMax API")
    print("=" * 60)
    url = "https://api.minimaxi.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINIMAX_KEY}"
    }
    data = {
        "model": "MiniMax-M1",
        "messages": [{"role": "user", "content": "你好"}]
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        if resp.status_code == 200:
            print("✅ MiniMax API Key 有效!")
        else:
            print("❌ MiniMax API Key 无效")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_kimi()
    test_minimax()
