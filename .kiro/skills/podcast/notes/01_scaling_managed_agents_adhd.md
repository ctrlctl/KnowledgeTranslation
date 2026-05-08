<style>
body, .markdown-body {
  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", "Noto Sans SC", "Source Han Sans CN", sans-serif;
  font-size: 17px;
  line-height: 2.0;
  max-width: 60ch;
  margin: 0 auto;
  padding: 2.5em;
  color: #333;
  letter-spacing: 0.03em;
}
h1 { font-size: 1.6em; margin-top: 2em; margin-bottom: 1em; }
h2 { font-size: 1.25em; margin-top: 3em; margin-bottom: 0.8em; color: #222; }
h3 { font-size: 1.05em; margin-top: 2em; }
p { margin: 1.4em 0; }
blockquote {
  border-left: 3px solid #999;
  padding: 0.6em 1.2em;
  margin: 2em 0;
  color: #444;
}
code {
  background: #f5f5f5;
  padding: 0.2em 0.5em;
  border-radius: 3px;
  font-size: 0.88em;
}
table { margin: 1.8em 0; border-collapse: collapse; }
th, td { padding: 0.7em 1.2em; border-bottom: 1px solid #eee; }
ul, ol { padding-left: 1.2em; }
li { margin: 0.8em 0; }
hr { border: none; border-top: 1px solid #eee; margin: 3em 0; }
</style>

# Scaling Managed Agents

把"思考"和"动手"拆开。

Anthropic Engineering · 2026-04-08

---

## 先说结论

Agent 系统拆成三块独立组件。

每块可以单独挂掉。
单独替换。
单独扩展。

三块分别是：

- **Session** — 发生过什么事的日志
- **Harness** — 调用模型、做决策的循环
- **Sandbox** — 跑代码、改文件的执行环境

接口稳定，实现随便换。

---

## 为什么要拆

Harness 是 agent 的外部控制框架。

它里面写死了
"模型做不到 X"
这样的假设。

但模型在进步。

这些假设很快就会过时。

---

一个真实例子：

Claude Sonnet 4.5
快用完 context 时
会提前收工。

团队管这叫 **context anxiety**。

于是在 harness 里加了 context reset。

换到 Opus 4.5 一跑——
这毛病没了。

reset 变成了死代码。

---

所以需要一组
能够跨越底层实现变化的
**稳定接口**。

这就是 Managed Agents。

---

## 设计思路

这是计算机领域的老问题：

怎么给"还没被发明出来的程序"
设计系统？

操作系统几十年前就解决了。

把硬件虚拟化成抽象。
`read()` 不关心底下是什么磁盘。
上面的接口不变，
下面的实现随便换。

---

Managed Agents 照搬这个思路。

把 agent 拆成三个可替换组件：

| 组件 | 职责 |
|------|------|
| **Session** | 记住发生过什么 |
| **Harness** | 思考、决策、路由 |
| **Sandbox** | 跑代码、改文件 |

每个组件的实现
可以独立替换，
互不影响。

---

## 别养宠物

**Pets vs Cattle**
宠物 vs 牲畜。

宠物 = 精心照料、不能丢的服务器。

牲畜 = 随时可以杀掉重建的服务器。

---

最初把所有东西塞进一个容器。

这个容器变成了宠物。

挂了有多痛苦：

- 容器挂了 → session 丢失
- 容器卡住 → 得人工抢救
- 想调试 → 分不清是 harness bug、网络丢包、还是容器下线
- 客户想连自己 VPC → 要么网络对等，要么跑 Anthropic 的 harness

---

## 怎么拆的

核心操作：

**Harness 搬出容器。**

---

### 容器变牲畜

Harness 调用容器的方式
和调用任何工具一样：

```
execute(name, input) → string
```

容器挂了？

收到 tool-call error。
传给 Claude。
Claude 决定要不要重试。
重试就拉起新容器。

**不用抢救了。**

---

### Harness 挂了也没事

Session 日志在外面。

Harness 里没有需要保留的状态。

挂了就重启一个：

1. `wake(sessionId)`
2. `getSession(id)` 拿回事件日志
3. 从最后一个事件继续

---

### 安全

以前的问题：

Claude 生成的代码
和凭证
在同一个容器里。

一次 prompt injection
骗 Claude 读环境变量
就够了。

---

修复：

**凭证永远不进 sandbox。**

Git — 初始化时用 token clone repo，之后 agent 不碰 token。

自定义工具 — OAuth token 在外部 vault，通过 proxy 调 MCP 工具。

---

## Session ≠ Context Window

长任务超出 context window 怎么办？

常规做法都是**不可逆**的：

- Compaction — 压缩成摘要
- Memory tool — 写到文件
- Context trimming — 删旧内容

问题：

删错了回不来。

很难预判
未来哪些 token 会被用到。

---

Managed Agents 的做法：

Session 日志 =
活在 context window 之外的
**持久化上下文**。

随时可以回看。
随时可以切片。
随时可以重读。

---

接口：`getEvents()`

- 从上次读到的地方继续
- 倒回某个时刻看前因
- 在某个动作前重新读取上下文

取出的事件
还能在 harness 里变换
再喂给 Claude。

---

为什么存储和管理要分开？

因为没法预测
未来模型需要什么样的
context engineering。

接口只保证 session 持久可查。

怎么管理，留给 harness。

---

## 多大脑 × 多双手

### 多大脑

以前每个 session 都要等容器启动。

即使根本不需要 sandbox。

拆开后，容器按需创建。

不需要的 session 立刻开始推理。

---

结果：

**p50 TTFT 下降 60%**

**p95 下降超过 90%**

扩展 = 启动更多无状态 harness，按需连 sandbox。

---

### 多双手

每只"手"就是一个工具调用：

```
execute(name, input) → string
```

Harness 不知道 sandbox 是什么。

容器、手机、Pokémon 模拟器，都行。

手和大脑不绑定。

大脑之间可以互相传递手。

---

## 记住三点

**Agent = Session + Harness + Sandbox**

三者解耦。

**每个组件都是牲畜**

挂了就换，不用抢救。

**接口稳定，实现随便换**

这就是"元 harness"。
