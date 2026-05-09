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

# The Think Tool：让 Claude 在复杂工具使用中停下来思考

> 原文：[The think tool](https://www.anthropic.com/engineering/claude-think-tool)
> 来源：Anthropic Engineering | 2025-03-20
> 作者：Anthropic

---

## 目录

- [什么是 Think Tool](#什么是-think-tool)
- [与 Extended Thinking 的区别](#与-extended-thinking-的区别)
- [适用场景](#适用场景)
- [实现方式](#实现方式)
- [性能表现](#性能表现)

---

## 什么是 Think Tool

Think tool 给 Claude 一个能力：在生成响应的过程中，加入一个额外的思考步骤——带有自己的专用空间——作为得出最终答案的一部分。

这是一个简单但强大的技术，在 Claude 的 agentic tool use 能力上带来了显著改进，包括：遵循策略、做出一致决策、处理多步问题——实现开销极小。

---

## 与 Extended Thinking 的区别

| | Extended Thinking | Think Tool |
|---|---|---|
| **时机** | Claude 开始生成响应**之前** | Claude 生成响应**过程中** |
| **作用** | 深度考虑和迭代计划后再行动 | 停下来思考是否有足够信息继续前进 |
| **适用** | 简单工具使用、非顺序工具调用、编码/数学 | 长链工具调用、策略密集环境、顺序决策 |
| **推理深度** | 更全面 | 更聚焦于模型发现的新信息 |

**Think tool 更适合的场景：**
- 需要调用复杂工具
- 在长链工具调用中仔细分析工具输出
- 导航有详细指南的策略密集环境
- 做顺序决策，每步建立在前一步之上，错误代价高

**2025年12月更新：** Extended thinking 能力已改进，大多数情况下推荐使用 extended thinking 而非专门的 think tool。

---

## 适用场景

1. **遵循复杂策略：** Agent 需要在多个约束条件下做决策时，think tool 让它在行动前检查是否满足所有条件。

2. **多步工具链：** 当 agent 需要连续调用多个工具，每次调用依赖前一次的结果时，think tool 让它在每步之间暂停分析。

3. **信息综合：** 从多个工具结果中综合信息做出判断时，think tool 提供专用空间来整合。

---

## 实现方式

实现极其简单——只是一个标准工具定义：

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

工具不执行任何操作——不获取新信息、不改变数据库，只是将思考追加到日志。这给了模型一个"暂停并思考"的显式机制。

---

## 性能表现

在 τ-Bench（一个测试 agent 在策略密集环境中遵循复杂指令能力的基准）上，think tool 带来了显著的性能提升。

**关键洞察：** 给模型一个显式的"思考空间"，比依赖它在生成过程中隐式推理要有效得多。这在需要仔细遵循多条规则、处理边缘情况、或在多个约束之间权衡时尤为明显。
