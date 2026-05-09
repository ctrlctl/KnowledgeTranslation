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

# Agent Observability Needs Feedback to Power Learning：Agent 可观测性需要反馈来驱动学习

> 原文：[Agent Observability Needs Feedback to Power Learning](https://www.langchain.com/blog/agent-observability-needs-feedback-to-power-learning)
> 来源：LangChain Blog | 2026-04-01
> 作者：LangChain

---

## 核心论点

可观测性（看到 agent 做了什么）是必要的但不充分的。要让 agent 真正改进，需要**反馈循环**——将观察转化为行动。

---

## 从观察到学习

### 仅有 Trace 不够

Trace 告诉你 agent 做了什么。但如果没有人（或系统）评判这些行为的好坏，trace 只是数据，不是信号。

### 反馈的形式

- **人类反馈：** 用户标记结果好/坏、编辑 agent 输出
- **自动评估：** LLM-as-judge 对 trace 评分
- **隐式信号：** 用户是否采纳了建议、是否重试了请求
- **下游指标：** 任务完成率、用户留存、错误率

---

## 反馈驱动的改进循环

1. **收集 trace** → 2. **附加反馈** → 3. **分析模式** → 4. **改进 agent** → 重复

改进可以是：
- 更新 prompt 或 system instruction
- 修改工具描述
- 调整 harness 逻辑（重试策略、降级路径）
- 更新记忆/知识库

---

## 关键洞察

- **可观测性是基础设施，反馈是燃料**
- 没有反馈的可观测性只是监控；有反馈的可观测性是学习系统
- Agent 改进不是一次性的——是持续的循环
- 最好的 agent 团队将 eval 和反馈嵌入日常工作流，而非作为独立项目
