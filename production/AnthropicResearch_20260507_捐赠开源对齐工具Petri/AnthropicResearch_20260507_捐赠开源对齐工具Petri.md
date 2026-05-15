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

# 捐赠我们的开源对齐工具

> 原文：[Donating our open-source alignment tool](https://www.anthropic.com/research/donating-open-source-petri)
> 来源：Anthropic Research | 2026-05-07
> 作者：Anthropic

---

## 索引

- [Petri 简介](#petri-简介)
- [Petri 3.0 的主要变化](#petri-30-的主要变化)
- [捐赠给 Meridian Labs](#捐赠给-meridian-labs)

---

## Petri 简介

2025 年 10 月，我们发布了 [Petri](https://www.anthropic.com/research/petri-open-source-auditing)——一个开源的对齐测试工具箱，可以应用于任何大语言模型。Petri 是 Anthropic Fellows 项目的产物，能够快速、简便地测试 AI 模型是否存在令人担忧的倾向，比如**欺骗、谄媚、配合有害请求**。它是我们为整个 AI 开发社区构建开放对齐工具这一努力的一部分。

自 Claude Sonnet 4.5 以来，Petri 一直是每个 Claude 模型对齐评估的组成部分。它的工作方式是：一个独立的 **"auditor"模型**（审计员）模拟一系列对齐相关场景，让被测模型在其中行动；然后另一个 **"judge"模型**（裁判）对产生的对话记录进行错位行为评分。

外部组织也在使用 Petri。例如，英国 AI 安全研究所（AISI）将其作为评估模型破坏 AI 研究倾向的[主要方法](https://arxiv.org/abs/2604.00788)。

---

## Petri 3.0 的主要变化

我们现在将 Petri 更新到第三版，主要变化如下：

- **适应性（Adaptability）**。Petri 3.0 做了重大架构调整，将审计员模型和目标模型拆分为可独立调整的组件，让用户能够将其适配到更多用途。

- **真实性（Realism）**。尽管对齐研究者努力让测试看起来真实，模型往往能从设置中的各种人为痕迹推断出自己正在被测试。一旦模型意识到正在被评估，研究者就无法观察到它*一般情况下*的行为了。Petri 的一个附加组件 **"Dish"** 大幅提升了测试的真实性——例如使用模型真实的 system prompt 和真实的 scaffold（包裹模型、帮助其达成目标的外部软件），就像在真正的生产部署中一样运行测试。

- **深度（Depth）**。我们将 Petri 与另一个开源对齐工具 [Bloom](https://www.anthropic.com/research/bloom) 做了集成。Bloom 能对特定选定行为进行更深入的评估，与 Petri 更广泛的扫描式方法形成互补。

---

## 捐赠给 Meridian Labs

我们还给了 Petri 一个新家。我们将其开发移交给了 [Meridian Labs](https://meridianlabs.ai/)——一个 AI 评估领域的非营利组织。这一举措类似于我们之前将 Model Context Protocol（MCP）[捐赠](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)给 Linux 基金会——目的是确保 Petri **独立于任何 AI 实验室**，让其评估结果在行业内外都被视为中立和可信的。

作为 Meridian Labs 的一部分，Petri 加入了 [Inspect](https://inspect.aisi.org.uk/) 和 [Scout](https://meridianlabs-ai.github.io/inspect_scout/) 等工具，共同构建一个对实验室、独立研究者和政府都开放的技术栈——在可靠的 AI 模型行为测试比以往任何时候都重要的当下。

更多关于 Petri 3.0 的信息可以在 [Meridian Labs 博客](https://meridianlabs.ai/blog/posts/introducing-petri-3/)上阅读。安装和使用说明见 [Petri 官网](https://meridianlabs-ai.github.io/inspect_petri/)。
