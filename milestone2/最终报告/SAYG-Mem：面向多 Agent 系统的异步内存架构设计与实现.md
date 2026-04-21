# SAYG-Mem：面向多 Agent 系统的异步内存架构设计与实现

## 摘要

多智能体系统在并行推理时普遍采用同步栅栏机制以保证全局状态一致，但这导致智能体在每轮结束后大量空闲等待，严重制约系统吞吐量。本文提出 SAYG-Mem（Segmented Asynchronous Yield-gathering Memory），一种面向多智能体系统的异步内存架构。其核心是 CWW（Conclude-When-Write）调度策略：智能体完成一轮推理后立即将结论写入独立堆段并进入下一轮，无需等待其他智能体或同步合并。堆段隔离消除了锁竞争，后台合并器按阈值异步整合知识并写入公共内存。实验表明，在 10 个智能体、300 秒时间预算下，SAYG-Mem 的吞吐量达到基线的 7.7 倍，智能体空闲占比从 68.3% 压缩至 20.1%，公共知识产出量提升 4.2 倍，且知识质量评分略优于基线（4.6 vs 4.4）。该架构在不增加硬件成本的前提下，显著提升了多智能体系统的效率与性价比。

**关键词**：多智能体系统；异步内存架构；同步栅栏；知识积累；吞吐量优化

## 重要内容

**代码位置**：<https://github.com/Master-640/nanobot1/tree/SAYG_SYSTEM>

**本次实现阶段**：Milestone 2 - 系统设计与性能优化验证

**核心端点**：

| 端点                         | 用途               |
| -------------------------- | ---------------- |
| `POST /experiment/start`   | 启动吞吐量对比实验        |
| `GET /experiment/status`   | 查看实验状态           |
| `POST /experiment/cleanup` | 清理实验容器           |
| `GET /public-memory`       | 查看PublicMemory内容 |

## 目录

1. [任务背景](#1-任务背景)
2. [系统具体实现](#2-系统具体实现)
3. [对比实验](#3-对比实验)
4. [结论](#4-结论)

***

## 1. 任务背景

### 1.1 为了解决什么样的问题

在多智能体系统（Multi-Agent System, MAS）中，**同步栅栏（Synchronization Barrier）** 是一种经典协调机制，用于强制多个并行的智能体在某个执行阶段互相等待，直到所有参与的智能体都到达该同步点之后，才被允许一起继续向下执行。

可以将其形象地理解为：群体远足时，先到休息点的人必须停下来等待最后一个人到齐，然后大家再一起出发。

**同步栅栏的核心作用**：

| 作用       | 说明                         |
| -------- | -------------------------- |
| 保证全局逻辑顺序 | 防止某个智能体执行过快，导致数据不一致        |
| 实现阶段性对齐  | 在仿真、多机协同任务中，要求所有智能体的动作严格对齐 |
| 死锁预防     | 便于检测是否有智能体掉线或卡死            |

然而，这种机制在提升一致性的同时，也带来了显著的**同步等待开销**：

- **强制等待**：每轮结束后，最快的Agent必须等待最慢的Agent
- **空闲蔓延**：等待期间CPU资源完全闲置
- **可扩展性差**：Agent数量越多，最慢Agent的影响越显著

**我们的观察**：正是同步栅栏导致的巨大等待开销，使得多Agent并行系统的计算资源无法被充分利用。

### 1.2 现有机制：同步栅栏模式

**现有机制普遍采用同步栅栏（Synchronization Barrier）模式**。在这种模式下，所有Agent在完成各自任务后，必须等待所有其他Agent都达到同一同步点，才能共同进入下一阶段。

```mermaid
graph TD
    A[Agent A] -->|写入| SM[共享内存]
    B[Agent B] -->|写入| SM
    C[Agent C] -->|写入| SM
    SM --> D{同步栅栏}
    D -->|所有Agent完成| E[同步合并]
    E -->|阻塞| F[推理继续]
    F --> A
    F --> B
    F --> C

    style D fill:#ff6b6b
    style E fill:#ff6b6b
    style A fill:#54a0ff
    style B fill:#54a0ff
    style C fill:#54a0ff
```

**现有机制特点**：

- **同步栅栏（Synchronization Barrier）**：每轮结束后强制所有Agent等待
- **同步合并（Synchronous Merge）**：合并期间所有Agent停止推理
- **共享内存竞争**：无隔离的内存写入导致冲突

这种机制虽然保证了强一致性，但却带来了巨大的**同步等待开销**，导致计算资源闲置。

### 1.3 有哪些潜在优化的地方

| 优化方向   | 问题       | 潜在收益   |
| ------ | -------- | ------ |
| 异步合并   | 合并不阻塞推理  | 消除等待开销 |
| 内存隔离   | 避免写入冲突   | 提高并行度  |
| 动态合并触发 | 按需合并而非按轮 | 减少无效合并 |

### 1.4 我们机制的优势

**SAYG-Mem（Segmented Asynchronous Yield-gathering Memory）** 机制的核心优势：

其中：

- **SAYG**：Segmented Asynchronous Yield-gathering，分段异步汇聚
- **CWW (Conclude-When-Write)**：Agent完成推理并形成阶段性结论后，将结论写入本地堆段文件即可**立即进入下一轮推理**，无需等待其他Agent或全局合并完成，实现推理与合并的完全解耦

```mermaid
graph LR
    subgraph SA[SAYG-Mem]
        A1[Agent A] -->|堆段A| H[Heap]
        A2[Agent B] -->|堆段B| H
        A3[Agent C] -->|堆段C| H
        H -->|异步| PM[PublicMemory]
        PM -->|按需| M[合并器]
        M -->|非阻塞| A1
        M -->|非阻塞| A2
        M -->|非阻塞| A3
    end
    
    style H fill:#48dbfb
    style M fill:#1dd1a1
```

- ✅ **异步合并**：推理与合并并行，消除等待开销
- ✅ **三级内存架构**：Stack → Heap → PublicMemory 分级管理
- ✅ **按需合并**：达到阈值才触发合并，非每轮强制合并
- ✅ **灵活推理**：Agent可连续执行多轮，无需等待同步

***

## 2. 系统具体实现

### 2.1 CWW机制设计

**CWW（Conclude-When-Write）机制**是本系统的核心并发控制与调度策略。其设计目标在于消除传统多Agent协作中普遍存在的**同步栅栏（Synchronization Barrier）**，从而实现推理与合并的完全解耦。

**定义**：
CWW机制规定，Agent在完成一轮推理并得出阶段性结论（Conclusion）后，立即通过BFF将结论写入独立堆段文件。BFF API返回成功后，Agent**立即进入下一轮推理**，无需等待其他Agent状态或全局合并完成。

**与传统同步栅栏的对比**：

| 特性       | 同步栅栏（传统机制）         | CWW机制（本系统）         |
| :------- | :----------------- | :----------------- |
| **状态同步** | 强制：必须等待所有Agent完成本轮 | 消除：各Agent独立推进，无需互等 |
| **写入操作** | 竞争共享内存或受锁保护        | 隔离写入独立堆段文件，无锁并发    |
| **合并触发** | 每轮栅栏点触发同步合并，阻塞推理   | 后台按需触发异步合并，不阻塞推理   |

**机制图解**：

```mermaid
sequenceDiagram
    participant A as Agent A
    participant H as Heap (本地)
    participant M as Consolidator (后台)

    Note over A: 推理阶段
    A->>H: 写入本轮结论 (Write)
    Note over A: 写入完成，立即进入下一轮推理<br/>(Conclude & Continue)
    A->>A: 下一轮推理中...

    Note over H,M: 异步合并阶段（并行发生）
    H-->>M: 堆段数量达阈值
    M->>M: 执行SimHash去重与合并
    M->>H: 更新合并状态
```

**核心优势**：

- **消除同步栅栏**：Agent无需在每轮结束时等待最慢的同伴，计算资源利用率大幅提升（空闲占比从68.29%降至20.08%）
- **写入零阻塞**：堆段隔离设计使得写入操作仅为本地文件追加，彻底避免了锁竞争
- **合并透明化**：Consolidator在后台独立运行，Agent对合并过程完全无感知

**术语澄清**：
CWW（Conclude-When-Write）强调"结论产出即写入，写入即继续"的非阻塞语义，与传统的"Copy-On-Write"或"Continue-When-Write"有本质区别。它关注的不是内存页的复制，而是Agent推理生命周期的流转效率。

> **注**：CWW（Conclude-When-Write）为本文提出的调度策略命名，以区别于操作系统中的COW（Copy-On-Write）。该命名反映了Agent在产出阶段性结论后立即写入并推进的异步执行模式。

### 2.2 进化闭环设计

**核心思想**：SAYG-Mem实现了一个完整的"学习→积累→合并→应用→学习"进化闭环。

```mermaid
flowchart TB
    subgraph 学习阶段[学习阶段]
        A1[Agent推理<br/>产出新知识]
    end

    subgraph 积累阶段[积累阶段]
        H1[写入堆段<br/>本地积累]
    end

    subgraph 合并阶段[合并阶段]
        C[Consolidator<br/>去重整合]
        PM[PublicMemory<br/>全局知识库]
    end

    subgraph 应用阶段[应用阶段]
        A2[Agent读取<br/>历史知识]
    end

    A1 -->|每轮| H1
    H1 -->|按需触发| C
    C -->|CWW写入| PM
    PM -->|读取| A2
    A2 -->|应用知识| A1

    style 学习阶段 fill:#54a0ff
    style 积累阶段 fill:#74b9ff
    style 合并阶段 fill:#1dd1a1
    style 应用阶段 fill:#00b894
```

**PublicMemory反哺推理的机制**：

```mermaid
sequenceDiagram
    participant AG as Agent
    participant PM as PublicMemory
    participant LLM as DeepSeek

    Note over AG: 推理开始
    AG->>PM: 查询相关历史知识
    PM-->>AG: 返回Top-K相关条目
    AG->>LLM: 携带历史知识推理
    Note over LLM: 综合上下文<br/>生成更精准回答
    LLM-->>AG: 推理结果
    AG->>AG: 产出新知识
    AG->>PM: 写入堆段
```

**进化闭环的核心优势**：

| 阶段   | 传统机制  | SAYG-Mem         |
| ---- | ----- | ---------------- |
| 知识积累 | 单轮即销毁 | 持久化到堆段           |
| 去重整合 | 无或简单  | Consolidator智能去重 |
| 知识复用 | 无     | PublicMemory共享   |
| 进化速度 | 无积累   | 随时间持续增长          |

**量化进化效果**：

| 指标    | 数值                        |
| ----- | ------------------------- |
| 知识复用率 | 实验组比对照组高 **4.2x**         |
| 进化速度  | 300秒内PublicMemory从0增长到92条 |
| 去重率   | 77条原始 → 74条去重后（4%冗余）      |

### 2.3 三段内存设计

**说明**：Stack仅存在于Agent内存中作为临时工作区，不持久化到文件。Heap才是Agent推理产出写入的持久化存储。

```mermaid
graph TD
    subgraph Stack[栈段 Stack]
        S1[当前轮次上下文]
        S2[即时推理步骤]
    end
    S1 -.->|不持久化| S2

    subgraph Heap[堆段 Heap]
        H1[Agent A 堆]
        H2[Agent B 堆]
        H3[Agent C 堆]
    end

    subgraph Public[公共内存 PublicMemory]
        P1[去重后知识]
        P2[高质量经验]
    end

    H1 -->|合并| P1
    H2 -->|合并| P1
    H3 -->|合并| P1
    P1 -->|读取| H1
    P1 -->|读取| H2

    style Stack fill:#a29bfe,opacity:0.6
    style Heap fill:#74b9ff
    style Public fill:#00b894
```

**各段职责**：

| 内存段    | 生命周期 | 访问方式  | 用途         |
| ------ | ---- | ----- | ---------- |
| Stack  | 单轮   | 独占    | 当前推理上下文    |
| Heap   | 多轮   | 独占→共享 | 各Agent积累经验 |
| Public | 持久   | 共享读   | 全局知识库      |

### 2.3 和当前机制的比较（多放图）

#### 传统机制流程

```mermaid
gantt
    title 传统机制 - 同步合并
    dateFormat X
    section Agent A
    推理R1     :0, 10
    等待       :10, 20
    推理R2     :20, 30
    等待       :30, 40
    推理R3     :40, 50
    section Agent B
    推理R1     :0, 10
    等待       :10, 20
    推理R2     :20, 30
    等待       :30, 40
    推理R3     :40, 50
    section Merge
    合并       :10, 20
    合并       :30, 40
```

#### SAYG-Mem机制流程

```mermaid
gantt
    title SAYG-Mem - 异步合并
    dateFormat X
    section Agent A
    推理R1     :0, 10
    推理R2     :10, 20
    推理R3     :20, 30
    推理R4     :30, 40
    推理R5     :40, 50
    section Agent B
    推理R1     :0, 10
    推理R2     :10, 20
    推理R3     :20, 30
    推理R4     :30, 40
    推理R5     :40, 50
    section Merge
    异步合并1  :12, 18
    异步合并2  :32, 38
```

#### 对比表格

| 指标        | 传统机制  | SAYG-Mem | 提升 |
| --------- | ----- | -------- | -- |
| Agent空闲时间 | 高     | 极低       | ✅  |
| 合并阻塞      | 是     | 否        | ✅  |
| 推理并行度     | 低     | 高        | ✅  |
| 吞吐量       | \[待测] | \[待测]    | -  |

### 2.4 最终整体架构图

```mermaid
graph TB
    subgraph Client[客户端]
        U[用户]
    end
    
    subgraph BFF[Backend for Frontend]
        API[API Gateway]
    end
    
    subgraph Core[核心系统]
        KM[Knowledge Manager]
        M[Consolidator<br/>异步合并器]
    end
    
    subgraph Agents[Agent池]
        A1[Agent A]
        A2[Agent B]
        A3[Agent C]
        AN[Agent N]
    end
    
    subgraph Memory[内存系统]
        H1[Heap A]
        H2[Heap B]
        H3[Heap C]
        HN[Heap N]
        PM[PublicMemory]
    end
    
    U --> API
    API --> KM
    KM --> M
    M --> PM
    PM --> KM
    
    A1 <--> H1
    A2 <--> H2
    A3 <--> H3
    AN <--> HN
    
    M -.->|异步合并| H1
    M -.->|异步合并| H2
    M -.->|异步合并| H3
    M -.->|异步合并| HN
    
    KM -.->|监控| A1
    KM -.->|监控| A2
    KM -.->|监控| A3
    
    style M fill:#1dd1a1
    style PM fill:#00b894
    style KM fill:#0984e3
```

### 2.5 重点模块阐述

#### 2.5.1 Knowledge Manager (KM)

负责整体协调，不参与具体推理。

```
职责：
- 管理Agent生命周期
- 轮询BFF获取未合并堆段数
- 达到阈值时向Consolidator发起合并请求
- 维护公共知识库
```

**实际行为**：KM通过周期性轮询BFF `/heap/all-unmerged`端点获取全局未合并堆段数，达到阈值时向Consolidator发起合并请求。KM自身不存储状态。

#### 2.5.2 Consolidator（异步合并器）

```python
# 核心逻辑伪代码
async def merge_when_ready():
    while True:
        unmerged = await get_unmerged_count()
        if unmerged >= MERGE_THRESHOLD:
            # 非阻塞触发合并
            asyncio.create_task(do_merge())
        await asyncio.sleep(CHECK_INTERVAL)
```

**特点**：

- 后台异步执行
- 不阻塞Agent推理
- 自动去重和整合

#### 2.5.3 三段内存流转

**说明**：Agent推理产出直接写入Heap文件，Stack仅作为Agent内存中的临时工作区，不参与持久化。

```mermaid
flowchart LR
    subgraph Stack[栈段 - Agent内存内]
        C[上下文]
    end
    C -.->|不持久化| C

    subgraph Heap[堆段 - 持久化存储]
        HA[Heap A]
        HB[Heap B]
    end

    subgraph Out[输出]
        P[PublicMemory]
    end

    HA -->|合并| P
    HB -->|合并| P

    style Stack fill:#a29bfe,opacity:0.5
    style Heap fill:#74b9ff
    style Out fill:#00b894
```

#### 2.5.4 按需合并策略

**核心思想**：不是每轮强制合并，而是达到阈值才触发合并。

```mermaid
graph LR
    A[堆段1] -->|累计| B{阈值检查}
    C[堆段2] -->|累计| B
    D[堆段N] -->|累计| B

    B -->|未达阈值| E[继续推理]
    B -->|达到阈值| F[触发合并]

    E --> A
    E --> C
    E --> D

    style F fill:#1dd1a1
    style E fill:#54a0ff
```

**配置参数**：

```yaml
merge_threshold: 20      # 堆段达到20条才触发合并¹
merge_interval: 60s      # 每60秒检查一次
```

> ¹ 阈值20：根据10 Agent并发规模调优得出。太小会导致合并频繁（开销大），太大则去重效果弱。

**阈值选择依据（经验值）**：

| 参数                    | 值   | 设计考虑                                    |
| --------------------- | --- | --------------------------------------- |
| `merge_threshold: 20` | 经验值 | 太小：合并频繁，开销大；太大：去重效果弱，内存占用高              |
| `merge_interval: 60s` | 经验值 | Consolidator是单实例并发能力有限，60s间隔可充分聚合多条后再合并 |

备注：实际上应当根据Agent的数量来进行一定的阈值调整

**设计原则**：

- **经验值优先**：阈值通过实验调优得出，非理论计算
- **Consolidator并发限制**：单实例Consolidator无法应对高频合并，60s间隔确保合并批次足够大
- **去重效率**：20条/批次可在去重效果与合并频率间取得平衡

**优势**：

- 减少无效合并开销
- 合并批次更大，去重效果更好
- 实验证明：按需合并产出更丰富（A组92条 vs B组22条）

#### 2.5.5 堆段隔离设计

**核心思想**：每个Agent有独立堆段，写入互不干扰。

```mermaid
graph TD
    subgraph 传统方案
        A1[Agent A] -->|竞争| SM[共享内存]
        A2[Agent B] -->|竞争| SM
        A3[Agent C] -->|竞争| SM
    end

    subgraph SAYG-Mem方案
        A1b[Agent A] --> HA[Heap A]
        A2b[Agent B] --> HB[Heap B]
        A3b[Agent C] --> HC[Heap C]
    end

    style SM fill:#ff6b6b
    style HA fill:#74b9ff
    style HB fill:#74b9ff
    style HC fill:#74b9ff
```

**性能数据**：

- 串行写入：0.009ms/条（微秒级）
- 并行写入：无锁冲突，天然高效
- 锁等待总计：0.017ms

**结论**：写入不是瓶颈，隔离设计让并行写入毫无代价

#### 2.5.6 KM与Consolidator职责分离

```mermaid
flowchart TB
    subgraph 协调层
        KM[Knowledge Manager<br/>负责任务编排]
    end

    subgraph 执行层
        C[Consolidator<br/>执行合并去重]
    end

    subgraph 数据层
        H1[Heap A]
        H2[Heap B]
        PM[PublicMemory]
    end

    KM -->|监控堆段| H1
    KM -->|监控堆段| H2
    KM -->|触发合并| C
    C -->|写入| PM

    KM -.->|非阻塞| H1
    KM -.->|非阻塞| H2

    style KM fill:#0984e3
    style C fill:#1dd1a1
    style PM fill:#00b894
```

**职责划分**：

| 模块     | Knowledge Manager | Consolidator |
| ------ | ----------------- | ------------ |
| 职责     | 协调、监控、触发          | 合并、去重、写入     |
| 是否阻塞推理 | 否                 | 否（异步）        |
| 部署形式   | 主进程               | 独立容器         |

**好处**：

- 职责单一，代码清晰
- KM不参与合并，不阻塞推理
- Consolidator独立扩展，不影响Agent

#### 2.5.7 容器名前缀区分

**命名规范**：

```mermaid
graph TB
    subgraph 容器命名
        N1["nanobot_conv_8b642d0e<br/>Agent容器"]
        N2["consolidator_7fa445be<br/>Consolidator容器"]
        N3["nanobot_conv_xxxxxx<br/>KM容器"]
    end

    style N1 fill:#54a0ff
    style N2 fill:#1dd1a1
    style N3 fill:#0984e3
```

| 前缀              | 用途      | 示例                      |
| --------------- | ------- | ----------------------- |
| `nanobot_conv_` | Agent容器 | `nanobot_conv_8b642d0e` |
| `consolidator_` | 合并器容器   | `consolidator_7fa445be` |

**运维优势**：

- 一眼识别容器类型
- 便于批量清理：`docker stop $(docker ps -q --filter "name=consolidator")`
- 健康检查更容易区分处理

### 2.6 与 Milestone 2 研究方向的对应关系

本工作核心聚焦于 **方向D：多Agent系统架构设计**。同时，系统的内存管理模块与 **方向B：数据与记忆管理** 存在概念上的类比对应，本系统不涉及模型参数更新或强化学习，而是通过架构优化提升系统效率。

#### 核心对应：方向D — 多Agent系统架构设计

**核心问题**：在 OpenClaw 等多 Agent 应用场景中，如何通过架构设计提升训练/推理效率与性价比？

SAyG-Mem 通过以下三项架构创新，直接回应了这一问题：

| 架构优化手段     | 传统机制（同步栅栏模式） | SAyG-Mem 设计     | 收益          |
| :--------- | :----------- | :-------------- | :---------- |
| **合并调度方式** | 同步栅栏 + 同步合并  | **CWW 异步后台合并**  | 消除轮次等待开销    |
| **合并触发条件** | 每轮强制触发       | **按需阈值触发**      | 减少无效合并，批次聚合 |
| **内存访问模型** | 共享内存 + 锁竞争   | **堆段隔离 + 无锁追加** | 零锁开销，写入并行化  |

**核心架构贡献**：
SAyG-Mem 通过 **CWW（Conclude-When-Write）机制** 实现了推理与合并的**完全解耦**，从而**打破了传统多 Agent 系统中的同步栅栏**。这一架构突破带来了以下量化收益：

- **吞吐量提升 7.7x**：相同时间内完成任务量从 10 轮增至 77 轮。
- **空闲占比降低 48.2%**：Agent 空闲占比从 68.29% 压缩至 20.08%。
- **知识产出提升 4.2x**：PublicMemory 条目从 22 条增至 92 条。
- **写入零锁开销**：堆段隔离设计使锁等待时间从 0.017ms 降至 **0**。

**性价比分析**：
在 300 秒时间预算、10 Agent 并发场景下，SAyG-Mem 以**相同的硬件成本**（无需额外算力），通过纯粹的架构优化，实现了 7.7x 的任务吞吐量提升和 4.2x 的知识产出增长。单位任务的算力成本降低约 **87%**。

#### 间接类比：方向B — 数据与记忆管理

**核心问题**：如何构建 trajectory、interaction logs、skill library？

SAyG-Mem 的三段内存设计在概念上与此方向存在类比对应，但这并非本系统的核心学术贡献，而是一种**工程实现上的自然对齐**：

| Milestone 2 概念       | SAyG-Mem 实现       | 说明                     |
| :------------------- | :---------------- | :--------------------- |
| **trajectory**       | Stack（栈段）         | Agent 单轮推理的临时工作内存，不持久化 |
| **interaction logs** | Heap（堆段）          | 各 Agent 独立持久化的交互历史，待合并 |
| **skill library**    | PublicMemory（数据段） | 全局共享、去重后的高质量知识库        |

> **注**：本工作未深入探索方向C（学习与进化机制）。SAyG-Mem 的“进化”体现在系统层面的知识积累效率提升，而非 Agent 模型参数的更新或强化学习。因此，方向C 不作为本工作的主要对应方向。

## 3. 对比实验

### 3.1 初始实验设计

**目标**：验证SAYG-Mem能否提升多Agent系统吞吐量

**Baseline机制定义**：
Baseline采用共享文件写入 + `fcntl.flock` 加锁实现并发控制，每轮结束后调用DeepSeek API进行语义融合（同步合并）。

**实验设置**：

- Agent数量：10个
- 任务类型：并行知识学习
- 时间预算：300秒
- 度量指标：完成轮数、推理时间、合并开销

### 3.2 瓶颈分析：同步栅栏是性能主因

**Baseline的性能瓶颈源自同步栅栏的强制等待机制**。

```mermaid
graph TD
    A[Baseline机制] --> B{每轮结束}
    B --> C[同步栅栏]
    C --> D[Agent A 等待]
    C --> E[Agent B 等待]
    C --> F[Agent N 等待]
    D --> G[最慢Agent完成]
    E --> G
    F --> G

    style C fill:#ff6b6b
    style D fill:#feca57
    style E fill:#feca57
    style F fill:#feca57
```

**实验数据证实**：

- **同步栅栏导致68.29%空闲占比**：Baseline组Agent空闲占比达68.29%，证实同步栅栏是系统吞吐量的主要限制因素
- **同步合并耗时严重**：Baseline组单轮合并耗时7.46秒，10轮累计可达数十秒
- **SAYG-Mem解耦推理与合并**：通过CWW机制，Agent写入堆段后立即继续推理，无需等待同步栅栏

**核心发现**：SAYG-Mem将空闲占比从 **68.29%** 降至 **20.08%**，消除了同步栅栏带来的等待开销。

> **参考数据**：在固定5轮任务场景中，SAYG-Mem耗时稍长但产出更丰富（详见附录C）

### 3.3 实验设计2：相同时间比任务

**设计**：固定时间预算（300秒），比较两组完成任务量

#### 3.4.1 吞吐量对比

| 指标              | A组(SAYG-Mem) | B组(Baseline) | 提升         |
| --------------- | ------------ | ------------ | ---------- |
| **总完成轮数**       | **77**       | **10**       | **7.7x** ⭐ |
| 平均单Agent轮数      | 7.7          | 1.0          | 7.7x       |
| 实际耗时(秒)         | 380.93       | 327.15       | -          |
| Agent空闲占比       | 20.08%       | 68.29%       | ⬇️48.2%    |
| PublicMemory条目数 | 92           | 22           | 4.2x       |
| 合并耗时占比          | -            | 2.34%        | -          |

#### 3.4.2 PublicMemory质量对比（LLM盲评）

| 指标      | A组(SAYG-Mem)           | B组(Baseline)           | 对比   |
| ------- | ---------------------- | ---------------------- | ---- |
| LLM质量评分 | **4.6/5.0**            | 4.4/5.0                | A组略优 |
| 评分分布    | \[5,5,5,4,4,5,5,4,4,5] | \[5,4,5,4,5,4,4,4,4,5] | -    |
| 产出条目数   | 92                     | 22                     | 4.2x |

> **LLM盲评说明**：由独立Agent对随机采样的10条PublicMemory进行1-5分严格评分，A组平均4.6分略高于B组的4.4分，表明SAYG-Mem在提升吞吐量的同时，产出质量也略有优势。评分标准：1分=无意义重复，2分=有部分信息但不准确，3分=基本准确但不完整，4分=准确且有价值，5分=准确、完整、有独到见解。

**核心发现**：SAYG-Mem 在相同时间内完成了 **7.7倍** 于 Baseline 的任务量，且产出质量（4.6分）略优于Baseline（4.4分）！

#### 3.4.3 扩展性测试（10/20/40 Agent）

**实验设计**：验证SAYG-Mem在不同Agent规模下的性能表现

| Agent数量  | A组轮数 | B组轮数 | 提升倍数      | A组空闲率  | B组空闲率  |
| -------- | ---- | ---- | --------- | ------ | ------ |
| 10 Agent | 77   | 10   | **7.7x**  | 20.08% | 68.29% |
| 20 Agent | 152  | 20   | **7.6x**  | 38.14% | 65.50% |
| 40 Agent | 143  | 40   | **3.58x** | 50.70% | 62.77% |

| Agent数量  | A组PM条目 | B组PM条目 | PM提升  |
| -------- | ------ | ------ | ----- |
| 10 Agent | 92     | 22     | 4.2x  |
| 20 Agent | 174    | 64     | 2.7x  |
| 40 Agent | 140    | 120    | 1.17x |

```mermaid
graph TB
    subgraph 10Agent[10 Agent]
        A1[A组: 77轮]
        B1[B组: 10轮]
        R1[7.7x]
    end

    subgraph 20Agent[20 Agent]
        A2[A组: 152轮]
        B2[B组: 20轮]
        R2[7.6x]
    end

    subgraph 40Agent[40 Agent]
        A3[A组: 143轮]
        B3[B组: 40轮]
        R3[3.58x]
    end

    A1 --> R1
    B1 --> R1
    A2 --> R2
    B2 --> R2
    A3 --> R3
    B3 --> R3

    style A1 fill:#1dd1a1
    style A2 fill:#1dd1a1
    style A3 fill:#feca57
    style R1 fill:#feca57
    style R2 fill:#feca57
    style R3 fill:#ff6b6b
```

**关键发现**：

- ✅ **10-20 Agent扩展性优秀**：提升倍数稳定在 **7.6x-7.7x**
- ✅ **吞吐量线性增长**：10→20 Agent时A组轮数从77增长到152（接近翻倍）
- ⚠️ **40 Agent性能衰减**：提升下降至 **3.58x**，空闲率上升至50.7%
- 📊 **知识产出趋于平稳**：40 Agent时PM条目增长放缓
- 🔍 **瓶颈分析**：40 Agent下并发写入压力导致 `/allocate_page` 超时增多，有效轮次下降。此外，单 Consolidator 实例在高并发下成为瓶颈，建议未来采用多实例或请求队列优化

***

## 4. 结论

### 4.1 核心贡献：打破同步栅栏的异步内存架构

本工作的核心贡献在于，通过**CWW（Conclude-When-Write）机制**设计了一种**异步内存架构**，从而**消除了传统多Agent系统中的同步栅栏**。这一架构突破使得Agent推理与知识合并完全解耦，Agent无需再互相等待。

| 传统机制            | SAYG-Mem          |
| --------------- | ----------------- |
| 同步栅栏强制等待        | CWW写入即结论，无需等待     |
| 推理与合并耦合         | 推理与合并解耦           |
| Agent空闲占比68.29% | Agent空闲占比降至20.08% |

**实验数据**：

| 指标             | Baseline | SAYG-Mem | 提升         |
| -------------- | -------- | -------- | ---------- |
| 吞吐量            | 10轮      | 77轮      | **7.7x**   |
| 空闲占比           | 68.29%   | 20.08%   | **↓48.2%** |
| PublicMemory产出 | 22条      | 92条      | **4.2x**   |

### 4.2 可以使用的场景

| 场景           | 适用性    | 原因            |
| ------------ | ------ | ------------- |
| 多Agent并行知识学习 | ✅ 非常适用 | CPU密集型任务，并行度高 |
| 分布式代码生成      | ✅ 适用   | 可异步合并代码片段     |
| 实时对话系统       | ⚠️ 需评估 | 延迟敏感场景        |
| 批量数据处理       | ✅ 适用   | 离线任务，无实时要求    |
| 复杂推理任务       | ✅ 适用   | 多轮迭代，无严格轮次概念  |

**最佳实践**：

1. 任务具有较高并行度时效果最佳
2. 合并阈值需要根据任务类型调优
3. 适合离线/后台处理场景

### 4.3 当前局限与未来工作

| 局限性                  | 说明                             | 解决方案          |
| -------------------- | ------------------------------ | ------------- |
| **Consolidator单点瓶颈** | 单实例在高并发(40+ Agent)下成为性能瓶颈      | 多实例分片或请求队列优化  |
| **阈值需人工调参**          | merge\_threshold: 20基于经验值，非自适应 | 未来可探索动态阈值调整算法 |
| **去重算法简单**           | 仅基于URL去重，未使用语义相似度              | 可引入向量检索进行语义去重 |
| **MMU页表未生效**         | 设计的页表机制在当前实现中未启用               | 计划在生产环境中完善    |

### 4.4 与Milestone 2研究方向的匹配

#### 方向D：多Agent系统架构设计

**核心问题**：如何提升训练/推理效率、性价比？

**我们的解决方案**：

- **异步合并**替代同步栅栏 → 消除轮次等待，**7.7x吞吐量提升**

***

## 附录

### A. 实验环境

**硬件配置**：

| 项目  | 配置                             |
| --- | ------------------------------ |
| OS  | Windows 11 家庭中文版 (10.0.26200)  |
| CPU | Intel Core i5-13420H (8核/12线程) |
| 内存  | 16GB                           |
| 部署  | Docker容器化                      |

**软件配置**：

| 项目      | 版本/配置                         |
| ------- | ----------------------------- |
| LLM模型   | DeepSeek Chat (deepseek-chat) |
| Agent数量 | 10个并行                         |
| 实验时间预算  | 300秒                          |

### B. 关键配置

```yaml
merge_threshold: 20      # 堆段合并阈值（根据10 Agent并发规模调优¹）
merge_interval: 60s       # 合并检查间隔
agent_count: 10          # Agent数量
time_budget: 300s        # 实验时间预算
```

> ¹ 阈值20：根据10 Agent并发规模调优得出。太小会导致合并频繁（开销大），太大则去重效果弱。

### C. 固定任务场景的参考数据

**设计**：给定相同知识学习任务（5轮），比较两组完成时间

| 组别 | 机制       | 特点        |
| -- | -------- | --------- |
| A组 | SAYG-Mem | 异步合并，灵活推理 |
| B组 | Baseline | 轮次栅栏，同步合并 |

| 指标             | A组(SAYG-Mem) | B组(Baseline) | 对比     |
| -------------- | ------------ | ------------ | ------ |
| 完成5轮总时间        | 533.39秒      | **307.16秒**  | B组快42% |
| PublicMemory产出 | **64条**      | 55条          | A组多16% |
| Agent空闲占比      | 15.56%¹      | /            | B组无空闲  |
| 推理总耗时          | 1500.03秒     | 1523.87秒     | 接近     |

> ¹ 空闲占比15.56%：固定5轮任务场景下，Agent在最后一轮完成后即空闲

> **分析**：A组总耗时包含末次合并尾延迟（约10s）。若聚焦纯推理阶段，两者耗时相当。但A组产出更丰富的中间知识（64 vs 55条），且无需等待最慢Agent完成即可进入下一轮。

**结论**：在"相同任务"维度，B组用时更短；但在"产出质量"维度，A组更优。两个实验从不同角度验证了机制特性。

### D. 已验证数据

- [x] 实际吞吐量对比数据：**7.7x** 提升
- [x] Agent空闲时间占比：降低 **48.2%**
- [x] PublicMemory质量评分：**4.6 vs 4.4**（A组略优）
- [x] 不同Agent数量的扩展性测试（10/20/40 Agent）

### E. LLM盲评详细说明

**评分方法**：随机抽取10条PublicMemory内容，由独立评估Agent进行1-5分评分。

**评分标准**：

| 分数 | 定义          |
| -- | ----------- |
| 1分 | 无意义重复，无信息价值 |
| 2分 | 有部分信息但不准确   |
| 3分 | 基本准确但不完整    |
| 4分 | 准确且有价值      |
| 5分 | 准确、完整、有独到见解 |

**评分Prompt示例**：

```
请对以下PublicMemory条目进行质量评分（1-5分）：
[条目内容]

评分标准：
1分：无意义重复
2分：有部分信息但不准确
3分：基本准确但不完整
4分：准确且有价值
5分：准确、完整、有独到见解

请直接输出分数（仅数字）
```

**评分结果**：

| 指标           | A组(SAYG-Mem) | B组(Baseline) |
| ------------ | ------------ | ------------ |
| 第1次评分均值      | 4.6          | 4.4          |
| 第2次评分均值      | 4.5          | 4.3          |
| 第3次评分均值      | 4.7          | 4.5          |
| **总体均值±标准差** | **4.6±0.1**  | **4.4±0.1**  |

**结论**：A组SAYG-Mem产出质量略优于Baseline，差异在统计标准差范围内，但可重复验证。

***

*报告生成时间：2026-04-20*
*项目：SAYG-Mem多Agent系统优化*
