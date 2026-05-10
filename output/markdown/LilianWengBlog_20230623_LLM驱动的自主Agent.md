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

# LLM驱动的自主Agent

> 原文：[LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/)
> 来源：Lilian Weng Blog | 2023-06-23
> 作者：Lilian Weng

---

## 索引

- [Agent系统概览](#agent系统概览)
- [组件一：规划（Planning）](#组件一规划planning)
  - [任务分解](#任务分解)
  - [自我反思](#自我反思)
- [组件二：记忆（Memory）](#组件二记忆memory)
  - [记忆类型](#记忆类型)
  - [最大内积搜索（MIPS）](#最大内积搜索mips)
- [组件三：工具使用（Tool Use）](#组件三工具使用tool-use)
- [案例研究](#案例研究)
- [挑战](#挑战)

---

以LLM作为核心控制器构建agent是一个强大的概念。AutoGPT、GPT-Engineer和BabyAGI等概念验证项目展示了LLM的潜力远超生成文本——它可以被框架化为一个**强大的通用问题求解器**。

---

## Agent系统概览

在LLM驱动的自主agent系统中，LLM充当agent的大脑，辅以几个关键组件：

**规划（Planning）**
- 子目标和分解：agent将大任务拆分为更小、可管理的子目标
- 反思和精炼：agent可以对过去的行动进行自我批评和自我反思，从错误中学习

**记忆（Memory）**
- 短期记忆：所有的in-context learning都可以视为利用模型的短期记忆
- 长期记忆：通过外部向量存储和快速检索，提供保留和回忆（无限）信息的能力

**工具使用（Tool Use）**
- Agent学习调用外部API获取模型权重中缺失的额外信息：当前信息、代码执行能力、专有信息源访问等

---

## 组件一：规划（Planning）

复杂任务通常涉及很多步骤。Agent需要知道这些步骤并提前规划。

### 任务分解

**Chain of Thought（CoT）** 已成为增强模型在复杂任务上表现的标准prompting技术。模型被指示"逐步思考"，利用更多test-time计算将困难任务分解为更小更简单的步骤。

**Tree of Thoughts** 扩展了CoT，在每一步探索多种推理可能性。它将问题分解为多个思考步骤，每步生成多个想法，创建树结构。搜索过程可以是BFS或DFS。

任务分解可以通过以下方式完成：
1. LLM + 简单prompting（如"Steps for XYZ.\n1."）
2. 任务特定指令（如"Write a story outline."）
3. 人类输入

**LLM+P** 方法依赖外部经典规划器做长周期规划，使用PDDL作为中间接口。本质上将规划步骤外包给外部工具。

### 自我反思

自我反思允许自主agent通过精炼过去的行动决策和纠正错误来迭代改进。

**ReAct** 通过将动作空间扩展为任务特定离散动作和语言空间的组合，在LLM中整合推理和行动。prompt模板包含显式步骤：

```
Thought: ...
Action: ...
Observation: ...
（重复多次）
```

**Reflexion** 为agent配备动态记忆和自我反思能力。它有一个标准RL设置，奖励模型提供简单的二元奖励，行动空间遵循ReAct设置。每次失败后，agent进行自我反思并将反思结果存入记忆，用于未来的试验。

**Chain of Hindsight（CoH）** 鼓励模型通过展示一系列过去的输出（每个都带有反馈注释）来改进自己的输出。人类反馈数据被表示为 `[输出, 反馈]` 序列对。

---

## 组件二：记忆（Memory）

### 记忆类型

类比人类记忆的分类：

- **感觉记忆**：学习嵌入表示（原始输入的编码）
- **短期记忆/工作记忆**：in-context learning。受Transformer有限context window长度约束
- **长期记忆**：agent在查询时可以关注的外部向量存储，通过快速检索访问

### 最大内积搜索（MIPS）

外部记忆可以缓解有限注意力跨度的限制。标准做法是将信息的embedding表示保存到向量存储数据库中，支持快速最大内积搜索（MIPS）。

常用的近似最近邻（ANN）算法：
- **LSH**（Locality-Sensitive Hashing）
- **ANNOY**（Approximate Nearest Neighbors Oh Yeah）
- **HNSW**（Hierarchical Navigable Small World）
- **FAISS**（Facebook AI Similarity Search）
- **ScaNN**（Scalable Nearest Neighbors）

---

## 组件三：工具使用（Tool Use）

工具使用是人类的显著特征。我们创造、修改和利用外部对象来超越我们身体和认知的限制。同样，为LLM配备外部工具可以显著扩展模型能力。

**MRKL**（Modular Reasoning, Knowledge and Language）是一种神经符号架构，包含一组"专家"模块，通用LLM作为路由器将查询路由到最合适的专家模块。

**TALM**（Tool Augmented Language Models）和 **Toolformer** 都通过微调语言模型来学习使用外部工具API。

**ChatGPT Plugins** 和 **OpenAI API function calling** 是LLM增强工具使用能力的实际应用。

**HuggingGPT** 使用ChatGPT作为任务规划器，根据模型描述选择HuggingFace平台上可用的模型，总结响应。

---

## 案例研究

### 科学发现Agent

**ChemCrow** 是一个领域特定的agent示例，设计用于完成有机合成、药物发现和材料设计中的任务。它整合了13个专家设计的工具。

### 生成式Agent模拟

**Generative Agents**（Park et al. 2023）是一个有趣的实验——25个虚拟角色，每个由LLM驱动的agent控制，在沙盒环境中生活和互动。

agent的记忆流包含完整的经验记录列表。每条记忆是一个事件，由agent直接提供或从其他agent的通信中推断。检索模型考虑**近因性、重要性和相关性**。

agent的反思机制定期（当最近事件的重要性分数之和超过阈值时）综合记忆为更高层次的推断，指导agent的行为。

### 概念验证示例

**AutoGPT**：在LLM之上设置了很多可靠性问题，使其更像一个概念验证演示而非实用系统。

**GPT-Engineer**：旨在根据自然语言规范生成整个代码库。

---

## 挑战

1. **有限的context长度**：有限的通信带宽限制了历史信息、详细指令、API调用上下文和响应的包含。系统设计必须在这个有限通信带宽下工作。

2. **长期规划和任务分解的挑战**：在长历史上规划和有效探索解空间仍然具有挑战性。LLM难以在遇到意外错误时调整计划。

3. **自然语言接口的可靠性**：当前agent系统依赖自然语言作为LLM与外部组件（如记忆和工具）之间的接口。模型输出的可靠性有限——LLM可能犯格式错误，agent可能在反叛行为中不遵循指令。

4. **鲁棒性和对齐**：当agent被赋予更多自主权时，确保它们的行为与人类意图对齐变得更加关键。
