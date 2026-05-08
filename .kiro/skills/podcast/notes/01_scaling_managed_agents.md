<style>
body, .markdown-body {
  font-family: "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, serif;
  line-height: 1.8;
}
</style>

# Scaling Managed Agents：把"思考"和"动手"拆开

**来源**：Anthropic Engineering | 2026-04-08
**原文**：https://www.anthropic.com/engineering/managed-agents
**作者**：Lance Martin, Gabe Cemaj, Michael Cohen

---

## 索引

- [引言：Harness里的假设会过时](#引言harness里的假设会过时)
- [设计思路：像操作系统一样做抽象](#设计思路像操作系统一样做抽象)
- [别养宠物](#别养宠物)
- [把大脑和双手拆开](#把大脑和双手拆开)
- [Session ≠ Context Window](#session--context-window)
- [多个大脑，多双手](#多个大脑多双手)
- [结论](#结论)

---

## 引言：Harness里的假设会过时

Harness（agent的外部控制框架——负责调用模型、路由tool call、管理执行流程）里写死了很多"模型做不到X"的假设。问题是，模型在进步，这些假设很快就会过时。

举个例子：Claude Sonnet 4.5 快用完 context window 时会提前收工——团队管这叫"context anxiety"（上下文焦虑）。于是在 harness 里加了 context reset 机制来应对。结果换到 Opus 4.5 一跑，这个毛病没了，reset 变成了多余的死代码。

既然 harness 注定要不断演进，Anthropic 就做了 Managed Agents：一个托管服务，通过一组能够跨越底层实现变化的稳定接口，代你运行长周期 agent——包括我们今天使用的那些实现。

---

## 设计思路：像操作系统一样做抽象

这其实是计算机领域的老问题：怎么给"还没被发明出来的程序"设计系统？

操作系统几十年前就解决了——把硬件虚拟化成 process、file 这样的抽象。`read()` 不关心底下是70年代的磁盘还是现代SSD。**上面的接口不变，下面的实现随便换。**

Managed Agents 照搬了这个思路，把 agent 拆成三个可替换的组件：

| 组件 | 是什么 | 类比 |
|------|--------|------|
| **Session** | 所有事件的 append-only 日志 | 文件系统 |
| **Harness** | 调用 Claude、路由 tool call 的循环 | 进程调度器 |
| **Sandbox** | Claude 跑代码、改文件的执行环境 | 用户空间 |

每个组件的实现可以独立替换，互不影响。Anthropic 只对接口的形状有主张，不管背后跑什么。

---

## 别养宠物

最初的设计把所有东西塞进一个容器：session、harness、sandbox 共享环境。好处是简单——文件操作就是 syscall，不用设计服务边界。

坏处是：**这个容器变成了"宠物"**。

在 pets-vs-cattle（宠物vs牲畜）的经典类比里，宠物是你精心照料、不能丢的；牲畜是可以随时替换的。一旦容器挂了，session 就没了；容器卡住了，得人工去"抢救"。

抢救意味着调试卡死的 session。唯一的观察窗口是 WebSocket 事件流，但它分不清是 harness 的 bug、网络丢包、还是容器下线——症状完全一样。想搞清楚就得进容器开 shell，但容器里有用户数据，所以实际上没法调试。

另一个问题：harness 默认 Claude 操作的所有东西都在同一个容器里。客户想让 Claude 访问自己 VPC 里的资源？要么网络对等，要么在客户环境里跑 Anthropic 的 harness。一个写死在 harness 里的假设，变成了对接不同基础设施时的障碍。

---

## 把大脑和双手拆开

解决方案：把"大脑"（Claude + harness）、"双手"（sandbox + 工具）、"记忆"（session 日志）三者解耦。每个都是独立接口，可以单独挂掉或替换。

### Harness 搬出容器

Harness 不再住在容器里，而是像调用任何工具一样调用容器：

```
execute(name, input) → string
```

容器变成了牲畜——挂了就挂了，harness 把错误当 tool-call error 传回 Claude，Claude 决定要不要重试。重试就用 `provision({resources})` 拉起一个新容器。不用再抢救了。

### Harness 自己挂了怎么办

Harness 也是牲畜。Session 日志在 harness 外面，所以 harness 里没有任何状态需要在崩溃中保留。挂了就重启一个，用 `wake(sessionId)` + `getSession(id)` 拿回事件日志，从最后一个事件继续。运行中通过 `emitEvent(id, event)` 持续写入 session。

### 安全边界

耦合设计下，Claude 生成的不可信代码和凭证在同一个容器里跑。一次 prompt injection 只要骗 Claude 读环境变量就够了——拿到 token 后攻击者可以创建不受限的新 session。

结构性修复：**让 sandbox 里永远碰不到凭证。**

两种做法：
- **Git**：初始化 sandbox 时用 access token clone repo 并配好 remote。之后 `git push/pull` 正常工作，但 agent 从头到尾不接触 token。
- **自定义工具**：OAuth token 存在外部 vault 里。Claude 通过专用 proxy 调用 MCP 工具，proxy 拿 session 关联的 token 去 vault 取凭证再调外部服务。Harness 全程不知道任何凭证。

---

## Session ≠ Context Window

长周期任务经常超出 context window 的长度。常规做法都涉及**不可逆的取舍**：

- **Compaction**：让 Claude 把 context 压缩成摘要
- **Memory tool**：把上下文写到文件里，跨 session 保留
- **Context trimming**：选择性删掉旧的 tool 结果或 thinking 块

问题是：你很难预判未来哪些 token 会被用到。删错了就回不来了。

Managed Agents 的做法：session 日志就是一个**活在 context window 之外的持久化上下文对象**。通过 `getEvents()` 接口，harness 可以按位置切片查询事件流——从上次读到的地方继续、倒回某个时刻看前因、或在某个动作前重新读取上下文。

取出的事件还可以在 harness 里做任意变换再喂给 Claude——比如重新组织顺序来提高 prompt cache 命中率。

为什么要把"存储"和"管理"分开？因为没法预测未来模型需要什么样的 context engineering。接口只保证 session 是持久的、可查询的；具体怎么管理上下文，留给 harness 自己决定。

---

## 多个大脑，多双手

### 多个大脑

解耦之后，客户不用再做网络对等就能让 Claude 访问自己 VPC 的资源——因为 harness 不再假设资源在旁边。

性能也有收益。之前每个 session 都要等容器启动（clone repo、拉事件、启动进程），即使这个 session 根本不需要 sandbox。这些等待时间直接体现在 TTFT（time-to-first-token，用户感知最强烈的延迟）上。

解耦后，容器只在需要时才通过 tool call 按需创建。不需要容器的 session 立刻开始推理。结果：

- **p50 TTFT 下降约 60%**
- **p95 下降超过 90%**

扩展到多个大脑就是启动多个无状态 harness，按需连接 sandbox。

### 多双手

每个大脑还能连接多个执行环境。实际上就是让 Claude 在多个 sandbox 之间做路由决策——比单 shell 操作难得多。早期模型做不到这个，所以最初用单容器。模型变强之后，单容器反而成了瓶颈：一个容器挂了，所有连接的执行环境状态都丢了。

解耦后每只"手"就是一个工具调用 `execute(name, input) → string`。Harness 不知道 sandbox 是容器、手机还是 Pokémon 模拟器。而且因为手和大脑不绑定，**大脑之间可以互相传递手**。

---

## 结论

Managed Agents 是一个**元 harness**（meta-harness）：不对 Claude 未来需要什么具体 harness 做假设，只提供通用接口让各种 harness 都能接入。

设计上的主张只有三点：
1. Claude 需要操作状态的能力（session）
2. Claude 需要执行计算的能力（sandbox）
3. Claude 需要扩展到多大脑、多双手的能力

接口保证这些能力可以长期可靠、安全地运行。至于需要多少大脑、多少手、它们在哪里——不做假设。
