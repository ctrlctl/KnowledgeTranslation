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

# 在后台运行 Subagent

> 原文：[Running Subagents in the Background](https://www.langchain.com/blog/running-subagents-in-the-background)
> 来源：LangChain Blog | 2026-04-16
> 作者：Hunter Lovell, Colin Francis

---

## 目录

- [传统 Subagent 在哪里崩溃](#传统-subagent-在哪里崩溃)
- [死锁：Supervisor 被阻塞](#死锁supervisor-被阻塞)
- [新信息难以协调](#新信息难以协调)
- [Async Subagent：后台运行](#async-subagent后台运行)
- [工作原理](#工作原理)
- [基于 Agent Protocol 构建](#基于-agent-protocol-构建)
- [如何在 Deep Agents 中使用](#如何在-deep-agents-中使用)

---

我们开始对 agent 提出更多要求——希望它们承担更长、更复杂的任务。在这个过程中，传统的 agent 编排方式开始出现裂缝。

LangChain 最近在 Deep Agents 中发布了 async subagent，来解决这个问题。这是一种让 agent 在后台运行委派工作的模式，它弥补了传统 agent 架构的一些不足。

---

## 传统 Subagent 在哪里崩溃

Subagent 是 supervisor agent 委派范围化工作的 agent。Subagent 从 supervisor 获取指令、访问相关工具、完成后返回摘要。这是一种**上下文工程模式**，在几乎所有构建的 agent 中都在采用，原因有两个：

- **Agent 在工作被拆分为更小任务时表现更好**——supervisor agent 理解问题、组织任务、协调执行者
- **小任务的所有信息并非都对大目标重要**——通过拆分为聚焦的独立 agent 运行，隐藏不必要的上下文

这个模式有效。但随着给 agent 更长更复杂的任务，内联 subagent 开始崩溃。

---

## 死锁：Supervisor 被阻塞

Subagent 通过给 supervisor agent 的工具调用。因为 agent 内部工具调用的工作方式，supervisor 在工具调用被 subagent 响应回答之前无法推理其他任何事。

当 subagent 被分配较小、低风险的任务时，这不是大问题。但现在我们给了 agent 更复杂的任务和工具（加上运行时间更长的模型），这个问题变得更加明显。**如果 subagent 花一小时，你必须等一小时才能再与 agent 交互。**

---

## 新信息难以协调

有几个信息通道对正在工作的 agent 很重要：

- **用户输入**——用户可能想在任务进行中引导 agent、添加上下文或改变优先级
- **其他工作的结果**——一个 subagent 的输出可能影响另一个 subagent 应该做什么
- **部分进展**——有时你想在任务完成前纠正一个走偏方向的任务

用内联 subagent，这些通道全部不可用。Supervisor 被阻塞，用户无法与它对话。Subagent 不能并发运行，所以没有结果的交叉授粉。Subagent 的轮次是全有或全无——没有办法发送中途更新或优雅地处理部分失败。Supervisor 发射 subagent 然后只能祈祷。

---

## Async Subagent：后台运行

一种简单的理解方式：async subagent 是在后台运行而非顺序执行的 subagent。不是等 subagent 完成才继续，supervisor 启动任务、立即获得 task ID、继续工作。它可以与用户对话、启动更多 subagent、或在问题的其他部分取得进展——同时工作在后台进行。

因为 subagent 是有状态的并维护自己的对话线程，supervisor 可以发送后续指令、中途纠正、或取消不再需要的工作。把它想成不是"发射后遗忘"，而是**"发射后引导"**。

---

## 工作原理

不是给 supervisor 每个 subagent 一个阻塞的工具调用，async subagent 给 supervisor 一组管理工具，更像任务队列：

| 工具 | 用途 |
|------|------|
| `start_async_task` | 在远程 agent 上启动任务，立即返回 task ID |
| `check_async_task` | 轮询任务状态，完成时获取结果 |
| `update_async_task` | 向运行中的任务发送后续指令 |
| `cancel_async_task` | 取消运行中的任务 |
| `list_async_tasks` | 列出所有跟踪的任务及其当前状态 |

Supervisor 在推理循环中自然使用这些工具——启动几个任务、回去和用户对话、检查进展、按需纠正。

**关键区别：** 传统 subagent 只是父 agent 的函数——共享进程、共享状态、只存在于 supervisor 的执行循环内。Async subagent 将它们视为独立的、可单独寻址的 agent。它们可以在自己的进程中运行、维护自己的状态、扩展到可能调用数百或数千个 subagent 的运行。

---

## 基于 Agent Protocol 构建

这种分离需要的不仅是进程内函数调用。Async subagent 基于 Agent Protocol 构建——一个框架无关的 API 规范，用于管理远程 agent。它定义了创建线程、启动运行、轮询状态、发送更新和管理长期记忆的标准端点。Supervisor 通过一致的接口管理异步工作所需的一切。

**关键好处是部署灵活性。** 你不锁定到任何单一托管平台。在 LangSmith 部署上运行 async subagent 获得托管体验，或在自己的基础设施上自托管。Supervisor 不关心 subagent 在哪里——发送任务、获得 task ID、通过相同标准接口管理生命周期。

---

## 如何在 Deep Agents 中使用

Deep Agents 是 LangChain 的通用 agent harness。添加 async subagent 只需把 async subagent spec 换入 `subagents` 列表——可以自由地与内联 subagent 混合搭配。

### 使用 LangSmith Deployment

定义 agent 并在 `langgraph.json` 中注册。因为 researcher 是独立 agent，supervisor 自动获得 async 管理工具：

```typescript
// agents.ts
import { createAgent } from "langchain";
import { createDeepAgent } from "deepagents";

export const researcher = createAgent({
  model: "anthropic:claude-sonnet-4-6",
  instructions: "Perform deep research on the given topic.",
  tools: [searchWeb, readUrl],
});

export const agent = createDeepAgent({
  model: "anthropic:claude-opus-4-6",
  subagents: [{
    name: "researcher",
    description: "Performs deep research on a topic.",
    graphId: "researcher",
  }],
});
```

```json
// langgraph.json
{
  "dependencies": ["."],
  "graphs": {
    "researcher": "./agents.ts:researcher",
    "agent": "./agents.ts:agent"
  }
}
```

Subagent 在自己的进程中运行、有自己的状态，supervisor 只是委派和回来检查。

### 自托管

如果你想完全控制 subagent 在哪里运行，可以自托管。Subagent 只需实现 Agent Protocol 端点，supervisor 通过 URL 而非 graph ID 连接：

```typescript
export const agent = createDeepAgent({
  model: "anthropic:claude-opus-4-6",
  subagents: [{
    name: "researcher",
    description: "Performs deep research on a topic.",
    graphId: "researcher",
    url: "http://localhost:2024",  // 指向你的自托管服务器
  }],
});
```

自托管服务器实现 Agent Protocol 端点（创建线程、启动运行、轮询状态、取消任务），可以运行在任何地方——Docker 容器、VM、你自己的 Kubernetes 集群。LangChain 有一个完整的自托管示例，包括 Hono 服务器、Postgres 支持的状态和 Docker Compose 设置，可以作为起点。
