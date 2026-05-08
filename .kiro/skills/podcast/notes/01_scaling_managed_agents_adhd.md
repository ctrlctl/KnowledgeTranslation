<style>
body, .markdown-body {
  font-family: "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, serif;
  font-size: 15px;
  line-height: 1.9;
  max-width: 68ch;
  margin: 0 auto;
  padding: 2em;
  color: #2c2c2c;
}
h1 { font-size: 1.5em; margin-top: 1.5em; }
h2 { font-size: 1.2em; margin-top: 2.5em; margin-bottom: 0.6em; }
p { margin: 1.1em 0; }
code {
  background: #f5f5f5;
  padding: 0.15em 0.4em;
  border-radius: 3px;
  font-size: 0.88em;
}
table { margin: 1.5em 0; border-collapse: collapse; }
th, td { padding: 0.5em 1em; border-bottom: 1px solid #eee; }
ul { padding-left: 1.2em; }
li { margin: 0.4em 0; }
hr { border: none; border-top: 1px solid #e0e0e0; margin: 2.5em 0; }
</style>

# Scaling Managed Agents：把"思考"和"动手"拆开

Anthropic Engineering · 2026-04-08 · [原文](https://www.anthropic.com/engineering/managed-agents)

---

## 目录

- [Harness 里的假设会过时](#harness-里的假设会过时)
- [像操作系统一样做抽象](#像操作系统一样做抽象)
- [别养宠物](#别养宠物)
- [把大脑和双手拆开](#把大脑和双手拆开)
- [Session ≠ Context Window](#session--context-window)
- [多大脑，多双手](#多大脑多双手)

---

## Harness 里的假设会过时

Engineering Blog 有一个持续的主题：如何构建有效的 agent，如何设计长时间运行的 harness。贯穿这些工作的共同线索是——harness 里写死了关于"Claude 自己做不到什么"的假设。但这些假设需要被频繁质疑，因为模型在进步，假设会过时。

举个例子。之前我们发现 Claude Sonnet 4.5 快用完 context window 时会提前收工——一种叫做 **context anxiety** 的行为。我们在 harness 里加了 context reset 来应对。但换到 Opus 4.5 上跑同一个 harness，发现这个行为已经消失了。那些 reset 变成了死代码。

Harness 注定要不断演进。所以我们做了 Managed Agents：Claude Platform 上的一个托管服务，通过一组能够跨越底层实现变化的稳定接口，代你运行长周期 agent——包括我们今天使用的那些实现。

---

## 像操作系统一样做抽象

构建 Managed Agents 意味着解决一个计算领域的老问题：怎么给"还没被发明出来的程序"设计系统。

几十年前操作系统就解决了——把硬件虚拟化成 **process**、**file** 这样的抽象，足够通用，适用于当时还不存在的程序。`read()` 不关心底下是70年代的磁盘还是现代 SSD。上面的接口不变，下面的实现随便换。

Managed Agents 照搬了这个思路。我们把 agent 的组件虚拟化成三个接口：

- **Session**：所有事件的 append-only 日志
- **Harness**：调用 Claude 并将 tool call 路由到相关基础设施的循环
- **Sandbox**：Claude 跑代码、改文件的执行环境

每个组件的实现可以独立替换，互不影响。我们对接口的形状有明确主张，但不管背后跑什么。

---

## 别养宠物

最初我们把所有 agent 组件放进一个容器——session、harness、sandbox 共享环境。好处是简单：文件操作就是 syscall，不用设计服务边界。

但把所有东西耦合到一个容器里，我们遇到了一个老的基础设施问题：我们养了一只宠物。在 **pets-vs-cattle** 的类比里，宠物是你精心照料、不能丢的；牲畜是可以随时替换的。我们的容器变成了宠物——挂了 session 就丢了，卡住了得人工抢救。

抢救意味着调试卡死的 session。唯一的观察窗口是 WebSocket 事件流，但它分不清是 harness 的 bug、网络丢包、还是容器下线——症状完全一样。想搞清楚就得进容器开 shell，但容器里有用户数据，实际上没法调试。

另一个问题：harness 默认 Claude 操作的所有东西都在同一个容器里。客户想让 Claude 访问自己 VPC 里的资源？要么网络对等，要么在客户环境里跑我们的 harness。一个写死在 harness 里的假设，变成了对接不同基础设施时的障碍。

---

## 把大脑和双手拆开

解决方案是把"大脑"（Claude + harness）、"双手"（sandbox + 工具）、"记忆"（session 日志）三者解耦。每个都是独立接口，可以单独挂掉或替换。

**Harness 搬出容器。** 它不再住在容器里，而是像调用任何工具一样调用容器：`execute(name, input) → string`。容器变成了牲畜。挂了，harness 收到 tool-call error 传回 Claude；Claude 决定要不要重试，重试就 `provision({resources})` 拉起新容器。不用抢救了。

**Harness 自己挂了也没事。** Session 日志在外面，harness 里没有需要在崩溃中保留的状态。挂了就重启一个，用 `wake(sessionId)` + `getSession(id)` 拿回事件日志，从最后一个事件继续。运行中通过 `emitEvent(id, event)` 持续写入 session。

**安全边界。** 耦合设计下，Claude 生成的不可信代码和凭证在同一个容器里跑。一次 prompt injection 骗 Claude 读环境变量就够了——拿到 token 后攻击者可以创建不受限的新 session。结构性修复：让 sandbox 里永远碰不到凭证。Git 场景下，初始化时用 access token clone repo 并配好 remote，之后 agent 不接触 token；自定义工具场景下，OAuth token 存在外部 vault，Claude 通过专用 proxy 调 MCP 工具，proxy 去 vault 取凭证再调外部服务。

---

## Session ≠ Context Window

长周期任务经常超出 context window 的长度。常规做法都涉及不可逆的取舍——compaction 把 context 压缩成摘要，memory tool 把上下文写到文件，context trimming 选择性删掉旧的 tool 结果。但很难预判未来哪些 token 会被用到，删错了回不来。

在 Managed Agents 里，session 日志充当一个活在 context window 之外的持久化上下文对象。接口 `getEvents()` 允许 harness 按位置切片查询事件流——从上次读到的地方继续、倒回某个时刻看前因、或在某个动作前重新读取上下文。

取出的事件还可以在 harness 里做任意变换再喂给 Claude——比如重新组织顺序来提高 prompt cache 命中率。我们把"可恢复的上下文存储"（session）和"任意上下文管理"（harness）分开，因为没法预测未来模型需要什么样的 context engineering。接口只保证 session 持久可查，怎么管理留给 harness 自己决定。

---

## 多大脑，多双手

**多大脑。** 解耦后客户不用再做网络对等就能让 Claude 访问自己 VPC 的资源。性能也有收益——以前每个 session 都要等容器启动（clone repo、拉事件、启动进程），即使根本不需要 sandbox。拆开后容器按需创建，不需要的 session 立刻开始推理。结果：p50 TTFT 下降约 60%，p95 下降超过 90%。扩展到多个大脑就是启动多个无状态 harness，按需连 sandbox。

**多双手。** 每只"手"就是一个工具调用 `execute(name, input) → string`。Harness 不知道 sandbox 是容器、手机还是 Pokémon 模拟器。手和大脑不绑定，大脑之间可以互相传递手。早期模型做不到在多个执行环境之间做路由决策，所以最初用单容器；模型变强之后，单容器反而成了瓶颈。

---

Managed Agents 是一个**元 harness**——不对 Claude 未来需要什么具体 harness 做假设，只提供通用接口让各种 harness 都能接入。设计上的主张只有：Claude 需要操作状态的能力（session）、执行计算的能力（sandbox）、扩展到多大脑多双手的能力。接口保证这些能长期可靠运行，至于需要多少、在哪里——不做假设。
