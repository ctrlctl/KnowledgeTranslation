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

# Effective Harnesses for Long-Running Agents：长时间运行Agent的有效Harness

> 原文：[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
> 来源：Anthropic Engineering | 2025-11-26
> 作者：Justin Young

---

## 目录

- [核心问题：跨上下文窗口的连续工作](#核心问题跨上下文窗口的连续工作)
- [两部分解决方案](#两部分解决方案)
- [环境管理](#环境管理)
- [增量进展](#增量进展)
- [测试](#测试)
- [每次启动的标准流程](#每次启动的标准流程)
- [失败模式与解决方案总结](#失败模式与解决方案总结)
- [未来方向](#未来方向)

---

## 核心问题：跨上下文窗口的连续工作

随着 AI agent 越来越强，开发者开始让它们处理需要数小时甚至数天的复杂任务。但让 agent 在多个上下文窗口之间保持一致的进展，仍然是一个未解决的问题。

核心挑战在于：agent 必须在离散的 session 中工作，每个新 session 开始时对之前发生的事情毫无记忆。想象一个软件项目由轮班工程师负责，每个新工程师到岗时完全不知道上一班做了什么。因为上下文窗口有限，而大多数复杂项目无法在单个窗口内完成，agent 需要一种方式来弥合 session 之间的鸿沟。

---

## 两部分解决方案

Anthropic 开发了一个两部分方案，让 Claude Agent SDK 能够有效地跨多个上下文窗口工作：

1. **Initializer agent**：在第一次运行时设置环境
2. **Coding agent**：在每个后续 session 中做增量进展，同时为下一个 session 留下清晰的 artifact

---

### 为什么 compaction 不够

即使有 compaction（将早期对话压缩摘要以节省上下文空间），像 Opus 4.5 这样的前沿模型在循环运行时，仅凭一个高层 prompt（如"构建一个 claude.ai 的克隆"）仍然无法构建出生产级 web 应用。

Claude 的失败表现为两种模式：

**模式一：试图一口气做完所有事。** Agent 倾向于 one-shot 整个应用。这经常导致模型在实现过程中耗尽上下文，留下一个半完成、未文档化的功能。下一个 session 的 agent 只能猜测之前发生了什么，花大量时间试图让基础应用重新运行。即使有 compaction，它也不总是能向下一个 agent 传递足够清晰的指令。

**模式二：过早宣布完成。** 在一些功能已经构建之后，后续的 agent 实例会环顾四周，看到已有进展，然后宣布任务完成。

---

## 环境管理

### Feature List（功能清单）

为了解决 agent 一口气做完或过早宣布完成的问题，initializer agent 被提示编写一个全面的功能需求文件，扩展用户的初始 prompt。在 claude.ai 克隆的例子中，这意味着超过 200 个功能点，例如"用户可以打开新聊天、输入查询、按回车、看到 AI 响应"。

这些功能最初全部标记为 `"passes": false`，这样后续的 coding agent 就有一个清晰的完整功能蓝图。

```json
{
  "category": "functional",
  "description": "New chat button creates a fresh conversation",
  "steps": [
    "Navigate to main interface",
    "Click the 'New Chat' button",
    "Verify a new conversation is created",
    "Check that chat area shows welcome state",
    "Verify conversation appears in sidebar"
  ],
  "passes": false
}
```

关键设计决策：

- Coding agent 只能修改 `passes` 字段的状态
- 使用强措辞指令："删除或编辑测试是不可接受的，因为这可能导致功能缺失或 bug"
- 选择 JSON 而非 Markdown——模型不太容易不当修改 JSON 文件

---

## 增量进展

有了初始环境脚手架后，coding agent 被要求**一次只做一个功能**。这种增量方式对于解决 agent 试图一次做太多事的倾向至关重要。

增量工作时，模型还必须在每次代码修改后将环境留在干净状态。实验发现，最好的方式是要求模型：

- **提交 git commit**，附带描述性的 commit message
- **在 progress 文件中写入进展摘要**

这让模型可以用 git 回滚坏的代码修改，恢复到代码库的工作状态。这些方法也提高了效率——消除了 agent 猜测之前发生了什么、花时间让应用重新运行的需要。

---

## 测试

另一个主要失败模式：Claude 倾向于在没有充分测试的情况下将功能标记为完成。没有明确提示时，Claude 会做代码修改，甚至用单元测试或 curl 命令测试开发服务器，但无法识别功能端到端不工作。

**解决方案：提供浏览器自动化工具。** 在构建 web 应用的场景中，明确提示 Claude 使用浏览器自动化工具（如 Puppeteer MCP）并像人类用户一样测试，显著提高了性能。Agent 能够识别和修复仅从代码中看不出来的 bug。

仍有局限：Claude 的视觉能力和浏览器自动化工具的限制使得某些 bug 难以发现。例如，Claude 无法通过 Puppeteer MCP 看到浏览器原生的 alert 弹窗，依赖这些弹窗的功能往往更容易出 bug。

---

## 每次启动的标准流程

有了上述所有机制后，每个 coding agent 被提示在开始时执行一系列步骤：

1. 运行 `pwd` 查看工作目录
2. 读取 git log 和 progress 文件，了解最近的工作
3. 读取 feature list 文件，选择优先级最高的未完成功能开始工作

还要求 initializer agent 编写一个 `init.sh` 脚本来运行开发服务器，然后在实现新功能之前先跑一个基本的端到端测试。

在 claude.ai 克隆的例子中，agent 总是先启动本地开发服务器，用 Puppeteer MCP 开始新聊天、发送消息、接收响应。这确保 Claude 能快速识别应用是否处于损坏状态，并立即修复现有 bug。如果 agent 直接开始实现新功能，可能会让问题更严重。

典型 session 开头的 assistant 消息：

```
[Assistant] I'll start by getting my bearings and understanding the current state of the project.
[Tool Use] <bash - pwd>
[Tool Use] <read - claude-progress.txt>
[Tool Use] <read - feature_list.json>
[Assistant] Let me check the git log to see recent work.
[Tool Use] <bash - git log --oneline -20>
[Assistant] Now let me check if there's an init.sh script to restart the servers.
<Starts the development server>
[Assistant] Excellent! Now let me navigate to the application and verify fundamental features are still working.
<Tests basic functionality>
[Assistant] Based on my verification testing, fundamental functionality is working well. Now let me review the tests.json file to understand what needs to be implemented next.
<Starts work on a new feature>
```

---

## 失败模式与解决方案总结

| 问题 | Initializer Agent 行为 | Coding Agent 行为 |
|------|----------------------|------------------|
| Agent 过早宣布整个项目完成 | 设置 feature list 文件：基于输入 spec，建立结构化 JSON 文件，包含端到端功能描述列表 | 在 session 开始时读取 feature list，选择单个功能开始工作 |
| Agent 留下有 bug 或未文档化进展的环境 | 初始化 git 仓库和 progress notes 文件 | Session 开始时读取 progress notes 和 git commit log，对开发服务器运行基本测试。Session 结束时写 git commit 和 progress 更新 |
| Agent 过早标记功能为完成 | 设置 feature list 文件 | 自我验证所有功能。只有在仔细测试后才将功能标记为 "passing" |
| Agent 需要花时间弄清如何运行应用 | 编写 `init.sh` 脚本来运行开发服务器 | Session 开始时读取 `init.sh` |

---

## 未来方向

这项研究展示了长时间运行 agent harness 中的一组可能解决方案。但仍有开放问题：

- **单 agent vs 多 agent**：目前不清楚单一通用 coding agent 在跨上下文中表现最好，还是多 agent 架构能实现更好的性能。专门化的 agent（如测试 agent、QA agent、代码清理 agent）可能在软件开发生命周期的子任务上做得更好。

- **领域泛化**：这个 demo 针对全栈 web 应用开发优化。未来方向是将这些发现推广到其他领域——科学研究、金融建模等长时间运行的 agentic 任务可能也适用这些经验。

---

**关键 takeaway：** 让 agent 快速理解工作状态是核心洞察。通过 `claude-progress.txt` 文件配合 git 历史实现这一点。这些实践的灵感来自于了解高效软件工程师每天在做什么。
