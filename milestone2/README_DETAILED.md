
# SAYG-Mem: 三段内存多Agent协同进化系统

## 📖 项目概述

**SAYG-Mem** (Stack/Heap/Yield-Guided Memory) 是一个面向多Agent协同的三段内存学习架构，旨在解决多Agent知识进化过程中的三个核心问题：

1. **推理噪声隔离** - 避免短期推理噪声污染长期知识库
2. **并发写入冲突** - 消除多Agent同时写入的竞争条件
3. **吞吐量瓶颈** - 通过异步合并机制提升系统整体性能

本项目是 **Milestone 2** 的完整实现，包含完整的实验验证和性能数据。

---

## 🎯 核心创新：三段内存架构

| 内存段 | 语义 | 存储内容 | 持久化 | 写入权限 | 并发特性 |
|---------|------|---------|--------|---------|---------|
| **栈段 (Stack)** | 私有短期噪声隔离区 | 单轮推理步骤、临时假设、中间计算 | ❌ | 单个Agent | 无竞争 |
| **堆段 (Heap)** | 独立中期协作缓冲区 | 阶段性结论、可共享的中间共识、任务最终输出 | ✅ (heap_{agent_id}.jsonl) | 单个Agent | 无竞争（独立堆） |
| **数据段 (Data)/PublicMemory** | 全局长期知识库 | 经过验证的Skill、方法论、多轮共识、Page处理结果 | ✅ | 仅KnowledgeManager | 只读共享 |

### 写入规则总结
```
推理噪声 → 栈段（不持久化）
任务产出 → 堆段（持久化，待合并）
长期知识 → 数据段（由KnowledgeManager写入PublicMemory）
```

---

## 🏗️ 系统架构

### 整体架构图
```
┌─────────────────────────────────────────────────────────────────────────┐
│                        验证脚本 (Orchestrator)                            │
│                  learn_segments_collab.py / run_*.py                     │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐         ┌─────────────────────────────────┐
│  BFF (FastAPI)   │         │  Docker Daemon                  │
│  :8000           │         │                                 │
└────────┬─────────┘         │  ┌─────────────┐  ┌───────────┐│
         │                   │  │ KM Agent    │  │ Collaborat││
         │ HTTP              │  │ Container   │  │ or Agent  ││
         │                   │  └─────────────┘  └───────────┘│
         ▼                   │         │                │       │
┌──────────────────┐         │         ▼                ▼       │
│ KnowledgeManager │         │  ┌─────────┐      ┌─────────┐   │
│   - CWW Merge   │         │  │ Volume  │      │ Volume  │   │
│   - PublicMemory│         │  │  (COW)  │      │  (COW)  │   │
└──────────────────┘         │  └─────────┘      └─────────┘   │
                              └─────────────────────────────────┘
```

### 核心组件

#### 1. **BFF Service** (`bff/bff_service.py`)
- **职责**：后端服务，提供 REST API
- **端口**：8000
- **功能**：
  - 会话管理（创建/删除/Fork/Merge）
  - 容器编排
  - 知识管理接口
  - Power 机制
  - 文件监控

#### 2. **KnowledgeManager** (`bff/knowledge_manager.py`)
- **职责**：PublicMemory 管理和 CWW 异步合并
- **核心机制**：**CWW (Concurrent Write Without blocking)**
  - 协作者提交 → 立即入队 → 立即返回（不阻塞）
  - 后台线程定时批量合并
- **配置**：
  - `merge_interval`: 合并间隔（默认 2.0s）
  - `merge_threshold`: 合并阈值（默认 3 条）

#### 3. **ContainerOrchestrator** (`bff/container_orchestrator.py`)
- **职责**：Docker 容器生命周期管理
- **功能**：
  - `create_container()` - 创建新容器
  - `fork_container()` - Fork 容器（COW 卷复制）
  - `merge_and_destroy()` - 合并后销毁容器
  - `destroy_container()` - 完全销毁容器

#### 4. **AgentServer** (`nanobot_agent/agent_server.py`)
- **职责**：容器内 HTTP 服务
- **接口**：
  - `POST /chat` - 发送消息给 agent
  - `GET /trajectory` - 获取轨迹数据
  - `GET /history` - 获取对话历史
  - `GET /health` - 健康检查

---

## 📊 实验结果

### 核心实验 1: 吞吐量对比

**实验设置**：
- 时间预算：300 秒
- Agent 数量：10
- 实验模式：固定时间预算，统计完成轮数

| 指标 | A组（SAYG-Mem） | B组（Baseline） | 提升 |
|------|----------------|----------------|------|
| 总完成轮数 | 43 | 10 | **4.3×** |
| 平均单Agent轮数 | 4.3 | 1.0 | - |
| 实际耗时 | 344.55s | 315.63s | - |
| 推理总耗时 | 1655.13s | 871.77s | - |
| 合并总耗时 | 0.00s | 78.85s | - |
| 合并耗时占比 | 0.0% | 25.0% | - |
| Agent空闲等待占比 | 52.0% | 72.4% | - |
| PublicMemory条目数 | 3 | 3 | - |
| 失败轮数 | 0 | 0 | - |

**结论**：
- 吞吐量提升 **4.3×**
- Agent 空闲等待占比降低 **20.4 个百分点**
- 合并耗时占比降低 **25.0 个百分点**

---

### 核心实验 2: 扩展性测试

| Agent数量 | A组轮数 | B组轮数 | 吞吐量提升 | A组空闲% | B组空闲% |
|-----------|---------|---------|-----------|----------|----------|
| 10 | 43 | 10 | 4.3× | 52.0% | 72.4% |
| 20 | 76 | 20 | 3.8× | 49.5% | 68.2% |
| 40 | 143 | 40 | 3.58× | 50.7% | 62.8% |

**分析结论**：
- 随着 Agent 数量增加，SAYG-Mem 的吞吐量优势保持在 3.5×~4.3×
- 空闲占比优势随着 Agent 增加略有下降，但仍显著优于 Baseline
- 系统在 40 个 Agent 时仍保持稳定

---

### 阈值敏感性分析

测试了不同 `(threshold, interval)` 组合对吞吐量的影响：

| Threshold | Interval | 总轮数 | 空闲等待% |
|-----------|----------|--------|----------|
| 5 | 30s | 43 | 52.0% |
| 5 | 60s | 42 | 53.1% |
| 5 | 120s | 40 | 54.5% |
| 20 | 30s | 45 | 50.2% |
| 20 | 60s | 44 | 51.3% |
| 20 | 120s | 41 | 52.8% |
| 50 | 30s | 46 | 49.1% |

**结论**：阈值和间隔设置对性能影响较小，系统具有鲁棒性。

---

## 🚀 快速开始

### 前置要求
- Python 3.10+
- Docker Desktop
- WSL 2（推荐）

### 步骤 0: 准备 Python 虚拟环境

```bash
# 进入项目根目录
cd d:/collections2026/phd_application/nanobot1/milestone2

# 创建虚拟环境（首次运行）
python -m venv shared/venv

# 激活虚拟环境
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

### 步骤 1: 构建 Docker 镜像

```bash
DOCKER_BUILDKIT=1 docker build -f shared/Dockerfile.agent -t nanobot-agent:latest .
DOCKER_BUILDKIT=1 docker build -f shared/Dockerfile.bff -t nanobot-bff:latest .
```

### 步骤 2: 启动 BFF 服务

**终端 1**：
```bash
cd d:/collections2026/phd_application/nanobot1/milestone2
./run_km_system.sh
```

### 步骤 3: 运行实验

**终端 2**：
```bash
cd d:/collections2026/phd_application/nanobot1/milestone2
source shared/venv/bin/activate

# 吞吐量对比实验（核心实验）
python sayg_integration/run_throughput_comparison.py

# 或单独运行 A 组吞吐量测试（SAYG-Mem）
python sayg_integration/learn_throughput_fixed_time_a.py

# 或单独运行 B 组测试（Baseline）
python sayg_integration/learn_throughput_fixed_time_b.py

# 扩展性测试（10/20/40 Agent）
python sayg_integration/run_scalability_test.py

# 阈值敏感性测试
python sayg_integration/run_threshold_sensitivity_test.py
```

---

## 📁 目录结构

```
milestone2/
├── bff/                             # BFF 后端服务
│   ├── bff_service.py              # FastAPI 主服务
│   ├── knowledge_manager.py        # KnowledgeManager 核心
│   ├── container_orchestrator.py   # Docker 容器管理
│   ├── bounty_hub.py              # 悬赏系统
│   ├── token_wallet.py            # Token 钱包
│   ├── public_space.py            # 公共空间
│   ├── reflex_engine.py           # 反射引擎
│   ├── social_graph.py            # 社交图谱
│   ├── evaluator.py               # 评估器
│   ├── db.py                      # 数据库
│   ├── config.py                  # 配置
│   └── key_logs.md                # 关键日志
├── nanobot_agent/                   # Agent 容器内服务
│   └── agent_server.py            # 容器内 HTTP 服务
├── sayg_integration/                # SAYG-Mem 实验
│   ├── learn_segments_collab.py   # 多Agent协作学习
│   ├── learn_throughput_fixed_time_a.py  # A组吞吐量
│   ├── learn_throughput_fixed_time_b.py  # B组吞吐量
│   ├── run_throughput_comparison.py      # 对比实验
│   ├── run_scalability_test.py    # 扩展性测试
│   ├── run_threshold_sensitivity_test.py  # 阈值测试
│   ├── config.py                  # 实验配置
│   ├── public_memory.py           # PublicMemory 实现
│   ├── heap_segment.py            # 堆段实现
│   ├── data_segment.py            # 数据段实现
│   ├── page_manager.py            # Page 管理
│   ├── consolidator.py            # 合并器
│   └── experiment_data/           # 实验数据
│       ├── throughput_comparison_result.md
│       ├── scalability_report.md
│       └── ...
├── frontend/                        # 前端界面
│   ├── src/
│   │   ├── components/
│   │   │   ├── BountyMarket.vue
│   │   │   ├── SkillEditor.vue
│   │   └── App.vue
│   └── index.html
├── logs/                            # 运行日志
├── data/                            # 数据目录
│   ├── heaps/                      # 堆段数据
│   └── public_memory/              # PublicMemory 数据
├── shared/                          # 共享配置
│   ├── Dockerfile.agent
│   ├── Dockerfile.bff
│   ├── docker-compose.yml
│   └── config.py
├── WSL_START_GUIDE.md              # WSL 启动指南
├── README.md                       # 原始 README
└── README_DETAILED.md              # 本文件
```

---

## 🔌 API 参考

### BFF 服务 API

#### 创建对话
```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "数据分析任务", "model": "deepseek-chat", "agent_type": "km"}'
```

#### 发送消息
```bash
curl -X POST http://localhost:8000/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "分析本月销售数据"}'
```

#### Fork 分支
```bash
curl -X POST http://localhost:8000/conversations/{id}/fork \
  -H "Content-Type: application/json" \
  -d '{"parent_conversation_id": "{id}", "new_branch_name": "explore"}'
```

#### Merge 分支
```bash
curl -X POST http://localhost:8000/merge \
  -H "Content-Type: application/json" \
  -d '{"source_conversation_id": "{fork_id}", "target_conversation_id": "{main_id}"}'
```

#### KnowledgeManager API
```bash
# 预置 0号Skill
curl -X POST http://localhost:8000/knowledge-manager/preset-skill-0 \
  -H "Content-Type: application/json" \
  -d '{"content": "skill内容", "skill_version": "1.0"}'

# 提交 Page
curl -X POST http://localhost:8000/knowledge-manager/submit-page \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_a", "page_content": "page内容", "page_title": "标题", "round_num": 1}'

# 检索 PublicMemory
curl -X GET http://localhost:8000/knowledge-manager/public-memory?query=skill&amp;top_k=3

# 获取统计
curl http://localhost:8000/knowledge-manager/stats
```

---

## 📚 核心文档

### 实验报告
- `sayg_integration/experiment_data/throughput_comparison_result.md` - 吞吐量对比实验
- `sayg_integration/experiment_data/scalability/scalability_report.md` - 扩展性测试报告

### 开发文档
- `WSL_START_GUIDE.md` - WSL 环境启动指南
- `README.md` - 原始实验复现指南

### 技术方案
- `.trae/documents/` 目录下的技术方案文档

---

## 🎯 Milestone 3 展望

当前已完成 **Milestone 2**，实现了：
- ✅ 三段内存架构
- ✅ CWW 异步合并机制
- ✅ 完整的实验验证
- ✅ 性能优化（吞吐量提升 4.3×）

**Milestone 3** 目标：
- 🔄 系统整合
- ♻️ 实现基本**进化闭环**
- 🤖 Agent 自我进化能力

---

## 📝 资源限制

| 资源 | 限制 |
|------|------|
| 内存 | 512MB / 容器 |
| CPU | 0.5 core / 容器 |
| 最大活跃容器 | 20 |

---

## 🔗 相关项目

- **nanobot** - 超轻量级个人 AI 助手框架
- **OpenClaw** - 原始参考项目
- **MetaClaw** - 本目录下的参考实现

---

## 📄 许可证

本项目用于教育和研究目的。

---

## 📞 联系方式

如有问题，请查看项目相关文档或联系维护者。

