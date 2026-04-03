FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制整个项目（包括 pyproject.toml）
COPY . /app

# 安装 nanobot 依赖（使用根目录的 pyproject.toml）
# 源码已禁用 vector_memory（见 nanobot/agent/loop.py）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e /app

# 创建必要的目录结构
RUN mkdir -p /app/personal/logs /app/personal/results /root/.nanobot/workspaces /app/experiment_data /app/experiment_outputs

# 设置环境变量支持
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV NANOBOT_WORKSPACE=/root/.nanobot/workspaces

WORKDIR /app/experiment_docker

# 默认运行容器启动脚本
CMD ["python", "container_runner.py"]
