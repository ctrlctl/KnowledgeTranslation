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

**索引**

- [传统Subagent在哪里崩溃](#传统subagent在哪里崩溃)
- [异步Subagent登场](#异步subagent登场)
- [工作原理](#工作原理)
- [基于Agent Protocol构建](#基于agent-protocol构建)
- [在Deep Agents中使用异步Subagent](#在deep-agents中使用异步subagent)

---

**要点：**

- 内联subagent在任务期间阻塞supervisor agent。因为agent循环中的tool call是同步的，supervisor在subagent完成之前无法响应用户、协调其他工作或纠正方向——当任务需要一小时或更长时间时，这是个真正的问题。
- **异步subagent立即返回task ID**，supervisor保持控制。Supervisor可以并行启动多个subagent、继续与用户对话、发送任务中更新、或取消不再需要的工作——更像是"发射并引导"而非"发射后不管"。
- 异步subagent基于**Agent Protocol**构建，不锁定在单一部署上。它们作为完全独立的agent运行，有自己的进程和状态，可以托管在LangSmith部署上或自托管在你自己的基础设施上。

---

## 传统Subagent在哪里崩溃

Subagent是supervisor agent将范围化工作委派给的agent。Subagent从supervisor获取指令、访问相关工具，完成后返回摘要。这是一种上下文工程模式，我们在构建的几乎所有agent中都在采用，原因有二：

- Agent在工作被拆分为更小任务时表现更好——supervisor理解问题、组织任务、然后协调执行者
- 不是小任务的所有信息都对大目标重要——通过拆分为聚焦的、独立的agent运行，我们对supervisor隐藏了不必要的上下文

这个模式有效。但随着我们给agent更长更复杂的任务，内联subagent开始崩溃。

### Agent在subagent工作时被死锁

Subagent通过给supervisor的工具调用，由于agent内部tool calling的工作方式，supervisor在tool call被subagent响应回答之前无法推理其他任何事情。当subagent被分配较小的低风险任务时这不是大问题。但现在我们给了agent更复杂的任务和工具（加上运行时间更长的模型），这变得更加明显。**如果subagent需要一小时，你必须等一小时才能再次与agent交互。**

### 新信息难以协调

有几个信息通道对工作中的agent很重要：

- **用户输入**——用户可能想在任务进行中引导agent、添加上下文或改变优先级
- **其他工作的结果**——一个subagent的输出可能影响另一个subagent接下来应该做什么
- **部分进度**——有时你想在任务完成前纠正一个走偏方向的任务

使用内联subagent时，这些通道都不可用。Supervisor被阻塞，用户无法与之对话。Subagent不能并发运行，所以没有结果的交叉传播。Subagent的轮次是全有或全无的——没有办法发送任务中更新或优雅地处理部分失败。Supervisor发射subagent然后只能祈祷。

---

## 异步Subagent登场

一种简单的理解方式：异步subagent是在后台运行而非顺序运行的subagent。Supervisor启动任务，立即获得task ID，然后继续工作，而不是等subagent完成才继续。它可以与用户对话、启动更多subagent、或在后台工作进行时推进问题的其他部分。

因为subagent是有状态的并维护自己的对话线程，supervisor可以发送后续指令、在任务中纠正方向、或取消不再需要的工作。把它想成不是"**fire-and-forget**"而是"**fire-and-steer**"。

---

## 工作原理

异步subagent不是给supervisor每个subagent一个阻塞的tool call，而是给supervisor一组管理工具，更像一个任务队列：

| 工具 | 用途 |
|------|------|
| `start_async_task` | 在远程agent上启动任务，立即返回task ID |
| `check_async_task` | 轮询任务状态，完成时获取结果 |
| `update_async_task` | 向运行中的任务发送后续指令 |
| `cancel_async_task` | 取消运行中的任务 |
| `list_async_tasks` | 列出所有跟踪的任务及其当前状态 |

Supervisor在推理循环中自然地使用这些工具——它可以启动几个任务、回去与用户对话、检查进度、按需纠正方向。

传统subagent实际上只是父agent的一个函数——它们共享进程、共享状态，只存在于supervisor的执行循环内。异步subagent将它们视为完全独立的、可单独寻址的agent。它们可以在自己的进程中运行、维护自己的状态，并扩展到可能调用数百或数千个subagent的运行。

---

## 基于Agent Protocol构建

这种分离需要的不仅仅是进程内函数调用。异步subagent基于**Agent Protocol**构建——一个框架无关的API规范，用于管理远程agent。它定义了创建线程、启动运行、轮询状态、发送更新和管理长期记忆的标准端点。

关键好处是**部署灵活性**。你不被锁定在任何单一托管平台上。在LangSmith部署上运行异步subagent获得托管体验，或在自己的基础设施上自托管。Supervisor不关心subagent在哪里。它发送任务、获得task ID，通过相同的标准接口管理生命周期。

---

## 在Deep Agents中使用异步Subagent

Deep Agents是我们的通用agent harness。添加异步subagent只需将异步subagent规格换入subagents列表——你可以自由地将它们与内联subagent混合搭配。

**使用LangSmith Deployment：**

```typescript
// agents.ts
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

Subagent在自己的进程中运行，有自己的状态，supervisor只是委派和回来检查。

**自托管：**

如果你想完全控制subagent运行的位置，可以自托管。Subagent只需实现Agent Protocol端点，supervisor通过URL而非graph ID连接到它：

```typescript
export const agent = createDeepAgent({
  model: "anthropic:claude-opus-4-6",
  subagents: [{
    name: "researcher",
    description: "Performs deep research on a topic.",
    graphId: "researcher",
    url: "http://localhost:2024", // 指向你的自托管服务器
  }],
});
```

自托管服务器实现Agent Protocol端点，可以运行在任何地方——Docker容器、VM、你自己的Kubernetes集群。
