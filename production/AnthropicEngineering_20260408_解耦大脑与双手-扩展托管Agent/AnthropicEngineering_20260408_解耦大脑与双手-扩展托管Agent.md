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

# 解耦大脑与双手：扩展托管 Agent

> 原文：[Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents)
> 来源：Anthropic Engineering | 2026-04-08
> 作者：Lance Martin, Gabe Cemaj, Michael Cohen

---

## 索引

- [为什么需要 Managed Agents](#为什么需要-managed-agents)
- [耦合架构的问题：宠物 vs 牲畜](#耦合架构的问题宠物-vs-牲畜)
- [解耦：大脑、双手与 Session](#解耦大脑双手与-session)
- [Session 作为上下文对象](#session-作为上下文对象)
- [扩展：多大脑与多双手](#扩展多大脑与多双手)
- [Meta-Harness 设计哲学](#meta-harness-设计哲学)

---

工程博客上一个持续的话题是如何构建有效的 agent 和设计长时间运行工作的 harness。贯穿这些工作的共同线索是：**harness 编码了关于 Claude 不能自己做什么的假设**。然而，这些假设需要经常质疑，因为随着模型改进它们会过时。

例如，在之前的工作中我们发现 Claude Sonnet 4.5 在感知到 context 限制接近时会过早收尾任务——一种有时被称为"context anxiety"的行为。我们通过在 harness 中添加 context reset 来解决。但当我们在 Claude Opus 4.5 上使用相同的 harness 时，发现这种行为已经消失了。Reset 变成了死重。

我们预期 harness 会持续演进。所以我们构建了 **Managed Agents**：Claude Platform 中的托管服务，通过一组旨在比任何特定实现更持久的接口，代你运行长周期 agent——包括我们今天运行的那些。

构建 Managed Agents 意味着解决计算中的一个老问题：如何为"尚未想到的程序"设计系统。几十年前，操作系统通过将硬件虚拟化为抽象——process、file——解决了这个问题，这些抽象足够通用，适用于尚不存在的程序。抽象比硬件更持久。`read()` 命令不关心它访问的是 1970 年代的磁盘包还是现代 SSD。

Managed Agents 遵循相同的模式。我们虚拟化了 agent 的组件：**session**（所有发生事件的 append-only 日志）、**harness**（调用 Claude 并将 Claude 的 tool call 路由到相关基础设施的循环）、**sandbox**（Claude 可以运行代码和编辑文件的执行环境）。这允许每个的实现被替换而不干扰其他。

---

## 耦合架构的问题：宠物 vs 牲畜

我们最初将所有 agent 组件放入单个容器，session、agent harness 和 sandbox 共享环境。这有好处：文件编辑是直接的 syscall，没有服务边界需要设计。

但通过将所有东西耦合到一个容器中，我们遇到了一个老的基础设施问题：我们养了一只**宠物**。在 pets-vs-cattle（宠物 vs 牲畜）的类比中，宠物是你不能承受失去的、需要精心照料的个体，而牲畜是可互换的。在我们的案例中，服务器变成了那只宠物；如果容器失败，session 就丢失了。如果容器无响应，我们不得不把它护理回健康状态。

护理容器意味着调试无响应的卡住 session。我们唯一的窗口是 WebSocket 事件流，但它无法告诉我们故障在哪里产生——harness 中的 bug、事件流中的丢包、容器离线都呈现相同的表象。

第二个问题是 harness 假设 Claude 工作的东西与它在同一个容器中。当客户要求我们将 Claude 连接到他们的 VPC 时，他们不得不将网络与我们对等互联，或在自己的环境中运行我们的 harness。

---

## 解耦：大脑、双手与 Session

我们到达的解决方案是将"**大脑**"（Claude 和它的 harness）与"**双手**"（执行操作的 sandbox 和工具）以及"**session**"（session 事件日志）解耦。每个变成一个对其他做很少假设的接口，每个可以独立失败或被替换。

**Harness 离开容器。** 解耦大脑与双手意味着 harness 不再住在容器内。它像调用任何其他工具一样调用容器：`execute(name, input) → string`。容器变成了**牲畜**。如果容器死了，harness 将失败作为 tool-call 错误捕获并传回 Claude。如果 Claude 决定重试，新容器可以用标准配方重新初始化：`provision({resources})`。我们不再需要把失败的容器护理回健康。

**从 harness 失败中恢复。** Harness 也变成了牲畜。因为 session 日志在 harness 外面，harness 中没有东西需要在崩溃中存活。当一个失败时，新的可以用 `wake(sessionId)` 重启，用 `getSession(id)` 取回事件日志，从最后一个事件恢复。

**安全边界。** 在耦合设计中，Claude 生成的任何不受信任的代码都在与凭证相同的容器中运行——所以 prompt injection 只需要说服 Claude 读取自己的环境。结构性修复是确保 token 永远不可从 Claude 生成代码运行的 sandbox 中到达。对于 Git，我们在 sandbox 初始化期间用仓库的访问 token 克隆 repo 并连接到本地 git remote。对于自定义工具，我们支持 MCP 并将 OAuth token 存储在安全保险库中。

---

## Session 作为上下文对象

长周期任务经常超出 Claude 的 context window 长度，标准的解决方式都涉及关于保留什么的不可逆决策。但选择性保留或丢弃上下文的不可逆决策可能导致失败——很难知道未来的 turn 需要哪些 token。

在 Managed Agents 中，session 充当一个**活在 Claude context window 之外的上下文对象**。但不是存储在 sandbox 或 REPL 中，上下文被持久存储在 session 日志中。接口 `getEvents()` 允许大脑通过选择事件流的位置切片来查询上下文。接口可以灵活使用：大脑可以从上次停止阅读的地方继续、在特定时刻前倒回几个事件查看前因、或在特定操作前重新阅读上下文。

我们将可恢复的上下文存储（在 session 中）和任意上下文管理（在 harness 中）的关注点分离，因为我们无法预测未来模型需要什么具体的 context engineering。

---

## 扩展：多大脑与多双手

**多大脑。** 解耦大脑与双手解决了我们最早的客户投诉之一。当团队想让 Claude 对他们 VPC 中的资源工作时，唯一的路径是网络对等互联。一旦 harness 不再在容器中，这个假设就消失了。

同样的变更有性能回报。当我们最初把大脑放在容器中时，每个 session 都要付完整的容器设置成本。使用解耦架构，我们的 **p50 TTFT 下降约 60%，p95 下降超过 90%**。扩展到多大脑只意味着启动多个无状态 harness，只在需要时连接到双手。

**多双手。** 我们还想要将每个大脑连接到多双手的能力。实践中这意味着 Claude 必须推理多个执行环境并决定把工作发到哪里。我们从大脑在单个容器中开始，因为早期模型没有这个能力。随着智能扩展，单容器变成了限制。

解耦大脑与双手使每只手成为一个工具，`execute(name, input) → string`。那个接口支持任何自定义工具、任何 MCP server 和我们自己的工具。Harness 不知道 sandbox 是容器、手机还是 Pokémon 模拟器。因为没有手与任何大脑耦合，大脑可以互相传递手。

---

## Meta-Harness 设计哲学

我们面临的挑战是一个老问题：如何为"尚未想到的程序"设计系统。操作系统通过将硬件虚拟化为足够通用的抽象而持续了几十年。

Managed Agents 是同样精神的 **meta-harness**，对 Claude 未来需要的具体 harness 不持意见。相反，它是一个具有通用接口的系统，允许许多不同的 harness。例如，Claude Code 是一个优秀的 harness，我们广泛使用。我们也展示了任务特定的 agent harness 在窄领域表现出色。Managed Agents 可以容纳任何这些，随时间匹配 Claude 的智能。

Meta-harness 设计意味着对 Claude 周围的接口持意见：我们预期 Claude 需要操作状态（session）和执行计算（sandbox）的能力。我们也预期 Claude 需要扩展到多大脑和多双手的能力。我们设计接口使这些可以在长时间范围内可靠且安全地运行。但我们不对 Claude 需要的大脑或双手的数量或位置做假设。

---

### 致谢

作者：Lance Martin、Gabe Cemaj 和 Michael Cohen。感谢 Nodir Turakulov 和 Jeremy Fox 在这些话题上的有益对话。特别感谢 Agents API 团队和 Jake Eaton 的贡献。
