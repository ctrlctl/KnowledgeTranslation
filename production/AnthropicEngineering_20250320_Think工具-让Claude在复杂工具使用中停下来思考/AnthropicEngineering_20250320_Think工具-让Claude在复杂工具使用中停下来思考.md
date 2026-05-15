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

# Think 工具：让 Claude 在复杂工具使用中停下来思考

> 原文：[The "think" tool: Enabling Claude to stop and think in complex tool use situations](https://www.anthropic.com/engineering/claude-think-tool)
> 来源：Anthropic Engineering | 2025-03-20
> 作者：Anthropic

---

## 索引

- [什么是"Think"工具？](#什么是think工具)
- [在 τ-Bench 上的表现](#在-τ-bench-上的表现)
- [在 SWE-Bench 上的表现](#在-swe-bench-上的表现)
- [何时使用"Think"工具](#何时使用think工具)
- [实现最佳实践](#实现最佳实践)
- [何时不使用"Think"工具](#何时不使用think工具)
- [开始使用](#开始使用)
- [结论](#结论)

---

> **2025年12月15日更新：** Extended thinking 能力自初始发布以来已有改进，我们现在建议在大多数情况下使用该功能而非专门的 think 工具。Extended thinking 提供类似的好处——给 Claude 空间来推理复杂问题——同时有更好的集成和性能。详见 extended thinking 文档。

随着我们持续增强 Claude 的复杂问题解决能力，我们发现了一种特别有效的方法：一个 **"think" 工具**，它在复杂任务中为结构化思考创造专门的空间。这个简单而强大的技术——如下文所述，它与 Claude 新的"extended thinking"能力不同——在 Claude 的 agentic 工具使用能力上带来了显著提升。包括遵循策略、做出一致决策、处理多步骤问题，且实现开销极小。

在这篇文章中，我们将探讨如何在不同应用中实现"think"工具，基于经过验证的 benchmark 结果分享开发者的实用指南。

---

## 什么是"Think"工具？

通过"think"工具，我们让 Claude 能够在得出最终答案的过程中加入一个额外的思考步骤——带有自己专属的空间。虽然听起来和 extended thinking 类似，但它们是不同的概念。

**Extended thinking** 关注的是 Claude 在开始生成响应之前做什么。Claude 在采取行动前深入思考并迭代其计划。

**"Think"工具** 则是让 Claude 在开始生成响应之后，添加一个步骤来停下来思考——它是否已经拥有继续前进所需的所有信息。这在执行长链工具调用或与用户的长多步对话中特别有用。

这使得"think"工具更适合以下场景：Claude 仅凭用户查询无法获得制定响应所需的全部信息，需要处理外部信息（如工具调用结果中的信息）。"think"工具中 Claude 进行的推理不如 extended thinking 那么全面，更聚焦于模型新发现的信息。

我们建议在较简单的工具使用场景（如非顺序工具调用或直接的指令遵循）中使用 extended thinking。Extended thinking 也适用于不需要 Claude 调用工具的场景，如编码、数学和物理。

**"Think"工具更适合以下场景：**
- Claude 需要调用复杂工具
- 在长链工具调用中仔细分析工具输出
- 在有详细指南的策略密集型环境中导航
- 做出顺序决策——每一步都建立在前一步之上，且错误代价高昂

以下是使用标准工具规范格式的示例实现（来自 τ-Bench）：

```json
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {
        "type": "string",
        "description": "A thought to think about."
      }
    },
    "required": ["thought"]
  }
}
```

---

## 在 τ-Bench 上的表现

我们使用 τ-bench（tau-bench）评估了"think"工具。这是一个综合性 benchmark，旨在测试模型在真实客服场景中使用工具的能力，"think"工具是该评估标准环境的一部分。

τ-bench 评估 Claude 的能力包括：
- 在与模拟用户的真实对话中导航
- 一致地遵循复杂的客服 agent 策略指南
- 使用各种工具访问和操作环境数据库

主要评估指标是 **pass^k**，它衡量给定任务的所有 k 次独立试验全部成功的概率，在所有任务上取平均。与其他 LLM 评估中常见的 pass@k 指标（衡量 k 次试验中至少一次成功）不同，pass^k 评估的是**一致性和可靠性**——这对客服应用至关重要，因为一致遵循策略是必需的。

### 性能分析

我们的评估比较了几种不同配置：
- 基线（无"think"工具，无 extended thinking 模式）
- 仅 Extended thinking 模式
- 仅"Think"工具
- "Think"工具 + 优化 prompt（航空领域）

结果显示，当 Claude 3.7 有效使用"think"工具时，在 benchmark 的"航空"和"零售"客服领域都有显著提升：

- **航空领域：** "think"工具 + 优化 prompt 在 pass^1 指标上达到 0.570，而基线仅为 0.370——**相对提升 54%**
- **零售领域：** 仅"think"工具就达到 0.812，而基线为 0.783

![](images/fig_01.png)

*图：Claude 3.7 Sonnet 在 Tau-Bench "航空"领域四种配置下的表现*

| 配置 | k=1 | k=2 | k=3 | k=4 | k=5 |
|------|-----|-----|-----|-----|-----|
| "Think" + Prompt | 0.584 | 0.444 | 0.384 | 0.356 | 0.340 |
| "Think" | 0.404 | 0.254 | 0.186 | 0.140 | 0.100 |
| Extended thinking | 0.412 | 0.290 | 0.232 | 0.192 | 0.160 |
| 基线 | 0.332 | 0.206 | 0.148 | 0.116 | 0.100 |

航空领域的最佳表现来自将"think"工具与优化 prompt 配对——该 prompt 给出了分析客户请求时应使用的推理方法示例。以下是优化 prompt 的示例：

```
## Using the think tool

Before taking any action or responding to the user after receiving tool results, 
use the think tool as a scratchpad to:
- List the specific rules that apply to the current request
- Check if all required information is collected
- Verify that the planned action complies with all policies
- Iterate over tool results for correctness
```

特别有趣的是不同方法的对比。使用"think"工具 + 优化 prompt 的结果显著优于 extended thinking 模式（后者表现与未提示的"think"工具相似）。

单独使用"think"工具（无提示）相比基线有所提升，但仍不及优化方案。**"think"工具 + 优化提示的组合以显著优势取得了最强表现**，这可能是因为 benchmark 的航空策略部分高度复杂，模型从被给予"如何思考"的示例中获益最多。

在零售领域，我们也测试了各种配置：

![](images/fig_02.png)

*图：Claude 3.7 Sonnet 在 Tau-Bench "零售"领域三种配置下的表现*

| 配置 | k=1 | k=2 | k=3 | k=4 | k=5 |
|------|-----|-----|-----|-----|-----|
| "Think" + 无 prompt | 0.812 | 0.735 | 0.685 | 0.650 | 0.626 |
| Extended thinking | 0.770 | 0.681 | 0.623 | 0.581 | 0.548 |
| 基线 | 0.783 | 0.695 | 0.643 | 0.607 | 0.583 |

"Think"工具即使没有额外提示也达到了最高的 pass^1 分数 0.812。零售策略明显比航空领域更容易导航，Claude 仅凭有一个思考空间就能提升表现，无需进一步指导。

### 来自 τ-Bench 分析的关键洞察

我们的详细分析揭示了几个有助于有效实现"think"工具的模式：

- **在困难领域，提示非常重要。** 仅仅提供"think"工具可能会有所改善，但在困难领域将其与优化提示配对会产生显著更好的结果。不过，较简单的领域可能仅凭有"think"的访问权就能受益。
- **跨试验的一致性提升。** 使用"think"带来的改进在 pass^k 直到 k=5 时都得以维持，表明该工具帮助 Claude 更有效地处理边缘情况和异常场景。

---

## 在 SWE-Bench 上的表现

在评估 Claude 3.7 Sonnet 时，我们的 SWE-bench 设置中也加入了类似的"think"工具，这为达到 0.623 的 state-of-the-art 分数做出了贡献。改编后的"think"工具定义如下：

```json
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or make any changes to the repository, but just log the thought. Use it when complex reasoning or brainstorming is needed. For example, if you explore the repo and discover the source of a bug, call this tool to brainstorm several unique ways of fixing the bug, and assess which change(s) are likely to be simplest and most effective. Alternatively, if you receive some test results, call this tool to brainstorm ways to fix the failing tests.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {
        "type": "string",
        "description": "Your thoughts."
      }
    },
    "required": ["thought"]
  }
}
```

我们的实验（使用"think"工具 n=30 样本，不使用 n=144 样本）显示，加入该工具的独立效果平均提升了 1.6%（Welch's t 检验：t(38.89) = 6.71, p < .001, d = 1.47）。

---

## 何时使用"Think"工具

基于这些评估结果，我们确定了 Claude 从"think"工具中获益最多的具体场景：

- **工具输出分析：** 当 Claude 需要在行动前仔细处理之前工具调用的输出，且可能需要回溯其方法时
- **策略密集型环境：** 当 Claude 需要遵循详细指南并验证合规性时
- **顺序决策：** 当每个行动都建立在前一个之上，且错误代价高昂时（常见于多步骤领域）

---

## 实现最佳实践

为了从 Claude 的"think"工具中获得最大收益，我们基于 τ-bench 实验推荐以下实现实践：

### 1. 使用领域特定示例进行策略性提示

最有效的方法是提供关于何时以及如何使用"think"工具的清晰指令，如用于 τ-bench 航空领域的那个。提供针对你特定用例定制的示例能显著改善模型使用"think"工具的效果：
- 推理过程中期望的详细程度
- 如何将复杂指令分解为可执行步骤
- 处理常见场景的决策树
- 如何检查是否已收集所有必要信息

### 2. 将复杂指导放在 system prompt 中

我们发现，当指令较长和/或复杂时，将关于"think"工具的说明放在 system prompt 中比放在工具描述本身中更有效。这种方法提供了更广泛的上下文，帮助模型更好地将思考过程整合到其整体行为中。

---

## 何时不使用"Think"工具

虽然"think"工具能带来实质性改进，但它并非适用于所有工具使用场景，且确实会增加 prompt 长度和输出 token 的成本。具体来说，我们发现"think"工具在以下场景中不会带来改进：

- **非顺序工具调用：** 如果 Claude 只需要进行单次工具调用或多次并行调用来完成任务，添加"think"不太可能有任何改进
- **简单指令遵循：** 当 Claude 不需要遵守很多约束，且其默认行为已经足够好时，额外的"think"不太可能带来收益

---

## 开始使用

"Think"工具是对你的 Claude 实现的一个简单补充，只需几步就能带来有意义的改进：

1. **用 agentic 工具使用场景测试。** 从有挑战性的用例开始——那些 Claude 目前在长工具调用链中的策略合规或复杂推理方面表现不佳的场景。
2. **添加工具定义。** 实现一个针对你领域定制的"think"工具。它只需极少代码但能实现更结构化的推理。同时考虑在 system prompt 中加入关于何时以及如何使用该工具的说明，附带与你领域相关的示例。
3. **监控和优化。** 观察 Claude 在实践中如何使用该工具，调整你的 prompt 以鼓励更有效的思考模式。

最好的一点是，添加这个工具在性能结果方面几乎没有负面影响。除非 Claude 决定使用它，否则它不会改变外部行为，也不会干扰你现有的工具或工作流。

---

## 结论

我们的研究表明，"think"工具能显著增强 Claude 3.7 Sonnet 在需要策略遵循和长链工具调用推理的复杂任务上的表现¹。"Think"不是万能方案，但对于正确的用例，它以极小的实现复杂度提供了实质性收益。

我们期待看到你如何使用"think"工具来构建更强大、更可靠、更透明的 AI 系统。

---

¹ 虽然我们的 τ-Bench 结果聚焦于 Claude 3.7 Sonnet 使用"think"工具的改进，但实验表明 Claude 3.5 Sonnet (New) 在相同配置下也能获得性能提升，说明这种改进可以泛化到其他 Claude 模型。

---

