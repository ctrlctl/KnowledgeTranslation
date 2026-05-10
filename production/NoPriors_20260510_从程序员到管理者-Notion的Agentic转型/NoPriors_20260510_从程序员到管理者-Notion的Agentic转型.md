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

# 从程序员到管理者：Notion 的 Agentic 转型

> 原文：[From Coder to Manager: Navigating the Shift to Agentic Engineering with Notion Co-Founder Simon Last](https://traffic.megaphone.fm/PDP4039354704.mp3)
> 来源：No Priors | 2026-05-10
> 嘉宾：Simon Last（Notion 联合创始人）

---

## 索引

- [从 GPT-4 到 Notion AI 的演进弧线](#从-gpt-4-到-notion-ai-的演进弧线)
- [每六个月重写一次 harness](#每六个月重写一次-harness)
- [Coding agent 如何改变工程组织](#coding-agent-如何改变工程组织)
- [Notion 的 Agent 产品：个人 Agent 与自定义 Agent](#notion-的-agent-产品个人-agent-与自定义-agent)
- [为 Agent 重新设计 API](#为-agent-重新设计-api)
- [Agent 的自举能力：coding 是 AGI 的内核](#agent-的自举能力coding-是-agi-的内核)
- [Simon 的个人工作流：13 天不停的 coding agent](#simon-的个人工作流13-天不停的-coding-agent)
- [从写代码的人变成管理 Agent 的人](#从写代码的人变成管理-agent-的人)

---

## 从 GPT-4 到 Notion AI 的演进弧线 [00:45]

2022 年 Simon 和联合创始人 Ivan 在墨西哥公司 offsite 上拿到 GPT-4 的访问权限。两个东西立刻打动了他们：一是它能跟随相当复杂的指令，二是它的**知识广度和深度**。

从那时起，Notion AI 的发展路径：

1. **AI Writer**（2023年2月）——单步任务，选中文本重写/编辑，最简单
2. **Q&A**（2023年10月）——对整个 workspace 做语义索引，基于来源回答问题
3. **跨平台索引**——Slack、Google Drive 等，逐步覆盖
4. **个人 Agent**（2025年8-9月）——拥有用户所有工具权限的通用助手
5. **自定义 Agent**（上周刚发布）——可以在后台自主运行的专用 agent

---

## 每六个月重写一次 harness [07:16]

Simon 说这是一个"running joke"：Notion 的 AI harness 大约每六个月重写一次，而且重写周期在缩短。

他认为很多公司犯的错误是**做了一个东西就一直用下去**。正确的做法是：时刻关注模型和技术的当前状态，然后围绕它重新设计 harness、系统和产品。这意味着你必须每六个月重写。

"我觉得挺好玩的。每次都是重新开始、重新思考的机会。"

而且现在有 coding agent 帮忙，**重写的意愿大幅提升**——agent 会帮你做。

---

## Coding agent 如何改变工程组织 [08:37]

Simon 从去年四月开始用 Claude Code，这是一个巨大的解锁。关键变化：

- **个人产出的上限极大提升**——但下限没变。差距从 10x 变成了 100x 甚至 1000x
- **团队规模没有明显变化**——小 Tiger team 一直是最优的，之前如此，现在更是
- **整体感觉更混乱**——更多原型、更多实验、PR 更大更有野心
- 设计团队建了自己的 git repo（"design playground"），设计师可以直接部署高保真原型
- 所有 PR 现在都由 agent 写，**但仍然做 code review**
- 他再也不会提交没有完整 integration test 的 PR 了

关键区分：这不是 vibe coding。你需要**仔细思考你要做什么改变、如何验证、如何安全部署**，然后让 agent 帮你执行这个过程。

---

## Notion 的 Agent 产品：个人 Agent 与自定义 Agent [13:06]

**个人 Agent**：每个 Notion 用户都有一个，拥有用户能访问的所有东西——创建数据库、更新内容、搜索 workspace、搜索网络、做研究。

**自定义 Agent**（刚发布）：
- 默认没有任何权限，需要你主动授予
- 可以在后台自主运行
- 可以连接 Slack 频道，自动响应消息并归档任务
- 可以访问特定数据库，定期搜索并生成报告

Simon 最兴奋的方向：让 agent 能**自举自己的能力**——如果需要一个还不存在的集成，它可以自己写代码、部署、然后使用。

---

## 为 Agent 重新设计 API [17:53]

Notion 原有的 API 用了一种"疯狂冗长的 JSON 格式"来表示 blocks，对 agent 来说非常糟糕。

解决方案：
- **页面读写**：设计了一种增强版 Markdown 方言，看起来像普通 Markdown 但支持所有 Notion block 类型。模型天然擅长这个
- **数据库操作**：直接用 **SQLite** 语法。模型也天然擅长

设计方法论：
1. 大量试用，观察 agent 在哪里卡住（"太多 token 了，怎么缩小？"）
2. 第一性原理思考：模型训练数据里有什么？它的先验知识是什么？
3. 持续迭代——"用户研究，只不过用户是 agent，而且你有无限访问权"

---

## Agent 的自举能力：coding 是 AGI 的内核 [15:01]

Simon 的核心观点：

> "我把 coding agent 看作 AGI 的内核。AGI 就是一个 coding agent。代码是表示确定性逻辑的极好原语。"

应用到知识工作 agent 上，这意味着：
- 如果集成不存在，agent 可以自己构建
- 如果需要连接新数据源，agent 可以自己实现
- 能力不再是预设的，而是**按需自举**的

---

## Simon 的个人工作流：13 天不停的 coding agent [20:20]

Simon 的日常：

- 用 Claude Code 或 Codex（偏好 CLI 工具）
- 目标是**同时运行尽可能多的 agent**
- 每晚睡前确保给 agent 足够多的任务，让它到早上还没做完——"这就是胜利"
- 个人记录：一个 coding agent **连续运行 13 天**不停，持续处理任务
- 承认半夜会醒来检查 agent 是否还在跑

自定义 Agent 的使用：
- **邮件分诊 agent**：每天自动归档 95% 不需要看的邮件。前几天用"面试模式"让 agent 提议归档哪些，人工纠正；几周后完全放手
- **内部反馈路由 agent**：监控 Slack 频道，自动把 bug 和产品反馈路由到正确的团队数据库。用类似的记忆模式，随时间积累了数百条路由规则

---

## 从写代码的人变成管理 Agent 的人 [27:46]

Simon 从去年夏天起就**不再手写代码**了。

演进路径：
1. 人类写所有代码
2. Tab 补全
3. 和 agent 对话，它做小任务，人还在外层循环
4. **现在**：设计端到端任务（包含修改和验证），自己只做最终验证和监控

> "我现在是 agent manager，不再是 coder。"

Notion 的产品愿景也相应转变：

- **之前**：为人类创造最好的直接执行工作的工具
- **现在**：为人类创造最好的管理 agent 执行工作的工具

但有趣的是，**你仍然需要相同的基础原语**——文档（非结构化写作）、数据库（结构化数据）、看板（协调结构）。Agent 喜欢写 Markdown，需要 Kanban board 来协调 100 个并行 coding agent。和人类一样。
