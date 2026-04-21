# SAYG-Mem 实验复现指南

## 步骤0：准备 Python 虚拟环境

本项目依赖 Python 3.10+ 及若干第三方库。为隔离环境、确保可复现性，请先创建并激活虚拟环境。

```bash
# 进入项目根目录
cd d:/collections2026/phd_application/nanobot1/milestone2

# 创建虚拟环境（首次运行）
python -m venv shared/venv

# 激活虚拟环境（每次新终端会话都需要执行）
# Linux / WSL:
source shared/venv/bin/activate
# Windows PowerShell:
.\shared\venv\Scripts\activate

# 安装项目依赖
pip install --upgrade pip
pip install httpx aiohttp aiofiles jieba fastapi uvicorn pydantic
```

验证环境：

```bash
python -c "import httpx, jieba; print('环境就绪')"
```

> 注意：后续所有 Python 脚本均需在已激活的虚拟环境中执行。

## 步骤1：重新构建 Agent 镜像

```bash
DOCKER_BUILDKIT=1 docker build -f shared/Dockerfile.agent -t nanobot-agent:latest .
DOCKER_BUILDKIT=1 docker build -f shared/Dockerfile.bff -t nanobot-bff:latest .
```

## 步骤2：启动 BFF 服务（终端 1）

```bash
cd d:/collections2026/phd_application/nanobot1/milestone2
./run_km_system.sh
```

## 步骤3：运行实验脚本（终端 2）

```bash
cd d:/collections2026/phd_application/nanobot1/milestone2
source shared/venv/bin/activate

# 吞吐量对比实验（核心实验）
python run_throughput_comparison.py

# 或单独运行 A 组吞吐量测试（SAYG-Mem）
python learn_throughput_fixed_time_a.py

# 或单独运行 B 组测试（Baseline）
python learn_throughput_fixed_time_b.py

# 扩展性测试（10/20/40 Agent）
python run_scalability_test.py
```

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     BFF (FastAPI)                            │
│              bff/bff_service.py                              │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP (httpx)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Docker Daemon                              │
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │ Container 1 │   │ Container 2 │   │ Container N │      │
│  │ nanobot     │   │ nanobot     │   │ nanobot     │      │
│  │ agent       │   │ agent       │   │ agent       │      │
│  │ :8080       │   │ :8080       │   │ :8080       │      │
│  └─────────────┘   └─────────────┘   └─────────────┘      │
│         ▲               ▲                   ▲                │
└─────────┼───────────────┼───────────────────┼──────────────┘
          │               │                   │
          ▼               ▼                   ▼
    ┌─────────┐     ┌─────────┐         ┌─────────┐
    │ Volume1 │     │ Volume2 │         │ VolumeN │
    │ (COW)   │     │ (COW)   │         │ (COW)   │
    └─────────┘     └─────────┘         └─────────┘
```

## 目录结构

```
milestone2/
├── nanobot_agent/
│   ├── __init__.py
│   └── agent_server.py      # 容器内 HTTP 服务
├── bff/
│   ├── __init__.py
│   ├── bff_service.py       # BFF FastAPI 服务
│   └── container_orchestrator.py  # Docker 容器管理
└── shared/
    ├── __init__.py
    ├── config.py            # 配置
    ├── Dockerfile.agent     # Agent 容器镜像
    ├── Dockerfile.bff       # BFF 容器镜像
    └── docker-compose.yml   # 编排配置
```

## 核心组件

### 1. nanobot_agent/agent_server.py
容器内运行的 HTTP API 服务，提供：
- `POST /chat` - 发送消息给 agent
- `GET /trajectory` - 获取轨迹数据
- `GET /history` - 获取对话历史
- `GET /health` - 健康检查

### 2. bff/container_orchestrator.py
Docker 容器编排器，负责：
- `create_container()` - 创建新容器
- `fork_container()` - Fork 容器（COW 卷复制）
- `merge_and_destroy()` - 合并后销毁容器
- `destroy_container()` - 完全销毁容器

### 3. bff/bff_service.py
BFF 服务，REST API：
- `POST /conversations` - 创建对话
- `POST /conversations/{id}/messages` - 发送消息
- `POST /conversations/{id}/fork` - Fork 分支
- `POST /merge` - 合并分支
- `DELETE /conversations/{id}` - 删除对话

## 使用方法

### 本地开发

```bash
# 1. 构建 Agent 镜像
cd milestone2
docker build -f shared/Dockerfile.agent -t nanobot-agent:latest .

# 2. 启动 BFF
cd milestone2/bff
pip install docker httpx fastapi uvicorn pydantic
python bff_service.py
```

### Docker Compose

```bash
cd milestone2
docker-compose -f shared/docker-compose.yml up --build
```

## API 示例

### 创建对话
```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "数据分析任务", "model": "deepseek-chat"}'
```

### 发送消息
```bash
curl -X POST http://localhost:8000/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "分析本月销售数据"}'
```

### Fork 分支
```bash
curl -X POST http://localhost:8000/conversations/{id}/fork \
  -H "Content-Type: application/json" \
  -d '{"parent_conversation_id": "{id}", "new_branch_name": "explore"}'
```

### Merge 分支
```bash
curl -X POST http://localhost:8000/merge \
  -H "Content-Type: application/json" \
  -d '{"source_conversation_id": "{fork_id}", "target_conversation_id": "{main_id}"}'
```

## 资源限制

| 资源 | 限制 |
|------|------|
| 内存 | 512MB / 容器 |
| CPU | 0.5 core / 容器 |
| 最大活跃容器 | 20 |
