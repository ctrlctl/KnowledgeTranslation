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

# Demystifying Evals for AI Agents：揭秘 AI Agent 评估

> 原文：[Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
> 来源：Anthropic Engineering | 2026-01-09
> 作者：Anthropic

---

## 目录

- [为什么 Agent 难以评估](#为什么-agent-难以评估)
- [评估的三个层次](#评估的三个层次)
- [组件评估](#组件评估)
- [轨迹评估](#轨迹评估)
- [端到端评估](#端到端评估)
- [实践建议](#实践建议)

---

## 为什么 Agent 难以评估

好的评估帮助团队更自信地发布 AI agent。没有评估，容易陷入被动循环——只在生产中发现问题，修一个故障又制造新的。

Agent 在多轮中运行：调用工具、修改状态、基于中间结果适应。这些让 agent 有用的能力——自主性、智能、灵活性——也让它们更难评估。

传统软件评估是确定性的：给定输入，检查输出。Agent 评估面临的独特挑战：

- **非确定性：** 同一输入可能产生不同但都正确的执行路径
- **多步骤：** 错误可能在任何步骤发生，且会级联
- **工具交互：** Agent 与外部系统交互，引入额外变量
- **状态修改：** Agent 改变环境状态，使测试隔离困难

---

## 评估的三个层次

### 组件评估（Component Evals）

测试 agent 的单个能力——工具选择、参数提取、响应格式化。快速、便宜、确定性高。

适用于：验证特定工具是否被正确调用、检查输出格式、测试边缘情况处理。

### 轨迹评估（Trajectory Evals）

评估 agent 的决策序列——不只是最终结果，还有到达那里的路径。

适用于：检查 agent 是否遵循预期策略、是否做了不必要的工具调用、是否在正确时机寻求澄清。

可以用 LLM-as-judge 来评估轨迹质量。

### 端到端评估（End-to-End Evals）

在真实或模拟环境中运行完整任务，验证最终结果。最接近生产行为，但最慢最贵。

适用于：回归测试、发布前验证、比较不同模型或 prompt 版本。

---

## 实践建议

1. **从组件评估开始**——快速迭代，建立基线
2. **用轨迹评估捕获策略问题**——agent 可能得到正确答案但用了错误方式
3. **端到端评估作为最终门控**——发布前的信心检查
4. **评估应该是持续的**——不是一次性的，而是 CI/CD 的一部分
5. **用真实数据**——避免过于简单的合成场景
6. **接受非确定性**——多次运行取统计结果，而非期望每次完全相同
