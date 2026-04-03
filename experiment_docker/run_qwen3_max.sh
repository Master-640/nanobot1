#!/bin/bash
TASKS=("Task1_Sales" "Task2_User" "Task3_Finance" "Task4_Review")
MODEL="qwen3-max-2026-01-23"
IMAGE="nanobot-experiment"

DATA_DIR="/mnt/d/collections2026/phd_application/nanobot1/experiment_docker/shared/data"
OUTPUT_DIR="/mnt/d/collections2026/phd_application/nanobot1/experiment_docker/results/outputs"

DASHSCOPE_API_KEY="sk-91fe1c9c529b46bb88dc200a2e97b2b6"

for TASK in "${TASKS[@]}"; do
    CONTAINER_NAME="nanobot_${TASK}_${MODEL}"
    CONTAINER_NAME=$(echo "$CONTAINER_NAME" | tr '/' '_' | tr ':' '_')

    echo "启动: $TASK / $MODEL"

    docker run -d --rm \
        --name "$CONTAINER_NAME" \
        -e SESSION_KEY="$CONTAINER_NAME" \
        -e NANOBOT_MODEL="$MODEL" \
        -e TASK_NAME="$TASK" \
        -e DASHSCOPE_API_KEY="$DASHSCOPE_API_KEY" \
        -v "$DATA_DIR:/app/experiment_data:ro" \
        -v "$OUTPUT_DIR:/app/experiment_outputs" \
        "$IMAGE" python container_runner.py

    sleep 1
done
