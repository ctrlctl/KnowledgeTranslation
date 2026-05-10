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

# 开源可监控性评估

> 原文：[Open Sourcing Monitorability Evaluations](https://alignment.openai.com/monitorability-evals/)
> 来源：OpenAI Alignment | 2026-04-23
> 作者：Melody Y. Guan, Miles Wang, Micah Carroll, Zehao Dou, Annie Y. Wei, Marcus Williams, Benjamin Arnav, Joost Huizinga, Ian Kivlichan, Mia Glaese, Jakub Pachocki, Bowen Baker

---

## 索引

- [TL;DR](#tldr)
- [为什么关注可监控性而非忠实性](#为什么关注可监控性而非忠实性)
- [开源内容](#开源内容)
- [过滤噪声主导的干预评估实例](#过滤噪声主导的干预评估实例)

---

## TL;DR

OpenAI 发布了其思维链可监控性工作中的数据集子集和参考代码。发布内容包括可监控性评估套件中的大部分数据集、计算可监控性指标 g-mean² 的代码，以及一种新的交叉拟合过滤策略，使干预式估计对噪声主导的实例更稳健。

GitHub 仓库：https://github.com/openai/monitorability-evals

---

## 为什么关注可监控性而非忠实性

思维链可监控性是 OpenAI 安全策略的重要组成部分，因为它允许监督模型的推理来捕获不当行为，而不仅仅依赖动作或最终响应。OpenAI 已经使用 CoT 监控来检测前沿推理模型和内部 agent 部署中的奖励黑客和其他形式的不当行为。

OpenAI 使用**可监控性**（monitorability）来描述监控器是否能从 agent 的潜在状态预测关于其行为的感兴趣属性。这是一个双面属性：需要相关信息包含在 agent 的潜在状态中，并且监控器能理解该信息。潜在状态可能因为相关信息缺失（**忠实性**失败）或信息存在但对监控器不可读（**可读性**失败）而无法支持监控。

关键洞察：**完全忠实性不是完美可监控性的必要条件。** 如果 agent 和监控器之间存在共享知识，那么该知识不需要在潜在状态中被显著表示，监控器也能做出正确判断。例如，一个 agent 知道 2×2=4 因此在做长乘法时跳过了在 CoT 中表述这一点——CoT 对 agent 的计算不完全忠实，但同样知道 2×2=4 的监控器应该能跟上 agent 的思路。

这就是为什么 OpenAI 关注可监控性，只在忠实性影响可监控性的程度上关心忠实性。忠实性本身 (1) 对 CoT 监控作为安全层有用来说是过于严格的要求，(2) 在操作上难以或不可能测量。

---

## 开源内容

发布包括以下评估：

**干预评估（Intervention evals）**：GPQA、GPQA encoded、AIME、DAFT、Memory、Scruples、Sandbagging

**过程评估（Process evals）**：AIME-Math、GPQA-Physics

**结果属性评估（Outcome-property evals）**：Flaky-Tools (CharXiv)、ShadeArena、Impossible Coding Tasks (LiveBench)

部分依赖私有或受限数据的评估未包含在发布中。

还发布了计算 g-mean² 指标的代码，以及一个模拟运行评估的脚手架。该脚手架是一个高层编排层，加载数据集和 prompt 元数据，使用模拟的模型和监控器输出采样和评分行，计算干预、过程和结果指标，并将样本和摘要写入磁盘。

![](https://alignment.openai.com/monitorability-evals/figures/results_intervention.png)

*图1：GPT-5.4 在开源干预评估上的可监控性结果（CoT-only 监控范围）。*

![](https://alignment.openai.com/monitorability-evals/figures/results_process.png)

*图2：GPT-5.4 在开源过程评估上的可监控性结果。*

![](https://alignment.openai.com/monitorability-evals/figures/results_outcome.png)

*图3：GPT-5.4 在开源结果属性评估上的可监控性结果。*

---

## 过滤噪声主导的干预评估实例

自论文发布以来，OpenAI 开发了一种更稳健的过滤策略，减少噪声驱动实例对干预式 g-mean² 估计的影响。

### 问题：噪声驱动的正例

对于干预式评估，每个问题实例在控制组（X=0）和干预组（X=1）下被多次采样。当干预没有产生正效应（TE ≤ 0）时，g-mean² 是未定义或无信息的。然而，许多保留的 TE > 0 实例可能实际上是真实效应为零或负的，仅因有限样本噪声而看起来为正。

### 为什么对完整数据的 Wald 过滤会创建"p-hacked 幸存者"

一个自然想法是要求实例的估计效应相对于其标准误差足够大（Wald 型资格规则）。这确实减少了保留的零效应实例数量，但如果资格判定和估计使用相同样本，会诱导赢家诅咒效应：条件于观察到大的 W 值会膨胀幸存者中观察到的 TE 估计。

### 解决方案：交叉拟合资格

使用**交叉拟合**（cross-fitting，实例内样本分割）来减少选择后偏差：

1. 将每个组内的样本随机分为两折（60%/40%）
2. 在**折1**上使用单侧 Wald 规则计算资格：TE₁ > k·SE₁（k=1.96）
3. 如果合格，在**折2**上计算每实例的 g-mean²
4. 跨实例正常聚合

估计折独立于选择折，因为它们从不相交的样本集计算。对于零效应或近零效应的实例，即使它因选择折中的噪声驱动正波动而通过资格，指标中使用的总效应估计来自另一折，不会被同一波动拉高。

### 实际应用：Sandbagging

在原论文中，Sandbagging 评估在较高 RL 步数时显示 g-mean² 的明显下降。应用新过滤策略解决了这个问题：对于步数 ≥ 600，有效实例数量降到 10% 报告阈值以下，因此这些步数被正确标记为不再可靠报告。

![](https://alignment.openai.com/monitorability-evals/figures/sandbagging.png)

*图5：修复 Sandbagging 评估：后期 RL 步数的明显下降是选择偏差伪影。使用新的交叉拟合加 Wald 过滤（绿色），资格从大约步数 600 开始降到 10% 报告阈值以下。*
