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

# Running Subagents in the Background：在后台运行 Subagent

> 原文：[Running Subagents in the Background](https://www.langchain.com/blog/running-subagents-in-the-background)
> 来源：LangChain Blog | 2026-04-16
> 作者：Hunter Lovell, Colin Francis

---

## 目录

- [传统 Subagent 的问题](#传统-subagent-的问题)
- [Async Subagent：后台运行](#async-subagent后台运行)
- [工作原理](#工作原理)
- [基于 Agent Protocol 构建](#基于-agent-protocol-构建)

---

## 传统 Subagent 的问题

Subagent 是 supervisor agent 委派范围化工作的 agent。Supervisor 理解问题、组织任务、协调执行者。这是一种上下文工程模式——通过拆分为聚焦的独立 agent 运行，隐藏不必要的上下文。

但随着任务变长变复杂，**内联 subagent 开始崩溃**：

### 死锁

Subagent 通过给 supervisor 的工具调用。因为 agent 循环中工具调用是同步的，supervisor 在 subagent 响应前无法推理其他任何事。如果 subagent 花一小时，你必须等一小时才能再与 agent 交互。

### 新信息难以协调

三个重要信息通道在内联模式下全部不可用：

- **用户输入：** 用户可能想在任务进行中引导 agent、添加上下文或改变优先级
- **其他工作的结果：** 一个 subagent 的输出可能影响另一个 subagent 应该做什么
- **部分进展：** 有时你想在任务完成前纠正方向

Supervisor 发射 subagent 然后只能祈祷。

---

## Async Subagent：后台运行

Async subagent 在后台运行而非顺序执行。Supervisor 启动任务，立即获得 task ID，继续工作。它可以与用户对话、启动更多 subagent、或在其他部分取得进展。

因为 subagent 是有状态的并维护自己的对话线程，supervisor 可以发送后续指令、中途纠正、或取消不再需要的工作。

**不是"发射后遗忘"，而是"发射后引导"。**

---

## 工作原理

Async subagent 给 supervisor 一组管理工具，像任务队列一样工作：

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

这种分离需要的不仅是进程内函数调用。Async subagent 基于 **Agent Protocol** 构建——一个框架无关的 API 规范，用于管理远程 agent。它定义了创建线程、启动运行、轮询状态、发送更新和管理长期记忆的标准端点。

**关键好处是部署灵活性：** 不锁定到任何单一托管平台。在 LangSmith 部署上运行获得托管体验，或在自己的基础设施上自托管。Supervisor 不关心 subagent 在哪里——发送任务、获得 task ID、通过相同标准接口管理生命周期。
