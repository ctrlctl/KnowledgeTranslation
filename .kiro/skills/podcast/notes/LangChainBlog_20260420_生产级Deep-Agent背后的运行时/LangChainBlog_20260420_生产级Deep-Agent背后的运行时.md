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

# The Runtime Behind Production Deep Agents：生产级 Deep Agent 背后的运行时

> 原文：[Runtime Behind Production Deep Agents](https://www.langchain.com/blog/runtime-behind-production-deep-agents)
> 来源：LangChain Blog | 2026-04-20
> 作者：Sydney Runkle, Vivek Trivedy

---

## 目录

- [Harness vs Runtime](#harness-vs-runtime)
- [持久执行（Durable Execution）](#持久执行durable-execution)
- [记忆](#记忆)
- [多租户](#多租户)
- [Human-in-the-Loop](#human-in-the-loop)
- [实时交互：Streaming 与 Double-texting](#实时交互streaming-与-double-texting)
- [Guardrails：中间件](#guardrails中间件)
- [可观测性](#可观测性)
- [Time Travel](#time-travel)
- [代码执行与沙箱](#代码执行与沙箱)
- [集成：MCP、A2A、Webhooks](#集成mcpa2awebhooks)
- [Cron：定时任务](#cron定时任务)
- [开放 Harness](#开放-harness)

---

## Harness vs Runtime

要构建好的 agent，你需要好的 harness。要**部署**那个 agent，你需要好的 runtime。

- **Harness**：围绕模型构建的系统——prompt、工具、skill，以及支持模型和 tool calling 循环的一切
- **Runtime**：底层的一切——持久执行、记忆、多租户、可观测性——让 agent 在生产中持续运行而无需团队重新发明

| 生产需求 | Runtime 能力 |
|----------|-------------|
| 可靠性 | 持久执行 |
| 记忆 | Checkpoint（短期）、Store（长期） |
| 护栏 | 中间件 |
| 多租户 | 认证、授权、Agent Auth、RBAC |
| 人类监督 | Human-in-the-loop（中断/恢复） |
| 实时交互 | Streaming、并发控制（double-texting） |
| 可观测性 | Tracing、time travel |
| 代码执行 | 沙箱 |
| 集成 | MCP、A2A、webhooks |
| 定时任务 | Cron |

---

## 持久执行（Durable Execution）

Agent 通过运行循环工作：给定 prompt，模型推理、调用工具、观察结果、重复直到完成。与毫秒级返回的典型 web 请求不同，这个循环可以跨越数分钟或数小时。

两个核心问题：

1. **长运行需要在基础设施故障中存活。** 一个花 20 分钟收集资料和综合发现的研究 agent，不能因为 worker 进程死亡就从头开始——agent 已经为 token 付了费并执行了 tool call。需要从最后完成的步骤恢复，所有先前状态完整。

2. **Agent 需要能够停下来等待。** 暂停等人类批准交易的 agent 不知道人类会在 30 秒还是 3 天后响应。为此占用 worker 进程或客户端连接不可行。Agent 需要真正停止：释放资源、释放 worker，然后在恢复时精确地从停止处继续。

**解决方案：** Agent 在带有自动 checkpoint 的托管任务队列上运行。每个图执行的 super-step 将 checkpoint 写入持久层（默认 PostgreSQL），以 `thread_id` 为键。Worker 崩溃时，运行的租约被释放，另一个 worker 从最新 checkpoint 接手。

**持久性是其他一切的基础。** 因为执行可以跨进程边界暂停和恢复，agent 可以无限期等待人类输入、在后台运行、在部署中存活、处理并发输入而不损坏状态。

---

## 记忆

Agent 需要两种不同的记忆：

**短期记忆：** 单次对话中积累的内容——交换的消息、tool call、跨运行构建的中间状态。存在于线程的 checkpoint 中，作用域为 `thread_id`，对话结束时（概念上）消失。

**长期记忆：** 跨对话携带的内容——跨对话学到的用户偏好、项目惯例和最佳实践、随每次查询增强的知识库。不属于任何单个线程，是用户级或组织级上下文。Checkpoint 无法做到这一点，因为 checkpoint 状态作用域为单个线程。

长期记忆使用 key-value 接口，记忆按命名空间元组组织（如 `(user_id, "memories")`），跨线程持久化。默认由 PostgreSQL 支持，支持通过 embedding 配置进行语义搜索。

**关键点：** 数月积累的记忆是系统产出的最有价值数据。它存在哪里很重要。将数据保持在你控制的标准格式中，才能在模型之间迁移、分析它、或在 agent 之外构建。

---

## 多租户

Agent 服务多个用户时出现三个问题：

1. **隔离用户数据：** 自定义认证作为中间件在每个请求上运行，验证凭证并返回用户身份和权限。授权处理器强制谁能看到或修改什么。

2. **让 agent 代表用户行动：** Agent 经常需要用用户凭证调用第三方服务。Agent Auth 处理 OAuth 流程和 token 存储——用户认证一次，agent 可以在后续运行中代表他们行动。

3. **控制谁能操作系统本身：** RBAC 处理操作者级别的访问控制——哪些团队成员可以部署 agent、配置它们、查看 trace 或更改认证策略。

---

## Human-in-the-Loop

两种常见场景：

**审查提议的 tool call：** 在 agent 执行后果性操作（发邮件、执行金融交易、删除文件）之前，人类看到它即将做什么并决定如何响应——批准、编辑后发送、或拒绝并给出修改请求。

**Agent 提出澄清问题：** Agent 到达无法自行解决的决策点——不是因为缺少工具，而是因为正确答案取决于人类判断。Agent 直接提出问题，人类的回答成为中断的返回值，agent 从停止处继续。

实现：`interrupt()` 暂停执行并向调用者展示 payload；`Command(resume=...)` 用人类的响应继续。`interrupt()` 是动态的——可以放在代码任何位置、包在条件中、或嵌入工具函数内。恢复接受任何 JSON 可序列化值——不限于批准/拒绝，审查者可以返回编辑后的草稿、人类可以提供缺失上下文。

---

## 实时交互：Streaming 与 Double-texting

**Streaming：** 部分输出在 agent 产出时流向客户端。支持多种模式：每个图步骤后的完整状态快照、仅状态更新、逐 token LLM 输出、或自定义应用事件。线程 streaming 支持通过 `Last-Event-ID` header 恢复——客户端重连时从最后收到的事件重放，无间隙。

**Double-texting：** 用户在 agent 仍在处理上一条消息时发送新消息。四种策略：

- **enqueue**（默认）：新输入等当前运行完成后顺序处理
- **reject**：拒绝任何新输入直到当前运行完成
- **interrupt**：停止当前运行、保留进度、从该状态处理新输入
- **rollback**：停止当前运行、回滚所有进度、将新消息作为全新运行处理

---

## Guardrails：中间件

有些生产关注点不能表达为"持久地运行循环"，而必须塑造循环本身。这些策略属于代码而非 prompt——需要每次都运行，而非模型碰巧记住时才运行。

两个具体案例：

- **在模型看到之前编辑敏感数据：** 客服 agent 处理包含 PII 的用户消息，需要在每次模型调用前确定性地编辑。
- **限制昂贵操作：** 调用付费外部 API 的 agent 需要每次运行的硬上限。

通过中间件处理，在定义的 hook 处包裹 agent 循环——`before_model`、`wrap_model_call`、`wrap_tool_call`、`after_model`。内置中间件包括 PII 编辑、模型重试、模型降级、工具调用限制、摘要、HITL、内容审核等。

---

## 可观测性

你不知道 agent 在生产中会做什么直到运行它。与传统应用不同，agent 的执行路径取决于模型在运行时的选择。出问题时，你不能只重读函数——需要看到实际发生了什么。

每个部署自动连接到 tracing 项目。开箱即用获得完整执行树——模型调用、工具调用、subagent 运行、中间件 hook——带有可按用户、时间窗口、成本、延迟、错误状态、反馈或自定义标签查询的结构化元数据。

Trace 是改进循环的基础：AI 助手分析 trace 并浮现洞察，Online Eval 自动对生产 trace 运行评分器以捕获回归。

---

## Time Travel

可观测性告诉你发生了什么。Time travel 让你问"如果某些事情不同会怎样"。

因为每个 super-step 写一个 checkpoint，运行历史中的每个点都已经是可以返回的快照。选择线程历史中的一个 checkpoint，可选地修改其状态，从那里恢复。修改后的 checkpoint 分叉线程历史——原始保持完整，新路径作为自己的分支向前运行。

解锁的模式：调试为什么 agent 选了工具 A 而非 B、对比两个 prompt 在相同上游上下文下的表现、通过回退到最后好的状态从偏离的运行中恢复、探索反事实。

---

## 代码执行与沙箱

能运行任意代码的 agent 是通用的——可以安装依赖、克隆仓库、执行测试、运行数据分析。这是"带函数调用的聊天机器人"和"能真正做事的 agent"之间的差距。

任意代码执行需要隔离。通过沙箱后端实现——配置实现 `SandboxBackendProtocol` 的后端时，harness 自动添加 execute 工具。

**Auth proxy 模式：** Agent 需要调用认证 API，但把凭证放在沙箱内是安全风险。Proxy 作为 sidecar 运行，拦截出站请求，从 workspace secrets 自动注入凭证。Secret 永远不进入沙箱。

**安全提醒：** 沙箱保护你的主机，不保护沙箱本身。通过 prompt injection 控制 agent 输入的攻击者可以在沙箱内运行命令。沙箱让攻击者远离你的机器，但沙箱内的任何东西都是暴露的。

---

## 集成：MCP、A2A、Webhooks

- **MCP**：连接 agent 到工具和数据源的开放标准。每个部署自动暴露 MCP 端点。
- **A2A**：agent 间通信的标准。每个部署自动暴露 A2A 端点，使跨部署的多 agent 架构可行。
- **Webhooks**：agent 完成运行时触发下游操作——无需轮询。

---

## Cron：定时任务

很多有价值的 agent 工作是主动的——按计划发生，无人触发。

两种模式：

- **Sleep-time compute：** Agent 在空闲期做有用工作。夜间研究 agent 追踪新论文、准备 agent 审查明天日历并起草简报、分类 agent 对隔夜支持工单分类。
- **健康和监控循环：** Agent 定期检查某些东西并在发现问题时行动或升级。

两种风格：
- **有状态 cron**：绑定到特定 `thread_id`，每次触发的运行追加到同一对话——适合需要看到自己历史的 agent
- **无状态 cron**：每次执行启动新线程——适合不需要运行间连续性的批处理工作

---

## 开放 Harness

Agent 基础设施中有一个趋势：转向托管解决方案时伴随着构建者选择的减少——锁定到单一模型提供商、封闭 harness、或隐藏在 API 后面的 harness 功能。

Deep Agents 的设计避免这一点：harness 是 MIT 许可的完全开源，agent 指令使用 `AGENTS.md`（开放标准），agent 通过开放协议暴露——MCP、A2A、Agent Protocol。没有模型或沙箱锁定，harness 没有黑箱。
