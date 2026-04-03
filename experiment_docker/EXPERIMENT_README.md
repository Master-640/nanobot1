# LLM Backend 对比实验 - Docker 容器化方案

## 📋 实验设计

### 架构
```
宿主机运行 run_experiments.py
  ↓
创建 16 个 Docker 容器（4 任务 × 4 模型）
  ↓
每个容器内:
  1. 运行 nanobot onboard
  2. 生成 config.json
  3. 启动 nanobot agent
  4. 发送任务消息（包含 CSV 数据）
  5. 监控完成情况（2 分钟无输出则退出）
  6. 保存结果到 /app/experiment_outputs/
  ↓
容器退出后，收集结果生成报告
```

### 实验矩阵

| 任务 | DeepSeek-chat | Qwen3-max | Kimi-k2.5 | MiniMax-M1 |
|------|--------------|-----------|-----------|------------|
| Task1_Sales | ✅ | ✅ | ✅ | ✅ |
| Task2_User | ✅ | ✅ | ✅ | ✅ |
| Task3_Finance | ✅ | ✅ | ✅ | ✅ |
| Task4_Review | ✅ | ✅ | ✅ | ✅ |

**总计**: 16 个容器，并发 4 个

---

## 🚀 使用方法

### 1. 准备数据

确保数据文件在 `shared/data/` 目录：
```
shared/data/
├── sales.csv
├── user_behavior.csv
├── financial.csv
└── reviews.csv
```

### 2. 配置 API Key

在宿主机设置环境变量：
```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-xxx"
$env:DASHSCOPE_API_KEY="sk-xxx"
$env:KIMI_API_KEY="sk-xxx"
$env:MINIMAX_API_KEY="xxx"

# Linux/macOS
export DEEPSEEK_API_KEY="sk-xxx"
export DASHSCOPE_API_KEY="sk-xxx"
export KIMI_API_KEY="sk-xxx"
export MINIMAX_API_KEY="xxx"
```

### 3. 运行实验

```bash
cd d:\collections2026\phd_application\nanobot1\experiment_docker
python run_experiments.py
```

### 4. 查看结果

结果保存在：
```
results/
├── container_results_YYYYMMDD_HHMMSS.json  # 汇总结果
└── outputs/                                 # 各任务产出
    ├── Task1_Sales/
    │   ├── deepseek_chat/
    │   │   ├── agent.log
    │   │   ├── token_usage.txt
    │   │   └── status.json
    │   └── ...
    └── ...
```

---

## 🔧 文件说明

| 文件 | 说明 |
|------|------|
| `run_experiments.py` | 宿主机运行脚本（orchestrator） |
| `container_runner.py` | 容器内运行脚本（每个容器执行一次） |
| `Dockerfile` | Docker 镜像定义 |
| `shared/data/` | 任务数据文件 |
| `results/outputs/` | 实验产出 |

---

## ⚙️ 配置参数

可在 `run_experiments.py` 中修改：

```python
MAX_CONCURRENT = 4           # 最大并发容器数
TIMEOUT_SECONDS = 1800       # 单个容器超时（30 分钟）
NO_OUTPUT_TIMEOUT = 120      # 无输出超时（2 分钟）
```

---

## 📊 完成判断

容器通过以下方式判断任务完成：

1. **主要判断**：监控 `token_usage.txt`，2 分钟无更新则认为完成
2. **超时保护**：最大运行 30 分钟，强制退出
3. **可选优化**：定期询问大模型是否完成任务（未实现）

---

## 🐛 故障排查

### 容器启动失败
```bash
# 手动测试单个容器
docker run -it --rm \
  -e SESSION_KEY=test \
  -e NANOBOT_MODEL=deepseek-chat \
  -e TASK_NAME=Task1_Sales \
  -e DEEPSEEK_API_KEY=xxx \
  -v ./shared/data:/app/experiment_data:ro \
  nanobot-experiment
```

### 查看容器日志
```bash
docker logs nanobot_Task1_Sales_deepseek_chat
```

### 清理残留容器
```bash
docker ps -a | grep nanobot | awk '{print $1}' | xargs docker rm -f
```

---

## 📈 后续优化

- [ ] 添加大模型完成度判断（询问是否完成任务）
- [ ] 支持更多 LLM Backend
- [ ] 自动生成对比报告（Markdown 格式）
- [ ] 支持实验重复运行（多次实验取平均）

---

*最后更新：2026-03-31*
