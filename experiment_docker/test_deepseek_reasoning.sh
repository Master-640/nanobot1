#!/bin/bash
# 单个测试 DeepSeek Reasoning 容器

docker run -d --rm \
  --name nanobot_deepseek_reasoning_test \
  -e SESSION_KEY=deepseek_reasoning_test \
  -e NANOBOT_MODEL=deepseek-reasoner \
  -e TASK_NAME=Task1_Sales \
  -e KIMI_API_KEY="sk-7cCePvSuePzAtih1RK39usAeanWDlrkNR2P8U3oYAcR1CFBH" \
  -e DASHSCOPE_API_KEY="sk-91fe1c9c529b46bb88dc200a2e97b2b6" \
  -e DEEPSEEK_API_KEY="sk-b192d1bf26f740adace7d5f628656921" \
  -e MINIMAX_API_KEY="sk-api-C6nEBNXTL060zsjHvdlo522KvNeU7Shk-EKsgvouTgJqjn2Dx0MgMAVQGg9CaYxMOGMaOm_Em-DwFDMtd2zu4EzTTDvmExKUi1Pgc5-vsM3hm1--sv_dKHs" \
  -v "/mnt/d/collections2026/phd_application/nanobot1/experiment_docker/shared/data:/app/experiment_data:ro" \
  -v "/mnt/d/collections2026/phd_application/nanobot1/experiment_docker/results/outputs:/app/experiment_outputs" \
  nanobot-experiment python container_runner.py

echo "Container started. Check with:"
echo "  docker logs -f nanobot_deepseek_reasoning_test"
