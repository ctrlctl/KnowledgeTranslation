<style>
body, .markdown-body {
  font-family: "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, serif;
  line-height: 2.0;
}
h2 { margin-top: 2em; }
blockquote {
  font-size: 1.2em;
  font-weight: bold;
  border-left: 4px solid #e74c3c;
  padding: 0.5em 1em;
  margin: 1.5em 0;
  background: #fdf2f2;
}
.tldr {
  background: #eef7ff;
  border: 2px solid #3498db;
  border-radius: 8px;
  padding: 1em;
  margin: 1em 0;
}
</style>

# 🧠 Scaling Managed Agents：把"思考"和"动手"拆开

<div class="tldr">

**⚡ 一句话总结：** Agent 系统里"思考的部分"和"干活的部分"不应该绑在一起。拆开之后，挂了能恢复、能扩展、更安全。

</div>

**来源**：Anthropic Engineering | 2026-04-08
**原文**：https://www.anthropic.com/engineering/managed-agents

---

## 这篇文章在讲什么？

Anthropic 做了一个叫 **Managed Agents** 的托管服务。核心设计思想就一个：

> **把 agent 拆成三块独立的东西，每块可以单独挂掉、单独替换、单独扩展。**

这三块是：
1. 🧠 **Session**（记忆） — 发生过什么事的日志
2. ⚙️ **Harness**（大脑） — 调用 Claude、路由 tool call 的循环
3. 🖐️ **Sandbox**（双手） — 跑代码、改文件的执行环境

---

## 为什么要拆？

> **因为 harness 里写死的假设会过时。**

一个真实的例子：

Claude Sonnet 4.5 快用完 context 时会提前收工（"context anxiety"）→ 团队在 harness 里加了 context reset → 换到 Opus 4.5 发现这毛病没了 → **reset 变成了死代码**。

模型在进步，harness 必须跟着变。所以需要一组**不随 harness 变化而变化的稳定接口**。

---

## 🐾 别养宠物

<div class="tldr">

**关键概念：Pets vs Cattle（宠物 vs 牲畜）**

- 🐱 宠物 = 精心照料、不能丢的服务器
- 🐄 牲畜 = 随时可以杀掉重建的服务器

最初的设计把所有东西塞进一个容器 → 这个容器变成了宠物 → 挂了就全完了。

</div>

具体有多痛苦：

- 容器挂了 → session 丢失
- 容器卡住 → 得人工"抢救"
- 想调试 → 唯一入口是 WebSocket 事件流，但**分不清是 harness bug、网络丢包、还是容器下线**
- 客户想连自己的 VPC → 要么网络对等，要么在客户环境跑 Anthropic 的 harness

---

## ✂️ 怎么拆的

> **核心操作：Harness 搬出容器。**

拆完之后：

### 容器变牲畜

Harness 调用容器的方式和调用任何工具一样：

```
execute(name, input) → string
```

容器挂了？Harness 收到一个 tool-call error，传给 Claude。Claude 决定要不要重试。重试就 `provision({resources})` 拉起新容器。

**不用抢救了。**

### Harness 自己挂了也没事

Session 日志在外面，harness 里没有需要保留的状态。挂了就重启一个：

```
wake(sessionId) → getSession(id) → 从最后一个事件继续
```

### 安全：Sandbox 里碰不到凭证

> **以前的问题：** Claude 生成的代码和凭证在同一个容器里。一次 prompt injection 骗 Claude 读环境变量就够了。

**修复：凭证永远不进 sandbox。**

| 场景 | 做法 |
|------|------|
| Git | 初始化时用 token clone repo，之后 push/pull 正常工作，agent 不碰 token |
| 自定义工具 | OAuth token 在外部 vault，Claude 通过 proxy 调 MCP 工具，proxy 去 vault 取凭证 |

---

## 📝 Session ≠ Context Window

<div class="tldr">

**核心问题：** 长任务超出 context window 怎么办？

常规做法（compaction、trimming）都是**不可逆的**——删错了回不来。

**Managed Agents 的做法：** Session 日志就是一个活在 context window 之外的持久化上下文。随时可以回看、切片、重读。

</div>

接口：`getEvents()` — 按位置切片查询事件流

- 从上次读到的地方继续
- 倒回某个时刻看前因
- 在某个动作前重新读取上下文

取出的事件还能在 harness 里做变换再喂给 Claude（比如重排顺序提高 prompt cache 命中率）。

**为什么存储和管理要分开？** 因为没法预测未来模型需要什么样的 context engineering。接口只保证 session 持久可查，怎么管理留给 harness。

---

## 🚀 多大脑 × 多双手

### 多大脑 → 性能飞升

以前每个 session 都要等容器启动（clone repo、拉事件、启动进程），即使根本不需要 sandbox。

拆开后，容器按需创建。不需要的 session 立刻开始推理。

> **结果：p50 TTFT 下降 60%，p95 下降超过 90%**

扩展 = 启动更多无状态 harness，按需连 sandbox。

### 多双手 → 一个大脑操控多个执行环境

每只"手"就是一个工具调用：`execute(name, input) → string`

Harness 不知道 sandbox 是容器、手机还是 Pokémon 模拟器。

而且因为手和大脑不绑定 → **大脑之间可以互相传递手**。

---

## 🎯 总结：记住这三点就够了

> 1. **Agent = Session + Harness + Sandbox，三者解耦**
> 2. **每个组件都是牲畜，挂了就换，不用抢救**
> 3. **接口稳定，实现随便换——这就是"元 harness"**

Managed Agents 不对 Claude 未来需要什么 harness 做假设。只保证三件事能长期可靠运行：操作状态（session）、执行计算（sandbox）、扩展到任意规模（多大脑多双手）。
