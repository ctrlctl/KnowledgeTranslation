<style>
body, .markdown-body {
  font-family: "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, serif;
  line-height: 1.8;
}
</style>

# Scaling Managed Agents：将大脑与双手解耦

**来源**：Anthropic Engineering | 2026-04-08
**原文**：https://www.anthropic.com/engineering/managed-agents
**作者**：Lance Martin, Gabe Cemaj, Michael Cohen

---

## 索引

- [核心观点](#核心观点)
- [背景：Harness的假设会过时](#背景harness的假设会过时)
- [设计灵感：操作系统的抽象](#设计灵感操作系统的抽象)
- [架构：Session、Harness、Sandbox](#架构sessionharnesssandbox)
- [Don't adopt a pet：宠物vs牲畜](#dont-adopt-a-pet宠物vs牲畜)
- [解耦大脑与双手](#解耦大脑与双手)
- [Session不是Claude的Context Window](#session不是claude的context-window)
- [多大脑，多双手](#多大脑多双手)
- [结论](#结论)

---

## 核心观点

Harness（agent外壳/脚手架）编码了关于模型能力的假设，但这些假设会随模型进步而过时。Managed Agents是Anthropic的托管服务，借鉴操作系统设计——将agent组件虚拟化为稳定接口，使底层实现可自由演进。

---

## 背景：Harness的假设会过时

Engineering Blog的一个持续主题是如何构建有效的agent（effective agents）和设计长时间运行工作的harness。贯穿这些工作的共同线索是：**harness编码了关于Claude自身无法做什么的假设**。然而，这些假设需要被频繁质疑，因为它们会随模型进步而过时。

一个例子：在之前的工作中，我们发现Claude Sonnet 4.5会在感知到context limit接近时过早结束任务——一种被称为"context anxiety"（上下文焦虑）的行为。我们通过在harness中添加context reset来解决。但当我们在Claude Opus 4.5上使用相同的harness时，发现这个行为已经消失了。那些reset变成了死代码（dead weight）。

我们预期harness会持续演进。因此我们构建了Managed Agents：Claude Platform中的托管服务，通过一小组**旨在比任何特定实现更持久的接口**来代你运行长周期agent——包括我们今天运行的那些实现。

---

## 设计灵感：操作系统的抽象

构建Managed Agents意味着解决计算领域的一个老问题：如何为"尚未被构想出的程序"（programs as yet unthought of）设计系统。

几十年前，操作系统通过将硬件虚拟化为抽象——**process**、**file**——解决了这个问题，这些抽象足够通用，适用于当时还不存在的程序。抽象比硬件更持久。`read()` 命令不关心它访问的是1970年代的磁盘组还是现代SSD。**上层抽象保持稳定，底层实现自由变化。**

Managed Agents遵循相同模式。我们虚拟化了agent的组件：

- **Session**（会话）：所有发生事件的append-only日志
- **Harness**（外壳）：调用Claude并将Claude的tool call路由到相关基础设施的循环
- **Sandbox**（沙箱）：Claude可以运行代码和编辑文件的执行环境

这允许每个组件的实现被替换而不干扰其他组件。我们对这些接口的形状有明确主张（opinionated），但对背后运行什么没有。

---

## Don't adopt a pet：宠物vs牲畜

我们最初将所有agent组件放入单个容器（container），意味着session、agent harness和sandbox共享一个环境。这有好处：文件编辑是直接的syscall，不需要设计服务边界。

但将所有东西耦合到一个容器中，我们遇到了一个老的基础设施问题：**我们养了一只宠物**（adopted a pet）。在pets-vs-cattle类比中，宠物是你不能失去的、需要精心照料的个体；而牲畜是可互换的。在我们的案例中，服务器变成了那只宠物——如果容器失败，session就丢失了。如果容器无响应，我们必须把它"护理"回来。

护理容器意味着调试无响应的卡住session。我们唯一的窗口是WebSocket事件流，但它无法告诉我们故障出在哪里——harness中的bug、事件流中的丢包、或容器下线，呈现的症状完全相同。要弄清楚出了什么问题，工程师必须在容器内打开shell，但因为那个容器通常也持有用户数据，这意味着我们实际上缺乏调试能力。

第二个问题：harness假设Claude工作的内容都在容器内。当客户要求将Claude连接到他们的VPC时，他们要么将网络与我们对等（peer），要么在自己的环境中运行我们的harness。**一个烘焙进harness的假设，在我们想连接不同基础设施时变成了问题。**

---

## 解耦大脑与双手

我们得出的解决方案是将"大脑"（Claude及其harness）与"双手"（执行动作的sandbox和工具）以及"session"（session事件日志）解耦。每个都变成了一个对其他组件做很少假设的接口，每个都可以独立失败或被替换。

### Harness离开容器

将大脑从双手解耦意味着harness不再住在容器内。它像调用任何其他工具一样调用容器：

```
execute(name, input) → string
```

容器变成了牲畜。如果容器死了，harness将故障作为tool-call error捕获并传回Claude。如果Claude决定重试，新容器可以用标准配方重新初始化：`provision({resources})`。我们不再需要把失败的容器护理回来。

### 从Harness故障中恢复

Harness也变成了牲畜。因为session日志在harness外部，harness中没有任何东西需要在崩溃中存活。当一个失败时，新的可以用 `wake(sessionId)` 重启，用 `getSession(id)` 取回事件日志，从最后一个事件恢复。在agent循环中，harness用 `emitEvent(id, event)` 写入session以保持持久的事件记录。

### 安全边界

在耦合设计中，Claude生成的任何不受信任的代码都在与凭证相同的容器中运行——所以prompt injection只需要说服Claude读取自己的环境变量。一旦攻击者获得这些token，他们可以生成新的、不受限制的session并将工作委派给它们。

结构性修复是确保**token永远不可从Claude生成代码运行的sandbox中访问**。

两种模式：
- **Git**：用仓库的access token在sandbox初始化时clone repo并连接到本地git remote。`git push/pull` 在sandbox内工作，agent永远不处理token本身。
- **自定义工具**：通过MCP支持，OAuth token存储在安全vault中。Claude通过专用proxy调用MCP工具；proxy获取对应凭证并调用外部服务。Harness永远不知道任何凭证。

---

## Session不是Claude的Context Window

长周期任务经常超出Claude的context window长度。标准解决方式都涉及**关于保留什么的不可逆决策**。我们在之前的context engineering工作中探索过这些技术：

- **Compaction**（压缩）：让Claude保存context window的摘要
- **Memory tool**：让Claude将上下文写入文件，实现跨session学习
- **Context trimming**：选择性移除token（如旧的tool结果或thinking块）

但选择性保留或丢弃上下文的不可逆决策可能导致失败。**很难知道未来的轮次需要哪些token。**

在Managed Agents中，session作为**存在于Claude context window之外的上下文对象**。上下文持久存储在session日志中。接口 `getEvents()` 允许大脑通过选择事件流的位置切片来查询上下文——可以从上次停止阅读的地方继续，在特定时刻前倒回几个事件查看前因，或在特定动作前重新阅读上下文。

获取的事件也可以在harness中被转换后再传入Claude的context window。我们分离了**可恢复的上下文存储**（在session中）和**任意上下文管理**（在harness中）的关注点，因为我们无法预测未来模型需要什么具体的context engineering。接口将上下文管理推入harness，只保证session是持久的且可被查询。

---

## 多大脑，多双手

### 多大脑

解耦大脑与双手解决了最早的客户投诉之一。当团队想让Claude对其VPC中的资源工作时，唯一路径是将网络与我们对等，因为持有harness的容器假设每个资源都在它旁边。一旦harness不再在容器中，这个假设就消失了。

同样的变化带来了性能收益。最初将大脑放在容器中意味着多个大脑需要同样多的容器。对每个大脑，在容器被provisioned之前不能进行推理；每个session都要支付完整的容器启动成本。每个session——即使是永远不会触碰sandbox的——都必须clone repo、启动进程、从服务器获取pending事件。

这个死时间体现在**TTFT（time-to-first-token）**中——衡量session从接受工作到产生第一个响应token之间等待多长时间。TTFT是用户最敏锐感受到的延迟。

解耦后，容器只在需要时通过tool call `execute(name, input) → string` 被大脑provisioned。不需要容器的session不用等待。推理可以在orchestration层从session日志拉取pending事件后立即开始。

使用这种架构：
- **p50 TTFT下降约60%**
- **p95下降超过90%**

扩展到多大脑只意味着启动多个无状态harness，仅在需要时连接到hands。

### 多双手

我们还想让每个大脑连接多双手。实践中，这意味着Claude必须推理多个执行环境并决定将工作发送到哪里——比在单个shell中操作更难的认知任务。我们最初将大脑放在单个容器中，因为早期模型不具备这种能力。随着智能扩展，单容器变成了限制：当那个容器失败时，我们丢失了大脑正在触及的每只手的状态。

解耦使每只手成为一个工具 `execute(name, input) → string`：名称和输入进去，字符串返回。该接口支持任何自定义工具、任何MCP服务器和我们自己的工具。Harness不知道sandbox是容器、手机还是Pokémon模拟器。因为没有手与任何大脑耦合，**大脑可以将手传递给彼此**。

---

## 结论

我们面临的挑战是一个老问题：如何为"尚未被构想出的程序"设计系统。操作系统通过将硬件虚拟化为足够通用的抽象而持续了数十年。

Managed Agents是同一精神的**元harness**（meta-harness），对Claude未来需要的具体harness不持立场。它是一个具有通用接口的系统，允许许多不同的harness。例如，Claude Code是我们广泛使用的优秀harness。我们也展示了任务特定的agent harness在窄领域中表现出色。Managed Agents可以容纳任何这些，随时间匹配Claude的智能。

元harness设计意味着对Claude周围的接口持明确主张：
- Claude需要操作状态的能力（session）
- Claude需要执行计算的能力（sandbox）
- Claude需要扩展到多大脑和多双手的能力

我们设计接口使这些可以在长时间范围内可靠且安全地运行。但我们**不假设Claude需要多少大脑或多少手，也不假设它们在哪里**。
