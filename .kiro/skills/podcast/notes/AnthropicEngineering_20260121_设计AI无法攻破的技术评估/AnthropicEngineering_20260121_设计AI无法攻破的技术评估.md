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

# Designing AI-Resistant Technical Evaluations：设计 AI 无法攻破的技术评估

> 原文：[Designing AI-Resistant Technical Evaluations](https://www.anthropic.com/engineering/AI-resistant-technical-evaluations)
> 来源：Anthropic Engineering | 2026-01-21
> 作者：Tristan Hume

---

## 背景

随着 AI 能力提升，评估技术候选人变得更难。今天能区分人类技能水平的 take-home 测试，明天可能被模型轻松解决——使其对评估无用。

Anthropic 性能工程团队自 2024 年初使用一个 take-home 测试，候选人为模拟加速器优化代码。超过 1000 名候选人完成了它，数十人现在在这里工作。

---

## 三次迭代的经验

### 第一版：被 AI 轻松解决

初始版本的优化任务，Claude 能达到与优秀候选人相当的分数。问题在于任务过于"模式匹配"——常见的优化技术可以直接应用。

### 第二版：增加领域特定复杂度

加入了需要理解模拟加速器特定架构的约束。AI 性能下降，但仍能通过暴力尝试获得不错分数。

### 第三版：需要真正的洞察力

设计了需要**发现非显而易见的性能瓶颈**的任务。关键不是应用已知技术，而是首先识别问题在哪里。这需要：
- 对系统行为的深度理解
- 形成和验证假设的能力
- 创造性地组合多种技术

---

## AI-Resistant 评估的设计原则

1. **需要发现而非应用：** 好的评估要求候选人发现问题，而非仅仅应用已知解决方案
2. **奖励深度理解：** 表面级别的模式匹配不应该得高分
3. **多层次的正确性：** 不是二元的对/错，而是有梯度的质量
4. **抵抗暴力搜索：** 解空间应该大到无法通过穷举找到答案
5. **需要整合多种信号：** 最好的答案需要综合来自不同来源的信息

---

## 更广泛的启示

这些原则不仅适用于招聘评估，也适用于 AI agent 的 eval 设计。如果你的 eval 可以被简单的模式匹配解决，它可能没有在测量你认为它在测量的东西。
