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

# 用 Agent 为 Agent 编写有效工具

> 原文：[Writing effective tools for agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
> 来源：Anthropic Engineering | 2025-09-11
> 作者：Ken Aizawa

---

## 索引

- [工具是什么：确定性与非确定性的契约](#工具是什么确定性与非确定性的契约)
- [如何编写工具：原型→评估→协作优化](#如何编写工具原型评估协作优化)
- [原则一：选择正确的工具](#原则一选择正确的工具)
- [原则二：命名空间划分](#原则二命名空间划分)
- [原则三：返回有意义的上下文](#原则三返回有意义的上下文)
- [原则四：优化 Token 效率](#原则四优化-token-效率)
- [原则五：Prompt-engineer 工具描述](#原则五prompt-engineer-工具描述)

---

## 工具是什么：确定性与非确定性的契约

传统软件是确定性系统之间的契约——`getWeather("NYC")` 每次都以完全相同的方式获取纽约天气。

**工具是确定性系统与非确定性 agent 之间的新型契约。** 当用户问"今天需要带伞吗？"，agent 可能调用天气工具、从通用知识回答、甚至先问一个关于位置的澄清问题。Agent 偶尔会幻觉或无法理解如何使用工具。

这意味着需要从根本上重新思考为 agent 编写软件的方式：不是像为其他开发者写函数和 API 那样写工具，而是**为 agent 设计**。

目标：增加 agent 能有效解决广泛任务的表面积。经验表明，对 agent 最"人体工学"的工具，对人类来说也出奇地直观。

---

## 如何编写工具：原型→评估→协作优化

### 1. 构建原型

快速搭建工具原型，包装为本地 MCP server 或 DXT，连接到 Claude Code 或 Claude Desktop 测试。自己测试以识别粗糙边缘。

### 2. 运行评估

生成大量基于真实世界使用的评估任务。强评估任务可能需要多次工具调用（甚至数十次）。

**强任务示例：**
- "安排下周与 Jane 的会议讨论 Acme Corp 项目。附上上次项目规划会议的笔记并预订会议室。"
- "客户 ID 9182 报告被收费三次。找到所有相关日志条目并确定是否有其他客户受影响。"

**弱任务示例：**
- "安排下周与 jane@acme.corp 的会议。"（太简单，不需要多步推理）

每个评估 prompt 配对可验证的响应。用简单 agentic 循环（while 循环包裹交替的 LLM API 和工具调用）程序化运行评估。

### 3. 与 Agent 协作优化

将评估 agent 的 transcript 拼接后粘贴到 Claude Code。Claude 擅长分析 transcript 并一次重构大量工具。使用 held-out 测试集确保不过拟合。

---

## 原则一：选择正确的工具

**更多工具不总是带来更好结果。** 常见错误：工具仅仅包装现有 API 端点，不管是否适合 agent。

Agent 有有限的"上下文"，而计算机内存便宜且充裕。如果 agent 用一个返回所有联系人的工具然后逐个读取——这是在浪费有限的上下文空间。更好的方式是直接跳到相关页面。

**建议：**
- 构建少量针对特定高影响工作流的深思熟虑的工具
- 工具可以合并功能，在底层处理多个离散操作
- 实现 `schedule_event` 而非分别实现 `list_users`、`list_events`、`create_event`
- 实现 `search_logs` 而非 `read_logs`
- 实现 `get_customer_context` 而非分别实现 `get_customer_by_id`、`list_transactions`、`list_notes`

每个工具应有清晰、独特的目的。工具应让 agent 像人类一样细分和解决任务，同时减少中间输出消耗的上下文。

---

## 原则二：命名空间划分

Agent 可能访问数十个 MCP server 和数百个工具。当工具功能重叠或目的模糊时，agent 会困惑。

**命名空间**（将相关工具分组在公共前缀下）帮助划分边界：
- 按服务：`asana_search`、`jira_search`
- 按资源：`asana_projects_search`、`asana_users_search`

前缀 vs 后缀命名对评估有非平凡影响，因 LLM 而异。

---

## 原则三：返回有意义的上下文

工具实现应只返回**高信号信息**。优先上下文相关性而非灵活性。

**避免返回：** `uuid`、`256px_image_url`、`mime_type`

**推荐返回：** `name`、`image_url`、`file_type`

将任意字母数字 UUID 解析为更有语义意义的语言，显著提高 Claude 在检索任务中的精度（减少幻觉）。

**`response_format` 枚举模式：** 暴露简单参数让 agent 控制工具返回 "concise" 还是 "detailed" 响应。Concise 响应可以只用 detailed 的 1/3 token。

---

## 原则四：优化 Token 效率

对任何可能消耗大量上下文的工具响应，实现**分页、范围选择、过滤和/或截断**，配合合理的默认参数值。Claude Code 默认限制工具响应为 25,000 token。

**截断时：** 用有帮助的指令引导 agent 追求更 token 高效的策略。

**错误响应：** 清晰传达具体可操作的改进，而非不透明的错误码或 traceback。

---

## 原则五：Prompt-engineer 工具描述

最有效的改进方法之一。工具描述加载到 agent 上下文中，可以集体引导 agent 走向有效的工具调用行为。

写工具描述时，想象如何向团队新人描述你的工具。考虑你可能隐含带入的上下文——专门的查询格式、小众术语定义、底层资源之间的关系——并使其显式化。

Claude Sonnet 3.5 在 SWE-bench Verified 上达到 SOTA，是在对工具描述做了精确改进之后——显著降低错误率并提高任务完成率。

---

**核心洞察：** 构建评估让你系统地衡量工具性能。你可以用 Claude Code 自动优化工具对抗这个评估。通过迭代的、评估驱动的过程，确保随着 agent 变得更强，工具也随之进化。
