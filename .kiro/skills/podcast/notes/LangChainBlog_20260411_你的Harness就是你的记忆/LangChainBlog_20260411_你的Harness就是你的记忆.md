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

# Your Harness, Your Memory：你的 Harness 就是你的记忆

> 原文：[Your Harness Your Memory](https://www.langchain.com/blog/your-harness-your-memory)
> 来源：LangChain Blog | 2026-04-11
> 作者：Harrison Chase

---

## 目录

- [Agent Harness 不会消失](#agent-harness-不会消失)
- [Harness 与记忆紧密绑定](#harness-与记忆紧密绑定)
- [不拥有 Harness 就不拥有记忆](#不拥有-harness-就不拥有记忆)
- [记忆的重要性与锁定效应](#记忆的重要性与锁定效应)
- [开放记忆，开放 Harness](#开放记忆开放-harness)

---

## Agent Harness 不会消失

构建 agentic 系统的"最佳"方式在过去三年发生了巨大变化：简单 RAG chain → 复杂 flow（LangGraph）→ agent harness。

Agent harness 的例子包括 Claude Code、Deep Agents、Pi（驱动 OpenClaw）、OpenCode、Codex、Letta Code 等。

有时有一种观点认为模型会吸收越来越多的脚手架。**这不是真的。** 2023 年需要的很多脚手架确实不再需要了，但被其他类型的脚手架取代了。Agent 按定义是 LLM 与工具和其他数据源交互——围绕 LLM 促进这种交互的系统永远存在。

证据？Claude Code 源码泄露时有 51.2 万行代码。那些代码就是 harness。即使是世界上最好模型的制造者也在大力投资 harness。

当 web search 被内置到 OpenAI 和 Anthropic 的 API 中时——它们不是"模型的一部分"。它们是坐在 API 后面的轻量 harness 的一部分，通过 tool calling 编排模型与搜索 API。

---

## Harness 与记忆紧密绑定

Sarah Wooders 写了一篇很好的博客解释为什么"记忆不是插件（它就是 harness）"。

有时有观点认为记忆是独立于任何特定 harness 的独立服务。**目前这不是真的。**

Harness 的一大职责是与上下文交互。正如 Sarah 所说：

> 要求把记忆插入 agent harness，就像要求把驾驶插入汽车。管理上下文，因此管理记忆，是 agent harness 的核心能力和职责。

记忆只是上下文的一种形式：

- **短期记忆**（对话中的消息、大型工具调用结果）由 harness 处理
- **长期记忆**（跨 session 记忆）需要由 harness 更新和读取

Harness 与记忆绑定的具体方式：

- `AGENTS.md` 或 `CLAUDE.md` 文件如何加载到上下文？
- Skill 元数据如何展示给 agent？（在 system prompt 中？在 system message 中？）
- Agent 能否修改自己的系统指令？
- 什么在 compaction 中存活，什么丢失？
- 交互是否被存储并可查询？
- 记忆元数据如何呈现给 agent？
- 当前工作目录如何表示？暴露多少文件系统信息？

目前记忆作为概念还在婴儿期。长期记忆通常不是 MVP 的一部分——先让 agent 整体工作，再考虑个性化。行业仍在摸索记忆，还没有广为人知的通用抽象。

---

## 不拥有 Harness 就不拥有记忆

Harness 与记忆紧密绑定。**如果你使用封闭 harness，特别是在 API 后面的，你不拥有你的记忆。**

三个严重程度：

**轻度问题：** 使用有状态 API（如 OpenAI 的 Responses API 或 Anthropic 的服务端 compaction），状态存储在他们的服务器上。想换模型并恢复之前的线程——不再可行。

**中度问题：** 使用封闭 harness（如 Claude Agent SDK，底层用 Claude Code，不开源），这个 harness 以你未知的方式与记忆交互。也许它在客户端创建了一些 artifact——但形状是什么、harness 应该如何使用它们？未知，因此不可从一个 harness 转移到另一个。

**最严重：** 整个 harness 包括长期记忆都在 API 后面。你对记忆（包括长期记忆）零所有权或可见性。你不知道 harness（意味着不知道如何使用记忆），更糟的是——你甚至不拥有记忆本身。

当人们说"模型会吸收越来越多的 harness"时——他们真正的意思是这些记忆相关的部分会进入模型提供商的 API 后面。

**这非常令人警惕——意味着记忆将被锁定到单一平台、单一模型。**

模型提供商有极大动机这样做，而且已经开始了。Anthropic 推出了 Claude Managed Agents，把所有东西都放在 API 后面。即使整个 harness 不在 API 后面，提供商也在推动更多东西进入 API——例如 Codex 虽然开源，但生成加密的 compaction 摘要（在 OpenAI 生态系统外不可用）。

---

## 记忆的重要性与锁定效应

虽然记忆还早期，但所有人都清楚它很重要：

- 让 agent 随着用户交互变得更好
- 让你建立数据飞轮
- 让 agent 个性化到每个用户
- 构建适应用户欲望和使用模式的 agentic 体验

**没有记忆，** 你的 agent 可以被任何有相同工具访问权的人轻易复制。

**有了记忆，** 你建立了专有数据集——用户交互和偏好的数据集，让你提供差异化的、越来越智能的体验。

到目前为止切换模型提供商相对容易——它们有相似甚至相同的 API。但这都是因为它们是无状态的。一旦有任何状态关联，切换就难得多——因为这些记忆很重要，切换就意味着失去访问权。

作者的亲身经历：内部邮件助手因意外被删除，重新创建后体验差得多——必须重新教它所有偏好、语气、一切。这让他意识到记忆有多强大和粘性。

---

## 开放记忆，开放 Harness

记忆需要被开放，由开发 agentic 体验的人拥有。它让你建立一个你实际控制的专有数据集。

记忆（因此 harness）应该与模型提供商分离。你应该想要尝试任何最适合你用例的模型的灵活性。模型提供商有动机通过记忆创造锁定。

**为了拥有你的记忆，你需要使用开放的 Harness。**
