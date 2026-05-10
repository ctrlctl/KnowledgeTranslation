<style>
body, .markdown-body { font-family: "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, serif; font-size: 15px; line-height: 2; max-width: 38em; margin: 0 auto; padding: 2em; color: #2c2c2c; background: #faf8f5; }
</style>

> 原文：[A Practical Approach to Verifying Code at Scale](https://alignment.openai.com/scaling-code-verification/)
> 来源：OpenAI Alignment | 2025-12-01
> 作者：Maja Trębacz, Sam Arnesen 等（Codex 团队）

## 索引

- [为什么需要自动代码审查](#为什么需要自动代码审查)
- [精确度比召回率更重要](#精确度比召回率更重要)
- [仓库级工具和执行是必要的](#仓库级工具和执行是必要的)
- [部署经验](#部署经验)

---

## 为什么需要自动代码审查

随着自主协作编码系统的普及，产出的代码量迅速超出彻底人工审查的极限。差距越大，AI 编写的代码引入严重 bug 和漏洞的风险就越大——无论是意外还是故意。

我们不能假设代码生成系统是可信或正确的；**必须检查它们的工作**。自动代码审查是一种实用的输出监控器，作为纵深防御策略的一部分，补充 CoT 监控、行动监控、内部激活监控、行为测试和诚实训练等其他安全工作。

本文分享了为 gpt-5-codex 和 gpt-5.1-codex-max 训练专用 agentic 代码审查器的经验。

---

## 精确度比召回率更重要

防御往往不是因为技术上错误而失败，而是因为太不实用以至于用户选择绕过它们。慢、嘈杂或笨重的系统会被绕过。

部署代码审查 agent 时，明确接受了一个权衡：**适度降低召回率以换取高信号质量和开发者信任**。先优化信噪比，然后才在不损害可靠性的前提下推高召回率。

我们希望发现最大化以下公式的结果：

$$P(\text{correct}) \times C_{\text{saved}} - C_{\text{human verification}} - P(\text{incorrect}) \times C_{\text{false alarm}}$$

技术上正确但更偏风格性质的评论甚至可能产生负效用（如在个人研究笔记本中指出注释拼写错误可能不值得）。

---

## 仓库级工具和执行是必要的

之前的代码审查尝试大多只提供变更的 diff 和可选的简短周围上下文。这产生最快的审查但也最不准确——审查器缺乏理解变更影响所需的上下文。

GPT-5.1-Codex 的审查器添加了：
- 推理能力
- 工具使用
- 仓库级上下文
- 精确度/延迟目标

给审查器仓库范围的工具和执行访问同时改善了召回率和精确度。

---

## 部署经验

在 OpenAI 内部，每个 PR 都自动审查，许多工程师在推送前在 Codex CLI 中运行 `/review`。模型已经保护了高价值实验并捕获了阻止发布的问题。

关键设计决策：
- 允许精确度和召回率的权衡以及其他指南通过自定义任务指令或仓库级 AGENTS.md 规范来可控
- 接受可衡量的权衡：适度降低召回率换取高信号质量
- 使审查器可以被开发者信任，从而实际被使用而非绕过
