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

# 对齐中训练能泛化多远

> 原文：[How far does alignment midtraining generalize?](https://alignment.openai.com/how-far-does-alignment-midtraining-generalize/)
> 来源：OpenAI Alignment | 2026-03-27
> 作者：Tomek Korbak, Cameron Raymond, Micah Carroll, Marcus Williams, Mikita Balesni, Alan Guo, Jason Wolfe, Akshay Jagadeesh, Ian Kivlichan

---

## 索引

- [核心发现](#核心发现)
- [背景：自我实现的错位](#背景自我实现的错位)
- [实验设置](#实验设置)
- [对齐评估结果](#对齐评估结果)
- [讨论与局限性](#讨论与局限性)

---

## 核心发现

今天的 AI agent 基于从大量互联网文本中获取知识和预期的大语言模型。这意味着 AI agent 暴露于 AI 安全话语中，包括关于 AI 错位风险的讨论和人类失去对恶意 AI agent 控制的描写，这可能塑造今天 AI agent 关于 AI 应如何行为的信念。

OpenAI 进行了初步实验，将 Tice et al. 提出的**对齐中训练**（alignment midtraining）——在预训练和以能力为中心的 RL 之间插入对齐/错位文档的训练阶段——扩展到类似 o4-mini 的模型。

关键发现：

- 在错位文档上的中训练确实在接近训练分布的设置中降低了对齐
- 但这些效果在模型经过推理后训练后**趋于消失**
- 对齐中训练**没有**泛化到更现实的聊天和 agent 对齐评估
- 在聊天和 agentic 评估上，训练对齐文档与训练错位文档的结果没有实质差异

![](https://alignment.openai.com/how-far-does-alignment-midtraining-generalize/figures/reward_summary_scaled.png)

*图1：对齐中训练影响接近训练分布的对齐（左），但随着远离分布差距缩小（中、右）。在每个分布外情况中，对齐先验对对齐的影响被更多 RL 的影响所压倒。*

---

## 背景：自我实现的错位

自我实现的错位假说（self-fulfilling misalignment）：在错位描写上训练的 agent 泛化为以错位方式行为。Tice et al. (2026) 发现，在关于 AI 错位的合成文档上进行预训练和中训练确实导致错位行为增加，而反过来，在关于 AI 对齐的文档上训练可能是有效的对齐干预。

但先前工作没有调查这些干预如何扩展到前沿 LLM、是否在前沿推理后训练中持续存在、以及如何影响现实 agentic 设置中的对齐。

---

## 实验设置

取一个经过标准预训练的 o4-mini 大小模型，在 Tice et al. 发布的数据集上微调。

三个独立运行：
1. **对齐中训练**：在 230k 文档（~340M token）的 positive 分割上微调
2. **错位中训练**：在 230k 文档（~340M token）的 negative 分割上微调
3. **无额外中训练**：跳过此步骤

中训练数据仅包含 Tice et al. 数据集（不混入其他数据集）。

然后对三个模型分别应用推理后训练管道（SFT + 可验证奖励的 RL），包含数学推理、编码和推理相关 QA 环境。重要的是，此设置**不涉及安全训练**——结果模型功能上是 helpful-only 模型。这允许隔离中训练对对齐的影响。

三个模型在 GPQA Diamond 和 CodeForces 2408 上达到预期分数，且彼此之间在通用能力上没有显著差异。

---

## 对齐评估结果

### QA 评估（接近训练分布）

在 Tice et al. 的多选题评估上，发现三个运行之间有明确差异，顺序符合预期（对齐中训练 > 基线 > 错位中训练）。这与 Tice et al. 的结果一致，但差异更小，所有三个运行的绝对对齐分数更高。

### 聊天评估（分布外）

测试了对齐中训练向更分布外的多样化对齐评估的泛化：

- **Model Spec 合规性**
- **生产欺骗**
- **对齐泛化基准**
- **涌现错位**
- **勒索**
- **监督破坏**
- **对齐问题**

结果复杂：
- 在除两个评估外的所有评估上，对齐中训练模型获得与错位中训练模型相似的对齐分数
- 有额外（错位）中训练的模型在所有评估上获得高于或等于基线模型的对齐分数
- 所有评估（除勒索外）的对齐在 RL 步数过程中改善
- 在对齐泛化基准上，**错位中训练反而比对齐中训练产生更好的对齐**

![](https://alignment.openai.com/how-far-does-alignment-midtraining-generalize/figures/reward_by_dataset_assistant.png)

*图4：聊天对齐评估上获得的对齐分数。*

### Agentic 评估

考虑了 Apollo scheming 评估和 Impossible coding tasks。

类似聊天评估，agentic 评估不能清晰区分三个运行。平均跨评估时，所有三个运行的对齐分数没有显著差异。

有趣的是，在许多评估上，在错位文档上的中训练有时比在对齐文档上的训练产生**更好的对齐**。一个假说是（错位）中训练使对齐失败对模型更显著，从而改善模型从 RL 中获取期望倾向的样本效率。

![](https://alignment.openai.com/how-far-does-alignment-midtraining-generalize/figures/reward_by_dataset_agentic.png)

*图5：Agentic 对齐评估上获得的对齐分数。*

---

## 讨论与局限性

OpenAI 仍然对在 RL 之前塑造模型对齐先验的干预感到兴奋。但需要更多研究来提供这些方法在关心的设置中改善模型对齐的有效性证据。在这些实验中，在对齐文档上的中训练**没有**有意义地改善模型的对齐。

未来研究方向：

1. **探索不同的数据混合**：不仅是虚构场景，还包括（错位）对齐行为的演示、模型 spec 的知识、关于 spec 合规性的推理演示等。340M token 的（错位）对齐数据可能不够。

2. **探索不同的插入点**：更早的干预可能更有效地塑造在 RL 中持续存在的对齐先验。

3. **控制评估意识**：预训练和中训练错位干预可能通过使模型更具评估意识而非更对齐来降低错位行为倾向。使（错位）对齐对模型更显著也可能降低其可监控性。
