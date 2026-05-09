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

# Auto-Review of Agent Actions Without Synchronous Human Oversight：无需同步人类监督的 Agent 行为自动审查

> 原文：[Auto-Review of Agent Actions Without Synchronous Human Oversight](https://alignment.openai.com/auto-review/)
> 来源：OpenAI Alignment | 2026-04-30
> 作者：Maja Trębacz et al.

---

## 核心思想

Auto-review 为部署编码 agent 提供了更安全的默认设置：使用一个独立的 agent 来批准或拒绝越界行为，无需人类实时在线。

---

## 问题

同步人类监督（每次 agent 做敏感操作都等人类批准）不可扩展：
- 人类不可能 24/7 在线
- 频繁中断破坏 agent 的长时间运行能力
- 对于低风险操作，人类审批是不必要的开销

但完全无监督又有风险——agent 可能执行有害操作。

---

## 解决方案：异步自动审查

用一个独立的"审查 agent"来评估主 agent 的行为：

1. 主 agent 提出要执行的操作
2. 审查 agent 评估该操作是否安全/合规
3. 如果安全 → 自动批准
4. 如果不确定 → 升级给人类
5. 如果明确危险 → 自动拒绝

---

## 设计考量

- **审查 agent 与主 agent 独立：** 避免共谋
- **审查标准明确：** 基于预定义的策略而非模糊判断
- **保守默认：** 不确定时拒绝而非批准
- **审计追踪：** 所有决策都被记录以供后续分析
- **人类升级路径：** 始终保留人类介入的通道

---

## 与 HITL 的关系

Auto-review 不是替代人类监督，而是在"完全人类监督"和"完全无监督"之间提供一个实用的中间地带。它让 agent 能在大多数情况下自主运行，同时在关键决策点保持安全保障。
