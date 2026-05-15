<style>
body, .markdown-body {
  font-family: "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, serif;
  font-size: 15px;
  line-height: 2;
  max-width: 38em;
  margin: 0 auto;
  padding: 2em;
  color: #2c2c2c;
  background: #faf8f5;
}
</style>

# Delta Channels：为长时间运行的 Agent 演进 Runtime

> 原文：[Delta Channels: Evolving our Runtime for Long-Running Agents](https://www.langchain.com/blog/delta-channels-evolving-agent-runtime)
> 来源：LangChain Blog | 2026-05-12
> 作者：Sydney Runkle

---

## 索引

- [核心要点](#核心要点)
- [问题：O(N²) 的 Checkpoint 存储](#问题on²-的-checkpoint-存储)
- [解决方案：Delta Channels](#解决方案delta-channels)
- [Benchmark 结果](#benchmark-结果)
- [API](#api)
- [Reducer 契约：跨 fold 的结合律](#reducer-契约跨-fold-的结合律)
- [从 pre-delta 线程迁移](#从-pre-delta-线程迁移)
- [下一步](#下一步)

---

## 核心要点

- 默认的全量快照模型下，checkpoint 存储以 **O(N²)** 增长——对于消息历史很长、使用文件系统做上下文的 agent，这很快就变成真实的运维成本。
- `DeltaChannel` 每步只存储 delta，每隔 K 步写一次全量快照，在控制恢复延迟的同时让存储成本随 session 增长保持平坦。
- 升级是透明的：现有线程继续工作，`messages` 和 `files` 在 Deep Agents v0.6 中默认使用 delta 存储，LangGraph 的完整 API 面（interrupts、time-travel、tooling）不变。

---

Deep Agents 构建在 LangGraph runtime 之上，每一步都会 checkpoint agent 的进度。这正是 observability、human-in-the-loop 和故障恢复得以实现的基础：你始终知道 agent 在哪里，可以从任何点恢复。

随着 agent 能力增强：

1. 它们运行得更久，消息历史跨越数十甚至数百步
2. 它们使用更多上下文，利用文件系统做上下文管理和卸载

对于 Deep Agents，消息历史和文件都存在 agent state 中。在每步快照的方式下，checkpoint 存储以 **O(N²)** 增长。一个跑 200 轮的 coding agent，当前的 checkpointing 方法会序列化 5.3GB 到 checkpointer。Delta channels 把它降到 129 MB——**超过 40 倍的缩减**，state 恢复性能几乎没有下降。

Delta channels 是我们演进 runtime 以跟上需求的方式。`DeltaChannel` 是 `langgraph 1.2` 中的新原语，改变了累积型 state 字段的 checkpoint 方式。不再每步序列化全量快照，而是每步只存储 diff。全量快照周期性写入以限制恢复成本。对 Deep Agents 来说，这意味着 `messages` 和 `files` 使用基于 delta 的存储。你仍然拥有 agent 进度的完整历史，只是成本降低了一个数量级。

---

## 问题：O(N²) 的 Checkpoint 存储

LangGraph 默认的 checkpointing 模型在每一步写入 agent state 的全量快照。对于小型、短命的 agent 这没问题。但 `messages` 和 `files` 是**只追加的累加器**——它们只会增长。

在全量快照 checkpointing 下，checkpoint N 包含步骤 1 到 N 的所有内容：

![](images/fig_12.png)

增长在 checkpoint 层复合：每一步序列化的数据比上一步更多，写入更大的 blob 到 checkpointer，消耗更多内存来持有它。你在序列化时间、写放大和冗余存储上都在付出代价。

---

## 解决方案：Delta Channels

Channel 是 LangGraph 中用来表示 graph state 中"字段"的原语。不同的 channel 类型控制数据如何通过 checkpoint 传递。

`DeltaChannel` 是 LangGraph 的新 channel 类型（1.2 版本 beta），改变了累积型字段的 checkpoint 表示。

在普通步骤中，`DeltaChannel` **只写入该步新增的更新**——一个很小的 delta。

全量快照每 `snapshot_frequency=K` 步写入一次（`deepagents` 默认 50）。这限制了恢复时重建 state 的成本：runtime 不需要从 session 开始重放每一个 delta 写入，只需要回溯到最近的快照——最多 K 步。没有周期性快照的话，一个很长的 session 意味着很慢的恢复。

![](images/fig_13.png)

底层增长仍然是二次的（因为快照每 K 步发生一次），但系数是基线的 ~1/K。在实际 session 长度下，O(N) 的 delta 项占主导，而且因为重建成本被 K 限制，恢复延迟保持平坦。存储收益实际上是免费的。

下面是标准快照方式 vs delta 方式的对比：

![](images/fig_14.png)

---

## Benchmark 结果

`DeltaChannel` 是 LangGraph 原语，但驱动它的工作负载——也是我们在这里做 benchmark 的——是 Deep Agents 的 coding session。长消息历史和文件系统支持的上下文卸载，正是 O(N²) checkpoint 增长成为真实运维问题的 state 形态。

我们跑了两个工作负载：

| | Workload A | Workload B |
|---|---|---|
| 场景 | 轻量 coding / 搜索 agent | 多文件功能实现 |
| 文件写入 / 轮 | 1 × 1 KB | 2 × 8 KB |
| 搜索结果 / 轮 | 1 × 1 KB | 1 × 5 KB |
| 大型搜索结果 | 82 KB 每 10 轮 | 100KB 每 5 轮 |
| AI 响应 / 轮 | 最小 | ~200 tokens |

周期性的大型搜索结果超过了 FilesystemMiddleware 的 20k-token 驱逐阈值，从 `messages` 卸载到 `files`。

### 方法论

所有 benchmark 使用完全 mock 的工作负载——没有真实 LLM 调用，`InMemorySaver`，确定性 mock 模型，完全可复现。表格报告的是**总 checkpointer 存储**：整个 session 中 saver 累积的所有字节。Token 计数使用 `total_message_chars / 4` 近似，这是 `FilesystemMiddleware` 内部用于驱逐阈值的方式。

设置如下：

```python
checkpointer = InMemorySaver()
agent = create_deep_agent(
    model=_MockModel(),   # 确定性 mock，无 API 调用
    tools=[external_search],
    checkpointer=checkpointer,
)
for i in range(turns):
    agent.invoke({"messages": [HumanMessage(...)]}, config)
```

### Workload A：轻量 coding 和搜索

存储一开始增长缓慢，然后随着全量快照大小复合而急剧加速。在 500 轮时基线累积了 4 GB；delta channels 保持在 110 MB 以下。

![](images/fig_15.png)

节省比从 10 轮时的 6× 增长到 500 轮时的 41×——仍在攀升，但随着接近理论上的 ~K× 上限而减速。这个上限不是固定的：`snapshot_frequency` 可配置，你可以根据工作负载在恢复延迟和存储节省之间权衡。更高的 K 意味着每个 session 更少的全量写入和更高的存储缩减，代价是恢复时稍多的 delta 重放。

![](images/fig_16.png)

### Workload B：多文件 coding session

更重的每轮 state 意味着 O(N²) 曲线更快变陡。基线在仅 200 轮时就达到 5.3 GB——一个现实的下午 agent 工作量。

![](images/fig_17.png)

节省比在 200 轮时达到 41× 且仍在攀升——两个工作负载收敛到相同的 ~K× 渐近线，但更重的工作负载更快到达，因为更大的每轮写入更激进地放大了二次系数。

![](images/fig_18.png)

---

## API

### 在 Deep Agents 中

Delta channels 在 `deepagents v0.6` 中默认开启。`messages` 和 `files` 都使用 delta-channel 存储。无需配置。

### 在 LangGraph 中

`DeltaChannel` 是 LangGraph 中的一等原语，你可以用于任何 state 字段。

```python
from typing_extensions import Annotated
from langgraph.channels.delta import DeltaChannel

def append(state: list[str], writes: list[list[str]]) -> list[str]:
    return state + [item for batch in writes for item in batch]

class MyAgentState(TypedDict):
    items: Annotated[list[str], DeltaChannel(reducer=append, snapshot_frequency=50)]
```

两个参数：

- **`reducer`** — 一个纯函数 `(state, list[writes]) -> new_state`，必须满足 batching-invariance：`reducer(reducer(s, xs), ys) == reducer(s, xs + ys)`。见下方 reducer 契约。
- **`snapshot_frequency`** — 多久写一次全量快照（默认 1000）。更高的值意味着每个 session 更少的全量写入但恢复时更多的 delta 重放。`deepagents` 使用 50。

这就是全部的 API 变更面。现有的工具、interrupt 处理和 time-travel 都继续工作。

---

## Reducer 契约：跨 fold 的结合律

`DeltaChannel` 对 reducer 施加了比旧的 `BinaryOperatorAggregate` channel 更严格的要求。这是定义自己的 delta-backed state 时唯一需要做对的事情。

**旧契约：**

```python
def reducer(existing: T, update: T) -> T: ...
```

**新契约：**

```python
# Batch fold — 一次性传入所有累积的写入
def reducer(state: T, writes: list[T]) -> T: ...
```

`DeltaChannel` 将自上次加载以来累积的所有写入在一次调用中传入。重建的结果必须与这些写入如何分批无关：

```python
reducer(reducer(state, [w1, w2]), [w3, w4]) == reducer(state, [w1, w2, w3, w4])
```

这叫做 **batching-invariance**（批处理不变性）。如果你的 reducer 违反了它，delta channel state 会与全量快照产生分歧——静默地，而且只在跨越快照边界的 session 中才会出现。

---

## 从 pre-delta 线程迁移

无需数据迁移。当 `DeltaChannel.from_checkpoint` 遇到一个普通 state 值（不是 `_DeltaSnapshot`）时，它直接将其作为基础 state 使用。现有线程继续工作——升级后的第一个新 checkpoint 开始在该普通值种子之上写入 delta。

---

## 下一步

Delta channels 随 `deepagents v0.6` 和 `langgraph v1.2` 发布。升级路径应该是无缝的。

Delta channels 带来的收益随着 session 变长而复合。长时间运行、具有深度上下文的 agent 是这个领域的方向，而 delta channels 是我们的 runtime 扩展以满足其需求的方式。

---
