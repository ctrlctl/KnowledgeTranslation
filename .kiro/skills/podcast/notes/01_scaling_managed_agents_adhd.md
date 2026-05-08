<style>
body, .markdown-body {
  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", "Noto Sans SC", "Source Han Sans CN", sans-serif;
  font-size: 17px;
  line-height: 2.0;
  max-width: 65ch;
  margin: 0 auto;
  padding: 2em;
  color: #2c3e50;
  letter-spacing: 0.02em;
}
h1 { font-size: 1.8em; margin-top: 1.5em; }
h2 { font-size: 1.4em; margin-top: 2.5em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }
h3 { font-size: 1.1em; margin-top: 1.8em; }
p { margin: 1.2em 0; }
blockquote {
  font-size: 1.1em;
  font-weight: 600;
  border-left: 4px solid #e74c3c;
  padding: 0.8em 1.2em;
  margin: 1.8em 0;
  background: #fdf8f8;
  border-radius: 0 6px 6px 0;
}
.tldr {
  background: #f0f7ff;
  border: 2px solid #4a9eff;
  border-radius: 8px;
  padding: 1.2em 1.5em;
  margin: 1.8em 0;
  font-size: 1.05em;
}
.tldr strong { color: #2070c0; }
code {
  background: #f5f5f5;
  padding: 0.2em 0.5em;
  border-radius: 4px;
  font-size: 0.9em;
}
table { margin: 1.5em 0; }
th, td { padding: 0.6em 1em; }
ul, ol { padding-left: 1.5em; }
li { margin: 0.5em 0; }
</style>

# Scaling Managed Agents

## 把"思考"和"动手"拆开

Anthropic Engineering · 2026-04-08
[原文链接](https://www.anthropic.com/engineering/managed-agents)

---

<div class="tldr">

**⚡ TL;DR**

Agent 系统拆成三块独立组件（session / harness / sandbox），每块可以单独挂掉、单独替换、单独扩展。借鉴操作系统的思路：接口稳定，实现随便换。

</div>

---

## 目录

- [问题：Harness 里的假设会过时](#问题harness-里的假设会过时)
- [思路：像操作系统一样做抽象](#思路像操作系统一样做抽象)
- [教训：别养宠物](#教训别养宠物)
- [方案：把大脑和双手拆开](#方案把大脑和双手拆开)
- [设计：Session ≠ Context Window](#设计session--context-window)
- [扩展：多大脑 × 多双手](#扩展多大脑--多双手)
- [记住这三点](#记住这三点)

---

## 问题：Harness 里的假设会过时

Harness 是 agent 的外部控制框架——调用模型、路由 tool call、管理执行流程。

它里面写死了很多"模型做不到 X"的假设。

但模型在进步，这些假设很快就会过时。

一个真实例子：

- Claude Sonnet 4.5 快用完 context 时会提前收工
- 团队管这叫 "context anxiety"
- 于是在 harness 里加了 context reset
- 换到 Opus 4.5 一跑——这毛病没了
- reset 变成了死代码

> Harness 注定要不断演进。所以需要一组能够跨越底层实现变化的稳定接口。

这就是 Managed Agents 要解决的事。

---

## 思路：像操作系统一样做抽象

这是计算机领域的老问题：怎么给"还没被发明出来的程序"设计系统？

操作系统几十年前就解决了：

- 把硬件虚拟化成 `process`、`file` 这样的抽象
- `read()` 不关心底下是70年代的磁盘还是现代 SSD
- 上面的接口不变，下面的实现随便换

Managed Agents 照搬这个思路，把 agent 拆成三个可替换组件：

| 组件 | 是什么 | 职责 |
|------|--------|------|
| **Session** | append-only 事件日志 | 记住发生过什么 |
| **Harness** | 调用 Claude 的循环 | 思考、决策、路由 |
| **Sandbox** | 执行环境 | 跑代码、改文件 |

每个组件的实现可以独立替换，互不影响。

---

## 教训：别养宠物

<div class="tldr">

**Pets vs Cattle（宠物 vs 牲畜）**

🐱 宠物 = 精心照料、不能丢的服务器

🐄 牲畜 = 随时可以杀掉重建的服务器

</div>

最初把所有东西塞进一个容器。这个容器变成了宠物。

挂了有多痛苦：

- 容器挂了 → session 丢失
- 容器卡住 → 得人工抢救
- 想调试 → WebSocket 事件流分不清是 harness bug、网络丢包、还是容器下线
- 客户想连自己 VPC → 要么网络对等，要么在客户环境跑 Anthropic 的 harness

一个写死在 harness 里的假设，变成了对接不同基础设施时的障碍。

---

## 方案：把大脑和双手拆开

把"大脑"（Claude + harness）、"双手"（sandbox + 工具）、"记忆"（session）三者解耦。

每个都是独立接口，可以单独挂掉或替换。

---

### 容器变牲畜

Harness 调用容器的方式和调用任何工具一样：

```
execute(name, input) → string
```

容器挂了？收到 tool-call error，传给 Claude。

Claude 决定要不要重试。重试就 `provision({resources})` 拉起新容器。

不用抢救了。

---

### Harness 挂了也没事

Session 日志在外面，harness 里没有需要保留的状态。

挂了就重启一个：

1. `wake(sessionId)`
2. `getSession(id)` 拿回事件日志
3. 从最后一个事件继续

运行中通过 `emitEvent(id, event)` 持续写入 session。

---

### 安全：Sandbox 里碰不到凭证

以前的问题：

Claude 生成的代码和凭证在同一个容器里。一次 prompt injection 骗 Claude 读环境变量就够了。

> 修复：凭证永远不进 sandbox。

| 场景 | 做法 |
|------|------|
| Git | 初始化时用 token clone repo，之后 agent 不碰 token |
| 自定义工具 | OAuth token 在外部 vault，通过 proxy 调 MCP 工具 |

---

## 设计：Session ≠ Context Window

长任务超出 context window 怎么办？

常规做法都是不可逆的：

- Compaction — 压缩成摘要
- Memory tool — 写到文件
- Context trimming — 删旧的 tool 结果

> 问题：删错了回不来。很难预判未来哪些 token 会被用到。

Managed Agents 的做法不一样：

Session 日志 = 活在 context window 之外的持久化上下文。

通过 `getEvents()` 随时可以：

- 从上次读到的地方继续
- 倒回某个时刻看前因
- 在某个动作前重新读取上下文

取出的事件还能在 harness 里变换再喂给 Claude。

存储和管理分开——因为没法预测未来模型需要什么 context engineering。

---

## 扩展：多大脑 × 多双手

### 多大脑

以前每个 session 都要等容器启动，即使根本不需要 sandbox。

拆开后，容器按需创建。不需要的 session 立刻开始推理。

> **p50 TTFT 下降 60%，p95 下降超过 90%**

扩展 = 启动更多无状态 harness，按需连 sandbox。

---

### 多双手

每只"手"就是一个工具调用：

```
execute(name, input) → string
```

Harness 不知道 sandbox 是容器、手机还是 Pokémon 模拟器。

手和大脑不绑定 → 大脑之间可以互相传递手。

---

## 记住这三点

> **1. Agent = Session + Harness + Sandbox，三者解耦**

> **2. 每个组件都是牲畜——挂了就换，不用抢救**

> **3. 接口稳定，实现随便换——这就是"元 harness"**

不对 Claude 未来需要什么 harness 做假设。

只保证三件事能长期可靠运行：

- 操作状态（session）
- 执行计算（sandbox）
- 扩展到任意规模（多大脑 × 多双手）
