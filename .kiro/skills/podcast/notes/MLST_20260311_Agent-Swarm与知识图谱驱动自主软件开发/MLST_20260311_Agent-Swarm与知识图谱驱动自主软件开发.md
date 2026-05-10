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

# Agent Swarm 与知识图谱驱动自主软件开发

> 原文：[Agent Swarms and Knowledge Graphs for Autonomous Software Development - #763](https://twimlai.com/podcast/twimlai/agent-swarms-knowledge-graphs-autonomous-software-development)
> 来源：Machine Learning Street Talk (TWIML) | 2026-03-11
> 嘉宾：Sudant Pardeshi（Blitzy 联合创始人兼 CTO，前 NVIDIA）

---

## 索引

- [自主开发 vs 辅助开发](#自主开发-vs-辅助开发)
- [Spec 的局限性](#spec-的局限性)
- [Context Engineering 与 Agentic Engineering](#context-engineering-与-agentic-engineering)
- [有效 Context Window 的真相](#有效-context-window-的真相)
- [知识图谱作为锚点](#知识图谱作为锚点)
- [Multi-Agent 的两种模式](#multi-agent-的两种模式)
- [Agent Swarm：从多线程到超并行](#agent-swarm从多线程到超并行)
- [并发冲突的解决](#并发冲突的解决)
- [动态 Agent 设计](#动态-agent-设计)
- [Agents.md 为什么不能规模化](#agentsmd-为什么不能规模化)
- [评估的困境](#评估的困境)
- [代码质量与可维护性](#代码质量与可维护性)
- [自强化知识图谱](#自强化知识图谱)

---

## 自主开发 vs 辅助开发 [04:29]

软件开发是 AI 最佳应用场景，因为代码**可验证**——可编译、可测试、可视化，存在正确答案。

两个层次：
- **辅助开发**：Copilot、CLI/IDE 工具，异步执行任务
- **自主开发**：点击 build，输出已测试、已验证的 PR，无错误，符合预期

核心挑战不是生成代码（代码已经是商品），而是**代码接受度**——符合标准、安全、可投产的代码。

关键区分：AI 在 greenfield 项目上表现出色，但在**企业级已有代码库**上工作时，因为信息量和边界条件太多，工具频繁失败。

---

## Spec 的局限性 [07:37]

Spec 对 agent 有锚定作用，但不够：

- 有些任务的依赖关系事先不清楚（如不知道后端数据库 schema）
- 新信息会改变架构决策
- 即使有完美 spec，大型项目（5万-10万行代码变更）执行时仍会遇到 context compaction 导致信息丢失

Anthropic 的 C 编译器项目就是例子——最热门的 issue 是"Hello World 无法编译"。**Ralph Vigam loop**（反复重试直到正确）在非专门设计的工具上不起作用。

---

## Context Engineering 与 Agentic Engineering [12:52]

两个关键概念：

**Context Engineering**：在正确的时间给 AI 正确数量的上下文，让它专注于最小有效任务。

**Agentic Engineering**：为正确的任务招募正确的 agent，配备正确的 prompt 和工具。不同模型擅长不同任务——GPT 5.3 在某些方面优于 Opus，反之亦然。

企业规模的问题：不是每个开发者都能以相同效率使用工具。MCP 设置、skills 配置、prompt 风格（XML tokens 对 Anthropic 有效但对 OpenAI 无效）——这些复杂性在规模化时被放大。

---

## 有效 Context Window 的真相 [19:11]

虽然模型声称有 100 万 token context，但**有效 context window 两年来几乎没变**——停留在 80K-120K token。

问题叠加：
- Spec 占用 context
- 5 个 MCP 各占 2 万 token = 10 万 token 消失
- Skills、agents.md 还没加载
- 实际工作文件还没放进去

结论：即使有 100 万 token 的 context length，超过有效前沿后 agent 性能急剧下降。这个物理约束在未来 3 年内不会根本改变。

---

## 知识图谱作为锚点 [20:24]

Blitzy 的核心技术：**图+向量的混合索引**。

- 深度理解代码库，映射所有关系，做语义摘要和聚合
- 在 1000 万行代码中从一个点到另一个点，一次请求即可完成（而非烧 token 遍历文件链）

与当前工具的对比：
- 早期 Copilot = RAG（语义向量搜索）
- 当前 Codex/Claude Code = grep（浅层索引）
- Blitzy = 语义方向 + grep 精确定位（类似 Find My 的方向指引）

**阈值**：代码库超过 2 倍最大 context window（约 7-10 万行），图+向量的优势就明显体现。

---

## Multi-Agent 的两种模式 [25:07]

**模式一：Sub-agent（多线程）**

一个 orchestrator 招募多个 sub-agent 并行搜索或分工（前端/后端）。优势：速度、减少 head agent 的 context 负担。

瓶颈：**leader agent 仍是单点**——所有结果汇报回来，context 问题只是被踢远了一步，没有根本解决。

**模式二：Agent Swarm（超并行）**

Blitzy 的方案：
1. 用 AI 将 spec 递归分解为任务
2. 每个任务分配给独立 agent
3. 用**数据库作为编排层**（而非单一 orchestrator）
4. 可招募数万 agent 并行工作

类比：从 CPU 多线程到 GPU 并行——不是一个 orchestrator 跟踪所有事情，而是分布式协调。

---

## 并发冲突的解决 [30:07]

多 agent 并行工作时防止互相踩踏的技术：

1. **多沙箱环境**：每个 agent 在独立环境中工作，通过源代码汇聚结果
2. **Git 作为 source of truth**：每个 agent 提交到 GitHub，定期检查是否仍能编译、是否符合 spec
3. **周期性代码审查**：内部 review agent 检查代码是否偏移
4. **QA agent**：测试所有代码
5. **图数据库锚定**：每个 agent 在图的节点上操作，知道文件依赖关系，减少冲突

---

## 动态 Agent 设计 [32:06]

演进路径：静态 agent（Cloud 3.5 时代）→ 动态 agent（当前）。

当前做法：
- 基础指令控制在 **5000 token 以内**
- Agent 可以查找 prompt guidelines（URL 引用而非全部塞入 context）
- **Agent 设计 agent**：根据 spec 的不同部分，动态决定什么 persona + 什么工具组合最适合

关键发现：**Persona 对推理质量有实质影响**。给 agent 金融专家身份后，文档用语从通用变为银行开发者能理解的术语。这不是玄学——persona 将模型放入正确的语义邻域。

每个 agent 启动时检查：加载后 context 占用是否仍在有效窗口内？

---

## Agents.md 为什么不能规模化 [39:10]

Agents.md 在小代码库（<7-10 万行）有效，但无法泛化：

- 无法用文本捕获所有团队的所有学习
- 与代码库中的实际模式冲突时，agent 行为不一致

真实案例：规则说"只用 fakes 不用 mocks"，但代码库中大量使用 mocks，另一条规则说"模仿已有模式"——agent 无所适从，结果随机。

---

## 评估的困境 [41:25]

当前 benchmark（SWE-bench verified/pro、Terminal Bench）不反映真实世界：

- 分数相近的模型，真实表现差异巨大
- Gemini 倾向创造性冗长方案，Opus 倾向精确简洁——benchmark 不捕获这种差异
- **轨迹质量比最终正确性更重要**：token 消耗、回合数、compaction 次数、推理速度

Blitzy 的评估方法：
- 固定内容和 prompt，让 LLM 按最新 guidelines 优化 prompt
- 用合成数据创建真实世界复杂度的 eval（多文件、百万行、模拟错误）
- 评估维度：正确性 + token 消耗 + 工具调用效率 + 推理轨迹质量

---

## 代码质量与可维护性 [49:03]

超越"能编译能跑测试"的质量维度：

- **Cyclomatic complexity**：代码维护难度的量化指标
- **安全性**：防御性编码、漏洞检测
- **可解释性**：文档、注释、变量命名
- **可维护性**：人类能否理解并继续开发

Blitzy 的做法：
- 开发过程中设置 checkpoint（每完成 N 个 feature 暂停审查）
- Review agent 分类风险（critical/major/minor）
- 防止错误级联（一个 interface 改错影响 50 个文件）
- 最终输出 project guide：完成度指标 + 未完成项说明

---

## 自强化知识图谱 [01:10:38]

Blitzy 的核心差异化：每次使用都让实例变得更好。

信号来源：PR 接受/拒绝、编辑、聊天问答、规则声明。

与 agents.md 的关键区别：
- 文本记忆 = 无论 agent 做什么都注入 prompt
- 图数据库记忆 = **只在 agent 工作于相关节点时才加载**

反馈存储为图中的实体，与其引用的代码位置关联。系统自动判断反馈是关于特定任务、整个 repo 还是用户偏好，存储在对应层级。

结果：不膨胀 context window，不跨越有效 context 阈值。
