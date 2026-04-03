#!/bin/bash
# 运行 Task2, Task3, Task4 的 deepseek-reasoner 实验

TASKS=("Task2_User" "Task3_Finance" "Task4_Review")
MODEL="deepseek-reasoner"
IMAGE="nanobot-experiment"

DATA_DIR="/mnt/d/collections2026/phd_application/nanobot1/experiment_docker/shared/data"
OUTPUT_DIR="/mnt/d/collections2026/phd_application/nanobot1/experiment_docker/results/outputs"

DEEPSEEK_API_KEY="sk-b192d1bf26f740adace7d5f628656921"
DASHSCOPE_API_KEY="sk-91fe1c9c529b46bb88dc200a2e97b2b6"
KIMI_API_KEY="sk-7cCePvSuePzAtih1RK39usAeanWDlrkNR2P8U3oYAcR1CFBH"
MINIMAX_API_KEY="sk-api-C6nEBNXTL060zsjHvdlo522KvNeU7Shk-EKsgvouTgJqjn2Dx0MgMAVQGg9CaYxMOGMaOm_Em-DwFDMtd2zu4EzTTDvmExKUi1Pgc5-vsM3hm1--sv_dKHs"

for TASK in "${TASKS[@]}"; do
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

echo ""
echo "已启动 ${#TASKS[@]} 个容器，查看日志:"
echo "  docker logs -f nanobot_Task2_User_deepseek-reasoner"
echo "  docker logs -f nanobot_Task3_Finance_deepseek-reasoner"
echo "  docker logs -f nanobot_Task4_Review_deepseek-reasoner"
