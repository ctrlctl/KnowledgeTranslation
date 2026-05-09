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

# The Anatomy of an Agent Harness：Agent Harness 解剖学

> 原文：[The Anatomy of an Agent Harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness)
> 来源：LangChain Blog | 2026-03-10
> 作者：Vivek Trivedy

---

## 目录

- [什么是 Harness？](#什么是-harness)
- [为什么需要 Harness：从模型视角出发](#为什么需要-harness从模型视角出发)
- [文件系统：持久存储与上下文管理](#文件系统持久存储与上下文管理)
- [Bash + 代码：通用工具](#bash--代码通用工具)
- [沙箱与验证工具](#沙箱与验证工具)
- [记忆与搜索：持续学习](#记忆与搜索持续学习)
- [对抗 Context Rot](#对抗-context-rot)
- [长时间自主执行](#长时间自主执行)
- [Harness 的未来](#harness-的未来)

---

## 什么是 Harness？

**Agent = Model + Harness。**

如果你不是模型，你就是 harness。

Harness 是除了模型本身之外的所有代码、配置和执行逻辑。一个裸模型不是 agent，但当 harness 赋予它状态、工具执行、反馈循环和可执行约束时，它就变成了 agent。

具体来说，harness 包括：

- System Prompt
- Tools、Skills、MCP 及其描述
- 捆绑的基础设施（文件系统、沙箱、浏览器）
- 编排逻辑（subagent 生成、handoff、模型路由）
- Hook/中间件用于确定性执行（compaction、continuation、lint 检查）

这篇文章的核心方法论：**从期望的 agent 行为倒推到 harness 工程设计。**

---

## 为什么需要 Harness：从模型视角出发

模型（大部分）接收文本、图像、音频、视频，输出文本。就这样。开箱即用它们不能：

- 跨交互维持持久状态
- 执行代码
- 访问实时知识
- 设置环境和安装包来完成工作

这些都是 harness 层面的功能。LLM 的结构要求某种包裹它们的机制来做有用的工作。

比如，要实现"聊天"这种产品 UX，我们把模型包在一个 while 循环里来追踪之前的消息并追加新的用户消息。每个读者都已经用过这种 harness。

**核心思路：将期望的 agent 行为转化为 harness 中的实际功能。**

---

## 文件系统：持久存储与上下文管理

**期望行为：** Agent 需要持久存储来与真实数据交互、卸载不适合放在上下文中的信息、跨 session 持久化工作。

模型只能直接操作上下文窗口内的知识。在文件系统之前，用户必须复制粘贴内容给模型——这对自主 agent 不可行。世界已经在用文件系统做工作，模型自然在数十亿 token 的文件系统使用数据上训练过。

**文件系统是最基础的 harness 原语**，因为它解锁了：

- Agent 获得工作空间来读取数据、代码和文档
- 工作可以增量添加和卸载，而非把所有东西都放在上下文中
- 文件系统是天然的协作表面——多个 agent 和人类可以通过共享文件协调
- Git 为文件系统添加版本控制，agent 可以追踪工作、回滚错误、分支实验

---

## Bash + 代码：通用工具

**期望行为：** Agent 自主解决问题，无需人类为每个可能的操作预先设计工具。

今天主要的 agent 执行模式是 ReAct 循环：模型推理、通过 tool call 执行动作、观察结果、在 while 循环中重复。但 harness 只能执行它有逻辑的工具。

**解决方案：给 agent 一个通用工具——bash。** 模型可以通过编写和执行代码即时设计自己的工具，而非被限制在固定的预配置工具集中。

Bash + 代码执行是向"给模型一台电脑让它自己搞定"迈出的一大步。

---

## 沙箱与验证工具

**期望行为：** Agent 需要一个有正确默认值的环境，可以安全地行动、观察结果、取得进展。

在本地运行 agent 生成的代码有风险，单一本地环境无法扩展到大型 agent 工作负载。

**沙箱给 agent 安全的操作环境：**

- 安全、隔离的代码执行
- 可以允许列表命令和强制网络隔离
- 环境可以按需创建、扇出到多个任务、完成后销毁

**好的环境配备好的默认工具：** 预装语言运行时和包、git 和测试的 CLI、用于 web 交互和验证的浏览器。

浏览器、日志、截图和测试运行器给 agent 一种观察和分析工作的方式——帮助它们创建**自我验证循环**：写应用代码、运行测试、检查日志、修复错误。

---

## 记忆与搜索：持续学习

**期望行为：** Agent 应该记住它们见过的东西，并访问训练时不存在的信息。

模型除了权重和当前上下文中的内容外没有额外知识。不能编辑模型权重的情况下，"添加知识"的唯一方式是通过上下文注入。

**对于记忆：** 文件系统再次是核心原语。Harness 支持像 `AGENTS.md` 这样的记忆文件标准，在 agent 启动时注入上下文。Agent 添加和编辑这个文件时，harness 将更新后的文件加载到上下文中。这是一种持续学习形式——agent 从一个 session 持久存储知识，并将该知识注入未来 session。

**对于实时知识：** Web Search 和 MCP 工具（如 Context7）帮助 agent 访问超出知识截止日期的信息。

---

## 对抗 Context Rot

**期望行为：** Agent 性能不应在工作过程中退化。

**Context Rot** 描述了模型随着上下文窗口填满而在推理和完成任务上变差的现象。上下文是珍贵且稀缺的资源。

**今天的 harness 在很大程度上是好的上下文工程的交付机制。**

三种策略：

1. **Compaction（压缩）：** 当上下文窗口接近填满时，智能地卸载和摘要现有上下文窗口，让 agent 可以继续工作。

2. **Tool call offloading（工具调用卸载）：** 减少大型工具输出对上下文窗口的噪声影响。Harness 保留超过阈值 token 数的工具输出的头尾 token，将完整输出卸载到文件系统。

3. **Skills（技能）：** 解决 agent 启动时加载太多工具或 MCP 服务器到上下文中导致性能退化的问题。Skills 是 harness 层面的原语，通过**渐进式披露（progressive disclosure）** 解决这个问题。

---

## 长时间自主执行

**期望行为：** Agent 自主、正确地完成复杂工作，跨越长时间范围。

自主软件创建是 coding agent 的圣杯。但今天的模型存在过早停止、复杂问题分解困难、跨多个上下文窗口工作时不连贯等问题。

这是早期 harness 原语开始复合的地方：

- **文件系统和 git** 用于跨 session 追踪工作。Agent 在长任务中产出数百万 token，文件系统持久捕获工作以追踪进展。Git 让新 agent 快速了解最新工作和项目历史。

- **Ralph Loop** 用于继续工作。这是一种 harness 模式：通过 hook 拦截模型的退出尝试，在干净的上下文窗口中重新注入原始 prompt，强制 agent 继续工作直到完成目标。文件系统使这成为可能——每次迭代以新鲜上下文开始但从上一次迭代读取状态。

- **规划和自我验证** 保持在正轨。规划是模型将目标分解为一系列步骤。Harness 通过好的 prompting 和注入如何使用文件系统中计划文件的提醒来支持这一点。完成每步后，agent 通过自我验证检查正确性。Harness 中的 hook 可以运行预定义测试套件，失败时带着错误消息循环回模型。

---

## Harness 的未来

### 模型训练与 Harness 设计的耦合

今天的 agent 产品（如 Claude Code 和 Codex）是在模型和 harness 在循环中的情况下后训练的。这帮助模型改进 harness 设计者认为它们应该原生擅长的动作。

这创造了一个反馈循环：有用的原语被发现、添加到 harness、然后在训练下一代模型时使用。但这种共同进化有有趣的副作用——改变工具逻辑会导致更差的模型性能。

**但这不意味着最好的 harness 就是模型后训练时用的那个。** Terminal Bench 2.0 排行榜是好例子：Opus 4.6 在 Claude Code 中的得分远低于在其他 harness 中的得分。LangChain 展示了仅通过改变 harness 就将 coding agent 从 Top 30 提升到 Top 5。

### Harness 工程的方向

随着模型更强，今天 harness 中的一些东西会被模型吸收。模型会原生地更擅长规划、自我验证和长时间连贯性。

但就像 prompt engineering 今天仍然有价值一样，harness engineering 可能会继续对构建好的 agent 有用。Harness 不仅修补模型缺陷，还围绕模型智能工程化系统使其更有效。配置良好的环境、正确的工具、持久状态和验证循环让任何模型更高效——无论其基础智能如何。
