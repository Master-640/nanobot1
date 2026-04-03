#!/bin/bash
# 只运行 MiniMax 和 Kimi 的实验（跳过其他已成功的）

TASKS=("Task1_Sales" "Task2_User" "Task3_Finance" "Task4_Review")

DATA_DIR="/mnt/d/collections2026/phd_application/nanobot1/experiment_docker/shared/data"
OUTPUT_DIR="/mnt/d/collections2026/phd_application/nanobot1/experiment_docker/results/outputs"
IMAGE="nanobot-experiment"

# API Keys
DEEPSEEK_API_KEY="sk-b192d1bf26f740adace7d5f628656921"
DASHSCOPE_API_KEY="sk-91fe1c9c529b46bb88dc200a2e97b2b6"
KIMI_API_KEY="sk-7cCePvSuePzAtih1RK39usAeanWDlrkNR2P8U3oYAcR1CFBH"
MINIMAX_API_KEY="sk-api-C6nEBNXTL060zsjHvdlo522KvNeU7Shk-EKsgvouTgJqjn2Dx0MgMAVQGg9CaYxMOGMaOm_Em-DwFDMtd2zu4EzTTDvmExKUi1Pgc5-vsM3hm1--sv_dKHs"

for TASK in "${TASKS[@]}"; do
    for MODEL in "kimi-k2.5" "MiniMax-M1"; do
        # 容器名称
        CONTAINER_NAME="nanobot_${TASK}_${MODEL}"
        CONTAINER_NAME=$(echo "$CONTAINER_NAME" | tr '/' '_' | tr ':' '_')

        echo "启动: $TASK / $MODEL"

        docker run -d --rm \
            --name "$CONTAINER_NAME" \
            -e SESSION_KEY="$CONTAINER_NAME" \
            -e NANOBOT_MODEL="$MODEL" \
            -e TASK_NAME="$TASK" \
            -e DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" \
            -e DASHSCOPE_API_KEY="$DASHSCOPE_API_KEY" \
            -e KIMI_API_KEY="$KIMI_API_KEY" \
            -e MINIMAX_API_KEY="$MINIMAX_API_KEY" \
            -v "$DATA_DIR:/app/experiment_data:ro" \
            -v "$OUTPUT_DIR:/app/experiment_outputs" \
            "$IMAGE" python container_runner.py

        sleep 1
    done
done

echo ""
echo "已启动所有容器，使用以下命令查看状态:"
echo "  docker ps"
