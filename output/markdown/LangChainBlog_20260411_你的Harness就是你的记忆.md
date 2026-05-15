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

# 你的 Harness 就是你的记忆

> 原文：[Your Harness Your Memory](https://www.langchain.com/blog/your-harness-your-memory)
> 来源：LangChain Blog | 2026-04-11
> 作者：Harrison Chase

---

**索引**

- [Agent Harness不会消失](#agent-harness不会消失)
- [Harness与记忆紧密绑定](#harness与记忆紧密绑定)
- [不拥有Harness就不拥有记忆](#不拥有harness就不拥有记忆)
- [记忆很重要，它创造锁定](#记忆很重要它创造锁定)
- [开放记忆，开放Harness](#开放记忆开放harness)

---

Harness与agent记忆紧密绑定。如果你使用封闭的harness——特别是如果它在专有API后面——你就是在选择将agent记忆的控制权让渡给第三方。记忆对于创造好的、有粘性的agentic体验极其重要。这创造了巨大的锁定。**记忆——因此也是harness——应该是开放的，这样你才拥有自己的记忆。**

---

## Agent Harness不会消失

构建agentic系统的"最佳"方式在过去三年里发生了巨大变化。ChatGPT出来时，你只能做简单的RAG链（LangChain）。然后模型变好了一点，可以创建更复杂的流程（LangGraph）。然后它们变得好很多，催生了一种新型脚手架——**agent harness**。Agent harness的例子包括Claude Code、Deep Agents、Pi（驱动OpenClaw）、OpenCode、Codex、Letta Code等等。

Agent harness不会消失。有时有一种观点认为模型会吸收越来越多的脚手架。这不是真的。已经发生的（并将继续发生的）是2023年需要的很多脚手架不再需要了。但这已经被其他类型的脚手架所取代。Agent，按定义，是LLM与工具和其他数据源交互。**围绕LLM总会有一个系统来促进这种交互。**

需要证据？当Claude Code的源代码泄露时，有**51.2万行代码**。那些代码就是harness。即使是世界上最好模型的制造者也在大力投资harness。当web搜索等功能被内置到OpenAI和Anthropic的API中时——它们不是"模型的一部分"。它们是坐在API后面的轻量级harness的一部分，通过tool calling编排模型与那些web搜索API。

---

## Harness与记忆紧密绑定

Sarah Wooders写了一篇很好的博客，讲为什么"记忆不是插件（它就是harness）"，我完全同意。有时有一种观点认为记忆是独立于任何特定harness的独立服务。在目前这个时间点，这不是真的。

Harness的一大职责是与上下文交互。正如Sarah所说：**要求把记忆插入agent harness，就像要求把驾驶插入汽车一样。** 管理上下文，因此也是记忆，是agent harness的核心能力和职责。

记忆只是上下文的一种形式。短期记忆（对话中的消息、大型tool call结果）由harness处理。长期记忆（跨会话记忆）需要由harness更新和读取。Sarah列出了harness与记忆绑定的许多其他方式：

- AGENTS.md或CLAUDE.md文件如何加载到上下文中？
- Skill元数据如何展示给agent？（在system prompt中？在system messages中？）
- Agent能否修改自己的系统指令？
- 什么在压缩中存活，什么丢失？
- 交互是否被存储并可查询？
- 记忆元数据如何呈现给agent？
- 当前工作目录如何表示？暴露多少文件系统信息？

现在，记忆作为一个概念还处于婴儿期。坦率地说，我们看到长期记忆通常不是MVP的一部分。首先你需要让agent整体工作起来，然后才能担心个性化。这意味着我们（作为一个行业）仍在摸索记忆。目前还没有众所周知的或通用的记忆抽象。

---

## 不拥有Harness就不拥有记忆

Harness与记忆紧密绑定。如果你使用封闭的harness，特别是如果它在API后面，你就不拥有你的记忆。这以几种方式表现：

**轻度糟糕：** 如果你使用有状态API（如OpenAI的Responses API或Anthropic的服务端压缩），你在他们的服务器上存储状态。如果你想换模型并恢复之前的对话线程——这不再可行。

**糟糕：** 如果你使用封闭的harness（如Claude Agent SDK，底层使用非开源的Claude Code），这个harness以你未知的方式与记忆交互。也许它在客户端创建了一些artifact——但它们的形状是什么，harness应该如何使用它们？这是未知的，因此无法从一个harness转移到另一个。

**最糟糕的**是另一种情况——当整个harness包括长期记忆都在API后面时。在这种情况下，你对记忆（包括长期记忆）零拥有权或可见性。你不知道harness（意味着你不知道如何使用记忆）。更糟的是——你甚至不拥有记忆！

当人们说"模型会吸收越来越多的harness"时——他们真正的意思是这些与记忆相关的部分会进入模型提供商提供的API后面。这非常令人担忧——它意味着**记忆将被锁定在单一平台、单一模型上**。

模型提供商有巨大的动机这样做。而且他们已经开始了。Anthropic推出了Claude Managed Agents，把所有东西都放在API后面，锁定在他们的平台上。即使整个harness不在API后面，模型提供商也有动机把越来越多的东西移到API后面——而且已经在这样做了。例如：即使Codex是开源的，它生成的是加密的压缩摘要（在OpenAI生态系统之外不可用）。

为什么他们这样做？因为**记忆很重要，它创造了仅靠模型无法获得的锁定**。

---

## 记忆很重要，它创造锁定

虽然记忆还处于早期，但所有人都清楚它很重要。它让agent随着用户交互而变得更好，让你建立数据飞轮。它让你的agent为每个用户个性化，构建一个适应他们的需求和使用模式的agentic体验。

没有记忆，你的agent很容易被任何有相同工具访问权的人复制。有了记忆，你建立了一个**专有数据集**——用户交互和偏好的数据集。这个专有数据集让你提供差异化的、越来越智能的体验。

到目前为止，切换模型提供商相对容易。它们有相似甚至相同的API。当然，你得稍微改改prompt，但那不难。但这一切都是因为它们是无状态的。一旦有任何状态关联，切换就难得多。因为这些记忆很重要。如果你切换，你就失去了对它的访问。

让我讲个故事。我内部有一个邮件助手。它建在Fleet（我们的无代码企业级OpenClaw构建平台）的模板上。这个平台内置了记忆，所以过去几个月我与邮件助手交互时它积累了记忆。几周前，我的agent被意外删除了。我很生气！我试图从同一模板创建一个agent——但体验差太多了。我不得不重新教它我所有的偏好、语气、一切。被删除的好处是——它让我意识到记忆可以多么强大和有粘性。

---

## 开放记忆，开放Harness

记忆需要被开放，由开发agentic体验的人拥有。它让你建立一个你实际控制的专有数据集。记忆（因此也是harness）应该与模型提供商分离。你应该想要尝试任何最适合你用例的模型的选择权。模型提供商有动机通过记忆创造锁定。

这就是为什么我们在构建**Deep Agents**。Deep Agents：

- 开源
- 模型无关
- 使用agents.md和skills等开放标准
- 有Mongo、Postgres、Redis等插件用于存储记忆
- 可通过LangSmith Deployment部署
- 可自托管，可部署在任何云上
- 可自带数据库作为记忆存储

**要拥有你的记忆，你需要使用开放的Harness。**
