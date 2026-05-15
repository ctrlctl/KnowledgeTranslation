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

# Effective Harnesses for Long-Running Agents：长时间运行 Agent 的有效 Harness

> 原文：[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
> 来源：Anthropic Engineering | 2025-11-26
> 作者：Justin Young

---

## 索引

- [长时间运行 Agent 的问题](#长时间运行-agent-的问题)
- [环境管理](#环境管理)
- [快速进入状态](#快速进入状态)
- [未来工作](#未来工作)

---

随着 AI agent 能力越来越强，开发者开始让它们承担需要数小时甚至数天才能完成的复杂任务。然而，如何让 agent 在多个 context window 之间持续推进工作，仍然是一个未解决的问题。

长时间运行 agent 的核心挑战在于：它们必须在离散的 session 中工作，而每个新 session 开始时对之前发生的事情毫无记忆。想象一个轮班制的软件项目——每位新上班的工程师对上一班发生了什么完全不知情。由于 context window 有限，而大多数复杂项目无法在单个 window 内完成，agent 需要一种方式来弥合 coding session 之间的断层。

我们开发了一个**双管齐下的方案**，让 [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) 能够跨多个 context window 高效工作：一个 **initializer agent** 在首次运行时搭建环境，一个 **coding agent** 负责在每个 session 中推进增量进展，同时为下一个 session 留下清晰的工件。代码示例见配套的 [quickstart](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)。

---

## 长时间运行 Agent 的问题

Claude Agent SDK 是一个强大的通用 agent harness，擅长编码以及其他需要模型使用工具来收集上下文、规划和执行的任务。它具备 compaction（上下文压缩）等上下文管理能力，让 agent 可以在不耗尽 context window 的情况下持续工作。理论上，有了这套机制，agent 应该能够无限期地做有用的工作。

然而，**compaction 并不够**。开箱即用的情况下，即使是 Opus 4.5 这样的前沿编码模型，在 Claude Agent SDK 上跨多个 context window 循环运行，如果只给一个高层级 prompt（比如"构建一个 claude.ai 的克隆"），也无法构建出生产级质量的 web 应用。

Claude 的失败表现为两种模式。第一种：agent 倾向于一次做太多事——本质上是试图一次性完成整个应用。这经常导致模型在实现过程中耗尽 context，让下一个 session 面对一个半完成、没有文档的功能。新 agent 不得不猜测之前发生了什么，花大量时间让基础应用重新跑起来。即使有 compaction 也会出现这个问题，因为 compaction 并不总能把完全清晰的指令传递给下一个 agent。

第二种失败模式通常出现在项目后期。当一些功能已经构建完成后，后续的 agent 实例会环顾四周，看到已经有了进展，然后宣布任务完成。

这把问题分解为两部分。首先，我们需要搭建一个初始环境，为 prompt 要求的*所有*功能奠定基础，引导 agent 逐步、逐功能地工作。其次，我们应该提示每个 agent 朝目标做增量进展，同时在 session 结束时让环境保持干净状态。所谓"干净状态"，指的是适合合并到 main 分支的代码：没有重大 bug，代码有序且文档完善，开发者可以直接开始新功能而不需要先清理别人留下的烂摊子。

在内部实验中，我们用一个两部分方案解决了这些问题：

1. **Initializer agent**：第一个 agent session 使用专门的 prompt，要求模型搭建初始环境：一个 `init.sh` 脚本、一个记录 agent 工作日志的 `claude-progress.txt` 文件，以及一个展示新增文件的初始 git commit。
2. **Coding agent**：后续每个 session 要求模型做增量进展，然后留下结构化的更新记录。^1

这里的**关键洞察**是找到一种方式，让 agent 在启动新的 context window 时能快速理解工作状态——通过 `claude-progress.txt` 文件配合 git 历史来实现。这些实践的灵感来自于观察高效软件工程师每天在做什么。

---

## 环境管理

在更新后的 [Claude 4 prompting guide](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices#multi-context-window-workflows) 中，我们分享了多 context window 工作流的最佳实践，包括一种"第一个 context window 使用不同 prompt"的 harness 结构。这个"不同的 prompt"要求 initializer agent 搭建好环境，提供未来 coding agent 高效工作所需的所有上下文。下面我们深入介绍这种环境的几个关键组件。

### Feature list（功能清单）

为了解决 agent 试图一次性完成应用或过早宣布项目完成的问题，我们提示 initializer agent 编写一份全面的功能需求文件，对用户的初始 prompt 进行展开。在 claude.ai 克隆的例子中，这意味着超过 200 个功能，比如"用户可以打开新对话、输入查询、按回车、看到 AI 回复"。这些功能最初全部标记为"failing"，这样后续的 coding agent 就能清楚地看到完整功能的全貌。

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

我们提示 coding agent 只能通过修改 `passes` 字段的状态来编辑这个文件，并使用强硬措辞的指令，比如"删除或编辑测试是不可接受的，因为这可能导致功能缺失或 bug"。经过一些实验，我们最终选择了 JSON 格式，因为模型不太容易不当地修改或覆盖 JSON 文件（相比 Markdown 文件）。

### Incremental progress（增量进展）

有了这个初始环境脚手架，coding agent 的下一轮迭代被要求每次只做一个功能。这种增量方式对于解决 agent 一次做太多事的倾向至关重要。

在增量工作的基础上，模型在每次代码变更后让环境保持干净状态仍然很关键。在实验中，我们发现引导这种行为的最佳方式是要求模型用描述性的 commit message 将进展提交到 git，并在 progress 文件中写下进展摘要。这让模型可以用 git revert 回退坏的代码变更，恢复到代码库的正常状态。

这些方法也提高了效率，因为 agent 不再需要猜测之前发生了什么、花时间让基础应用重新跑起来。

### Testing（测试）

我们观察到的最后一个主要失败模式是 Claude 倾向于在没有充分测试的情况下就标记功能为完成。如果没有明确提示，Claude 会做代码变更，甚至用单元测试或 `curl` 命令对开发服务器做测试，但无法识别功能在端到端层面并不工作。

在构建 web 应用的场景中，一旦明确提示 Claude 使用浏览器自动化工具、像人类用户一样做所有测试，它在端到端验证方面表现就很好。

![](images/fig_02.gif)
*Claude 通过 Puppeteer MCP server 截取的 claude.ai 克隆测试截图。*

给 Claude 提供这类测试工具显著提升了性能，因为 agent 能够发现并修复仅从代码层面看不出来的 bug。

一些问题仍然存在，比如 Claude 的视觉能力和浏览器自动化工具的局限性使得某些类型的 bug 难以发现。例如，Claude 无法通过 Puppeteer MCP 看到浏览器原生的 alert 弹窗，依赖这些弹窗的功能因此更容易出 bug。

---

## 快速进入状态

有了以上所有机制，每个 coding agent 被提示在开始时执行一系列步骤来了解当前状况，有些很基础但仍然有帮助：

1. *运行 `pwd` 查看你的工作目录。你只能编辑这个目录中的文件。*
2. *阅读 git 日志和 progress 文件，了解最近做了什么。*
3. *阅读 features list 文件，选择优先级最高的未完成功能开始工作。*

这种方式为 Claude 在每个 session 中节省了一些 token，因为它不需要自己摸索如何测试代码。让 initializer agent 写一个能启动开发服务器的 `init.sh` 脚本也很有帮助，这样可以在实现新功能之前先跑一个基本的端到端测试。

在 claude.ai 克隆的例子中，这意味着 agent 总是先启动本地开发服务器，用 Puppeteer MCP 开一个新对话、发送消息、接收回复。这确保了 Claude 能快速发现应用是否处于损坏状态，并立即修复现有 bug。如果 agent 直接开始实现新功能，很可能会让问题更严重。

一个典型 session 的开头是这样的：

```
[Assistant] I'll start by getting my bearings and understanding the current state of the project.
[Tool Use] <bash - pwd>
[Tool Use] <read - claude-progress.txt>
[Tool Use] <read - feature_list.json>
[Assistant] Let me check the git log to see recent work.
[Tool Use] <bash - git log --oneline -20>
[Assistant] Now let me check if there's an init.sh script to restart the servers.
<Starts the development server>
[Assistant] Excellent! Now let me navigate to the application and verify that some fundamental features are still working.
<Tests basic functionality>
[Assistant] Based on my verification testing, I can see that the fundamental functionality is working well. The core chat features, theme switching, conversation loading, and error handling are all functioning correctly. Now let me review the tests.json file more comprehensively to understand what needs to be implemented next.
<Starts work on a new feature>
```

---

**Agent 失败模式与解决方案**

| 问题 | Initializer Agent 行为 | Coding Agent 行为 |
|------|----------------------|------------------|
| Claude 过早宣布整个项目完成 | 搭建 feature list 文件：基于输入规格，建立一个结构化 JSON 文件，列出端到端功能描述 | 在 session 开始时读取 feature list 文件，选择单个功能开始工作 |
| Claude 留下带 bug 或未记录进展的环境 | 写入初始 git 仓库和 progress notes 文件 | 在 session 开始时读取 progress notes 文件和 git commit 日志，对开发服务器跑基本测试以捕获未记录的 bug。在 session 结束时写 git commit 和 progress 更新 |
| Claude 过早标记功能为完成 | 搭建 feature list 文件 | 自行验证所有功能。只有在仔细测试后才标记功能为"passing" |
| Claude 需要花时间弄清楚如何运行应用 | 写一个能启动开发服务器的 `init.sh` 脚本 | 在 session 开始时读取 `init.sh` |

*总结长时间运行 AI agent 的四种常见失败模式及解决方案。*

---

## 未来工作

这项研究展示了长时间运行 agent harness 中的一组可能方案，让模型能够跨多个 context window 做增量进展。然而，仍有一些开放问题。

最值得关注的是：单一的通用 coding agent 在跨 context 场景下是否表现最好，还是通过 multi-agent 架构能获得更好的性能？专门化的 agent——比如测试 agent、QA agent 或代码清理 agent——在软件开发生命周期的子任务上可能做得更好，这似乎是合理的。

此外，这个 demo 针对全栈 web 应用开发做了优化。未来的方向是将这些发现推广到其他领域。这些经验中的部分或全部很可能适用于其他类型的长时间运行 agentic 任务，比如科学研究或金融建模。

---

### 致谢

作者：Justin Young。特别感谢 David Hershey、Prithvi Rajasakeran、Jeremy Hadfield、Naia Bouscal、Michael Tingley、Jesse Mu、Jake Eaton、Marius Buleandara、Maggie Vo、Pedram Navid、Nadine Yasser 和 Alex Notov 的贡献。

这项工作反映了 Anthropic 多个团队的集体努力，他们让 Claude 能够安全地进行长周期自主软件工程，特别是 code RL 和 Claude Code 团队。有兴趣贡献的候选人欢迎在 [anthropic.com/careers](http://anthropic.com/careers) 申请。

---

^1 我们在这里称它们为不同的 agent，仅仅是因为它们有不同的初始 user prompt。system prompt、工具集和整体 agent harness 在其他方面完全相同。
