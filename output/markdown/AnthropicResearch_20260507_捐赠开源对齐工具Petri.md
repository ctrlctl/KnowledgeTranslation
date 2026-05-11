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

- [Petri 是什么](#petri-是什么)
- [Petri 3.0 的主要变化](#petri-30-的主要变化)
- [捐赠给 Meridian Labs](#捐赠给-meridian-labs)

---

## Petri 是什么

2025 年 10 月，Anthropic 发布了 [Petri](https://www.anthropic.com/research/petri-open-source-auditing)——一个开源的对齐测试工具箱，可以应用于任何大语言模型。Petri 作为 Anthropic Fellows 项目的一部分开发，可以快速、简便地测试 AI 模型是否存在令人担忧的倾向，如**欺骗、谄媚和配合有害请求**。

Petri 自 Claude Sonnet 4.5 以来一直是每个 Claude 模型对齐评估的一部分。它的工作方式是：一个单独的"审计员"模型模拟一系列对齐相关场景，让被测模型在其中行动，然后另一个"裁判"模型对产生的对话记录进行错位行为评分。

外部组织也在使用 Petri——例如英国 AI 安全研究所（AISI）将其作为评估模型破坏 AI 研究倾向的[主要工具](https://arxiv.org/abs/2604.00788)。

---

## Petri 3.0 的主要变化

1. **适应性（Adaptability）**：重大架构变更，将审计员模型和目标模型拆分为可独立调整的组件，允许用户适配更多用途。

2. **真实性（Realism）**：尽管对齐研究者努力让测试看起来真实，模型往往能从设置中的各种人为痕迹推断出自己正在被测试。如果模型意识到正在被评估，研究者就无法看到模型*一般情况下*的行为。Petri 的附加组件 **"Dish"** 让设置更加真实——例如使用模型真实的 system prompt 和真实的 scaffold（包裹模型帮助其达成目标的软件），就像在真正的模型部署中一样。

3. **深度（Depth）**：Petri 现在与另一个开源对齐工具 [Bloom](https://www.anthropic.com/research/bloom) 集成，Bloom 可以对特定选定行为进行更深入的评估（相比 Petri 更广泛的方法）。

---

## 捐赠给 Meridian Labs

Anthropic 将 Petri 的开发移交给了 [Meridian Labs](https://meridianlabs.ai/)——一个 AI 评估非营利组织。这一举措类似于之前将 MCP（Model Context Protocol）[捐赠](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)给 Linux 基金会——确保 Petri 独立于任何 AI 实验室，使其结果被行业内外视为中立和可信的。

作为 Meridian Labs 的一部分，Petri 加入了 [Inspect](https://inspect.aisi.org.uk/) 和 [Scout](https://meridianlabs-ai.github.io/inspect_scout/) 等其他工具，构建一个对实验室、独立研究者和政府都开放的技术栈——在可靠的 AI 模型行为测试比以往任何时候都重要的时刻。

---

## 要点

- **Petri** 是开源对齐测试工具，用"审计员+裁判"模式评估模型的错位行为
- **Dish** 附加组件解决了"模型知道自己在被测试"的问题，用真实 prompt 和 scaffold 运行测试
- 捐赠给独立非营利组织确保评估结果的中立性和可信度
- 与 Bloom 集成实现从广度筛查到深度评估的完整流程
