# 构建Multi-Agent研究系统

> 来源：output/markdown/AnthropicEngineering_20250613_构建Multi-Agent研究系统.md

## 要点摘录

### 为什么用 Multi-Agent

**原文：**
> Sub-agent 通过在各自的 context window 中并行运行来促进压缩——同时探索问题的不同方面，然后为主研究 agent 浓缩最重要的 token。每个 sub-agent 还提供关注点分离——不同的工具、prompt 和探索轨迹——减少路径依赖，实现彻底、独立的调查。

**理解/讨论：**
Multi-agent 的两个核心价值：
1. 并行压缩：sub-agent 在各自 context window 中并行探索，为主 agent 浓缩信息
2. 关注点分离：不同工具、prompt、探索轨迹，减少路径依赖

性能数据：multi-agent 比单 agent 高 90.2%；token 使用量解释 80% 的性能方差。代价：agent 用 4× 聊天 token，multi-agent 用 15× 聊天 token。

---

### 架构：编排者-工人模式

**原文：**
> 我们的 Research 系统使用编排者-工人（orchestrator-worker）模式的 multi-agent 架构：主 agent 协调过程，同时委派给并行运行的专门化 sub-agent。

**理解/讨论：**
完整流程：用户查询 → LeadResearcher 规划（存入 Memory 防 context 截断）→ 创建 sub-agent 并行搜索 → 综合结果 → CitationAgent 处理引用 → 返回最终结果。与传统 RAG 的区别：多步动态搜索 vs 静态检索相似 chunk。

---

### Prompt Engineering 与工具设计

**原文要点：**
> - 像你的 agent 一样思考：在 Console 中用精确 prompt 和工具构建模拟
> - 教编排者如何委派：每个 sub-agent 需要目标、输出格式、工具和来源指导、清晰的任务边界
> - 按查询复杂度缩放努力：简单事实 1 agent / 复杂研究 10+ sub-agent
> - 让 agent 改进自身：给定 prompt 和失败模式，模型能诊断并建议改进，任务完成时间减少 40%
> - 先广后窄：从短而广的查询开始再深入
> - 并行工具调用：研究时间减少高达 90%

**理解/讨论：**
核心思路：观察 agent 失败 → 改工具/prompt → 让 agent 自己改进自己。委派时给 sub-agent 的四要素（目标、格式、工具指导、边界）是面试可展开的点。

---

### 评估 Multi-Agent 系统

**原文要点：**
> - 立即用小样本开始评估（~20 个查询），不要因为觉得只有大规模 eval 才有用就推迟
> - LLM-as-judge 按 rubric 评估：事实准确性、引用准确性、完整性、来源质量、工具效率
> - 人类测试者发现 eval 遗漏的边界情况（如 agent 选择 SEO 内容农场而非权威来源）

**理解/讨论：**
LLM-as-judge 擅长评估内容正确性，但不擅长评估来源质量、信息可信度这类需要人类判断力的维度。评估需要自动 eval + 人工评估结合。关键：不要等大规模 eval，小样本就能发现大变化。

---

### 生产可靠性

**原文要点：**
> - Agent 是有状态的，错误会累积。让 agent 知道工具正在失败并让它适应，效果出奇地好。
> - 调试需要完整的生产追踪，监控决策模式而非对话内容。
> - 使用 rainbow deployments 逐步转移流量。
> - 同步执行创造瓶颈，异步执行增加协调复杂度。

**理解/讨论：**
核心教训：agentic 系统中微小变化级联为大的行为变化。不能从头重启（昂贵+用户沮丧），要从错误处恢复。Rainbow deployment 是 agent 系统特有的部署策略——因为 agent 高度有状态且持续运行。

---

### 附录技巧

**原文要点：**
> - 终态评估：评估最终状态而非逐轮过程
> - 长对话管理：总结已完成阶段存入外部记忆，接近 context 限制时生成新 sub-agent 交接
> - Sub-agent 输出到文件系统：避免"传话游戏"信息丢失，减少 token 开销

**理解/讨论：**
三个实用技巧。"输出到文件系统"解决了 multi-agent 中信息在层层传递中丢失的问题——sub-agent 直接写入持久存储，主 agent 只拿轻量引用。
