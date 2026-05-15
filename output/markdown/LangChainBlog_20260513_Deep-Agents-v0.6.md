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

# Deep Agents v0.6：新特性一览

> 原文：[New in Deep Agents v0.6](https://www.langchain.com/blog/deep-agents-0-6)
> 来源：LangChain Blog | 2026-05-13
> 作者：Sydney Runkle

---

## 索引

- [核心要点](#核心要点)
- [Code Interpreter](#code-interpreter)
- [模型无关的 PTC（Programmatic Tool Calling）](#模型无关的-ptcprogrammatic-tool-calling)
- [递归工作流](#递归工作流)
- [Harness Profiles](#harness-profiles)
- [Streaming](#streaming)
- [Delta Channels](#delta-channels)
- [ContextHub Backend](#contexthub-backend)
- [总结](#总结)

---

## 核心要点

- **在开源模型上跑生产级 agent** — Harness profiles 让你从 Kimi、Qwen、DeepSeek 等模型获得生产级性能，成本比闭源前沿 API 低 20 倍以上。
- **大幅削减 agent 基础设施成本** — Delta channels 将长时间运行 agent 的 checkpoint 存储减少最多 100 倍，不牺牲可观测性或弹性。
- **构建更丰富的实时 agent UI** — 新的 streaming 原语提供类型化、可订阅的事件投影，覆盖消息、工具调用和子 agent，从 runtime 一直到前端。

---

## Code Interpreter

我们在 Deep Agents 中发布了可安装的 code interpreter，给 agent 一个**可编程的工作空间**——可以转换数据、协调工具调用、把中间工作排除在模型上下文之外。

Agent 写代码来表达意图，然后内存中的 runtime 执行代码并返回相关结果。

沙箱是在环境上操作的代码优先方式（运行命令、安装依赖、编辑文件），而 interpreter 是在 **agent 循环内部**操作的代码优先方式：组合工具、保持状态、决定什么信息应该返回给模型。

```javascript
const topics = ["retrieval", "memory", "evaluation"];

const reports = await Promise.all(
  topics.map((topic) =>
    tools.task({
      description:
        `Research ${topic} in Deep Agents and return three concise findings.`,
      subagent_type: "general-purpose",
    }),
  ),
);

reports.join("\n\n");
```

---

## 模型无关的 PTC（Programmatic Tool Calling）

标准的工具调用循环让模型成为每一步的流量控制器：模型请求工具、在上下文中接收完整结果、推理该结果、重复。即使中间结果只是用来计算下一个输入，它仍然必须通过多次模型调用来链接。

**Programmatic Tool Calling (PTC)** 改变了这个工作流。模型写代码从执行 runtime 内部调用工具，工作流可以在不需要每次工具调用都往返模型的情况下运行。中间结果可以留在 runtime state 中，interpreter 可以过滤噪声输出、处理数据、重试失败，只把相关上下文返回给模型。

```javascript
const pages = await Promise.all(
  urls.map((url) => tools.fetchUrl({ url })),
);

const relevant = pages
  .filter((page) => page.includes("interpreter"))
  .slice(0, 3);

relevant.map((page) => page.slice(0, 500));
```

这种工具调用模式**减少 token 消耗**，减少不必要的模型往返，让 agent 的推理步骤更小。Anthropic 通过将其作为 API 行为添加到模型家族中来推广了这个模式，但有了 interpreter，任何 agent 用任何模型（包括开源模型）都能实现这一点。

---

## 递归工作流

Interpreter 让 agent 以更新颖的方式与 harness 交互。因为工具和子 agent 可以从代码中调用，agent 可以取一个子 agent 的输出、检查它、转换它，然后送入下一步——不需要把每个中间产出物都路由回主模型。

这使得**递归工作流**成为可能：agent 可以维护一个问题队列，对下一个问题调用子 agent，存储结果，从结果生成后续工作，直到有足够的证据来综合答案。

```javascript
const frontier = ["What changed in interpreter middleware?"];
const findings = [];

while (frontier.length && findings.length < 6) {
  const question = frontier.shift();
  const report = await tools.task({
    description:
      `Answer this question. If there is a useful next question, ` +
      `include it as "Follow-up: ..."\n\n${question}`,
    subagent_type: "general-purpose",
  });
  findings.push(report);
  const next = report.match(/Follow-up: (.*)/)?.[ 1];
  if (next) frontier.push(next);
}

findings.join("\n\n");
```

这与 Recursive Language Models (RLM) 背后的思想相邻：把工作状态保持在模型上下文之外，对选定的分支调用模型或子 agent，控制什么进入下一次模型调用。

安装方式：`deepagents[quickjs]`（Python）或 `@langchain/quickjs`（npm），作为 middleware 添加：

```python
from deepagents import create_deep_agent
from langchain_quickjs import REPLMiddleware

agent = create_deep_agent(
    model="baseten:zai-org/GLM-5",
    middleware=[REPLMiddleware()],
)
```

---

## Harness Profiles

Kimi K2.6、GLM 5.1、DeepSeek V4 等开源模型现在可以胜任生产级 agent 工作，成本通常比闭源前沿模型低 20 倍以上。但模型在不同的工具调用格式和 prompt 约定上做了 post-training，而大多数 harness 是针对作者构建时使用的闭源模型调优的。直接换上去，你可能只看到模型真实能力的一小部分——因为模型说的是 harness 不理解的"方言"。

这个差距是大的且可测量的。在我们自己的测试中，**仅 harness 层的变更**就把 gpt-5.2-codex 在 Terminal-Bench 2.0 上从 52.8% 提升到 66.5%（Top 30 → Top 5），gpt-5.3-codex 在 tau2-bench 上提升 20%，opus-4.7 提升 10%。在 tau2-bench 上，prompt 和 middleware 可以在不换模型的情况下移动 10-20 分。

"Harness"是模型周围的东西：基础 system prompt、工具及其描述、以及塑造每轮的 middleware。**Harness profile** 将这些 per-model 覆盖捕获为一个命名的、可版本化的单元。

DeepAgents v0.6 让 harness profiles 成为一等抽象。你可以 diff、版本化、和模型一起切换 profile，让调优工作可以延续。我们为主要模型提供内置 profiles，让强性能成为默认。

---

## Streaming

Agent 在返回最终答案之前做了大量工作。好的用户体验需要在工作发生时就展示出来，并让用户能够引导 agent。Streaming 是让这一切成为可能的原语。

新版本让 streaming 成为一等应用原语。通过 `stream_events(..., version="v3")`，agent 和 graph 现在发出统一的事件流，带有开发者实际想渲染的原语的人体工学投影：消息文本、推理块、工具调用、状态更新、子图、子 agent、自定义 channel 和最终输出。

```python
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "Research LangChain streaming"}]},
    version="v3",
)

for message in stream.messages:
    for delta in message.text:
        print(delta, end="", flush=True)

for subagent in stream.subagents:
    print(f"\n[{subagent.name}] {subagent.status}")
    for message in subagent.messages:
        for delta in message.text:
            print(delta, end="", flush=True)
```

这个 streaming 模型也通过新的 Agent Server 端点和 SDK 支持传输到网络上。前端方面，发布了 `@langchain/react`、`@langchain/vue`、`@langchain/svelte` 和 `@langchain/angular` 的 v1 框架集成。

---

## Delta Channels

Deep Agents 构建在 LangGraph runtime 上，每步 checkpoint agent 进度。随着 agent 变得更强大，它们运行更久、使用更多上下文，checkpoint 存储以 O(N²) 增长。

Delta channels 不再每步序列化全量快照，而是只存储 diff。对于一个模拟的 200 轮多文件 coding session：

- 无 delta channels：**5.27 GB** checkpoint 存储
- 有 delta channels：**129 MB**

根据对话长度和上下文大小，切换到 delta channels 可以合理地带来 **10-100 倍**的 checkpointer 存储缩减。

---

## ContextHub Backend

Context Hub 是 Deep Agents 的 LangSmith 支持的文件系统。它给你一个版本化的地方来存放塑造 agent 行为的文件，让 prompt、skills 和其他上下文的改进可以跨运行延续。

底层，agent 从 Hub repo 读取（也可以写入）。写入作为带历史、审查和环境标签的 commit 落地——你可以在 staging 中迭代，然后推到 production，无需搭建单独的存储层。

```python
from deepagents import create_deep_agent
from deepagents.backends import ContextHubBackend

agent = create_deep_agent(
    model="google_genai:gemini-3.1-pro-preview",
    backend=ContextHubBackend("my-agent"),
)
```

也可以只把 `/memories/` 路由到 Hub，其余保持线程作用域：

```python
from deepagents.backends import CompositeBackend, StateBackend, ContextHubBackend

agent = create_deep_agent(
    model="google_genai:gemini-3.1-pro-preview",
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": ContextHubBackend("my-agent"),
        },
    ),
)
```

---

## 总结

Deep Agents 五月版本的主线是**性能**：

- **Harness profiles**：从模型中榨取性能，解锁开源模型上的可行 agent 运行，成本是前沿 API 的零头
- **Code interpreter**：给 agent 更多自主权来编写和执行代码，帮助完成复杂任务并优化上下文窗口使用
- **Streaming**：支持高度并行化系统的订阅模型，覆盖工具和子 agent 进度
- **DeltaChannel**：支持长时间运行、长上下文 agent 的 checkpoint 存储原语
- **ContextHubBackend**：agent 行为文件的版本化家园，让一次运行的上下文改进可以延续到下一次

---
