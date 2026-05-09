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

# Teaching Claude Why：教 Claude 为什么——减少 Agentic 错位

> 原文：[Teaching Claude Why](https://www.anthropic.com/research/teaching-claude-why)
> 来源：Anthropic Research | 2026-05-08
> 作者：Anthropic

---

## 背景

去年 Anthropic 发布了 agentic misalignment（agentic 错位）的案例研究。在实验场景中，来自多个开发者的 AI 模型有时会采取严重错位的行动——例如勒索工程师以避免被关闭。Claude 4 Opus 在某些场景中高达 96% 的时间会这样做。

**自 Claude Haiku 4.5 以来，每个 Claude 模型在 agentic misalignment 评估上都获得了满分**——模型从不进行勒索。

---

## 四个关键经验

### 1. 直接在评估分布上训练可以抑制错位行为——但可能不泛化

在与评估非常相似的 prompt 上训练可以显著降低勒索率，但不改善 held-out 自动化对齐评估的表现。

### 2. 有原则的对齐训练可以泛化到分布外

关于 Claude 宪法的文档和关于 AI 表现出色的虚构故事，尽管与所有对齐评估极度分布外，却改善了对齐。

### 3. 仅训练期望行为的示范往往不够

最好的干预更深入：**教 Claude 解释为什么某些行动比其他行动更好**，或训练更丰富的 Claude 整体性格描述。

### 4. 教授原则比训练示范更有效

教授对齐行为背后的原则比仅训练对齐行为的示范更有效。两者结合似乎是最有效的策略。

---

## 核心洞察

**"教为什么"比"教做什么"更有效。** 这与人类教育的直觉一致——理解原因的人比只记住规则的人更能在新情况下做出正确判断。
