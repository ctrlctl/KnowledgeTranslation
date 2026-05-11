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

# 从 Prompt 到产品：Responses API 一周年

> 原文：[From prompts to products: One year of Responses](https://developers.openai.com/blog/one-year-of-responses)
> 来源：OpenAI Developers Blog | 2026-05-09
> 作者：OpenAI

---

## 索引

- [概述](#概述)
- [案例1：AI Agent 故障检测（Raindrop AI）](#案例1ai-agent-故障检测)
- [案例2：深度推理工作流（Repo Prompt）](#案例2深度推理工作流)
- [案例3：唱片收藏对话界面（Collxn）](#案例3唱片收藏对话界面)
- [案例4：屏幕录制转交互式 Demo（Arcade）](#案例4屏幕录制转交互式-demo)
- [案例5：AI 输出中的品牌可见性（Hexagon）](#案例5ai-输出中的品牌可见性)

---

## 概述

一年前 OpenAI 推出了 Responses API——为开发者和企业构建有用、可靠 agent 的基础。给模型配备一组托管工具，让 AI 从聊天助手进化为能代你采取行动的系统。

今天 Responses API 支持多种工具来驱动 agentic 工作流，以及专为更强模型设计的新特性和原语。数千开发者正在用它加速客户支持、法律、生命科学、旅行等行业的生产力。

以下是五个开发者故事。

---

## 案例1：AI Agent 故障检测

**Raindrop AI** — Alexis Gauba & Ben Hylak

- 工具：自定义工具
- 模型：GPT-5.2（测试 GPT-5.4）

Raindrop 是世界上最有野心的 AI 公司背后的监控平台，用于捕获 agent 在生产中偏离轨道的情况。

系统使用 Responses API（通过 Vercel AI SDK）运行后台分析，跨不同模型提供商共享工具，保持系统在环境间可移植。

平台聚焦三个核心系统：

1. **Agent 行为监控**：持续评估 agent 行为是否符合预期。开发者可以设置不良结果的条件，平台在条件满足时发出告警。
2. **故障检测和告警**：检测到异常后通知开发者，展示调查所需的相关上下文——跟踪跨 agent 版本的行为变化、识别哪个 prompt 或系统变更触发了故障、检查推理 trace 和 tool call。
3. **调查和调试工具**：帮助开发者诊断 agent 工作流中的问题，连接故障检测和系统改进。

---

## 案例2：深度推理工作流

**Repo Prompt** — Eric Provencher

- 工具：Codex + App Server + MCP、web search
- 模型：GPT-5.3 Codex

> "与其让推理模型在规划或审查时浪费上下文窗口来导航上下文，我们用一个单独的 agent 提前策展上下文，让推理模型把尽可能多的推理能力用于解决任务。"

Eric 构建了一个帮助开发者和研究者对大量文档、代码库和数据集进行深度分析的系统。核心架构**将上下文收集与深度推理分离**：

1. **上下文构建 agent**：分析大型数据仓库，确定哪些信息与查询相关。输出结构化上下文包。
2. **"Oracle" 深度推理**：不做 tool call 或额外信息检索，完全聚焦于分析策展好的上下文。通过分离研究和推理，模型可以把全部推理能力用于理解问题。
3. **迭代研究循环**：推理模型产出后，另一个 agent 审查结果并决定是否需要额外调查。如果需要，系统启动另一轮上下文收集和推理。

依赖的 Responses API 能力：后台任务（长时间运行）、Agent 编排（协调循环）、可观测性（监控执行中的工作流）。

---

## 案例3：唱片收藏对话界面

**Collxn** — Ash Ryan Arnwine

- 工具：Web search + 16 个自定义工具
- 模型：GPT-5.4、GPT-5 nano

> "Responses API 感觉像是在帮我减轻工作，相比构建完整 RAG 系统这样的替代方案。"

Collxn 帮助黑胶收藏者重新发现书架上已有的唱片。它接入 Discogs 收藏，每天发送"Daily Drop"邮件，聚焦一张不同的唱片。

用 Responses API 驱动的聊天界面"Ask This Drop"让用户可以对唱片提问——当前市场价格、艺术家其他专辑、这个压制版有多稀有。

关键点：**有状态对话**让多轮聊天交互更简单快速，整体架构比构建完整 RAG 系统简化了很多。

---

## 案例4：屏幕录制转交互式 Demo

**Arcade** — Nick Sorrentino & Pawel Wszola

- 工具：Computer use
- 模型：GPT-5.2、computer-use-preview

> "集成 API 驱动的内容生成将发布 demo 所需步骤减少了 50%。"

Arcade 把屏幕录制变成精美的交互式产品 demo。工作流：

1. 用户录制屏幕执行工作流
2. 桌面/浏览器端直接捕获结构化交互（点击、输入、滚动）；移动端录制纯视频
3. 录制发送到 Responses API + computer-use 工具，分析视觉帧并推断发生的交互
4. 系统将推断的动作转换为结构化步骤
5. 生成叙述文本和交互热点

集成后：发布前所需操作中位数**下降 50%**，P80 操作数从 ~230 降到 ~120。

---

## 案例5：AI 输出中的品牌可见性

**Hexagon** — Tunde Adeyinka & Ramon Silva

- 工具：Web search
- 模型：GPT-5.2 Chat

Hexagon 回答零售商的新问题：**AI 助手如何谈论你的产品？**

三个核心系统：

1. **响应模拟**：每天生成数千个真实消费者 prompt 和购物查询，通过 Responses API 发送，分析返回输出以跟踪品牌在 AI 生成答案中的可见性。
2. **多 Agent 内容生成管道**：四 agent 架构，每个 agent 执行管道中的专门步骤，通过非确定性循环进行迭代优化后发布。
3. **仪表盘和客户工具**：包含"Hexi"聊天机器人，客户可以对话式探索分析数据。

依赖的关键能力：Web search（复制浏览器启用的响应）、用户位置参数（模拟不同地区查询）、推理努力度控制、上下文持久化（跨调用维护上下文）。

---

## 总结

一年过去，Responses API 已成为开发者创建 agentic 软件的核心构建块。平台本身在快速演进——更好的编排、更丰富的工具生态（OpenAI 托管容器 + 网络 + shell 工具）。
