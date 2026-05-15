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

# 用 Agent Skills 装备 Agent 应对真实世界

> 原文：[Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
> 来源：Anthropic Engineering | 2025-10-16
> 作者：Barry Zhang, Keith Lazuka, Mahesh Murag

---

## 索引

- [Skills 如何工作](#skills-如何工作)
- [上下文窗口中的触发流程](#上下文窗口中的触发流程)
- [Skills 中的代码执行](#skills-中的代码执行)
- [编写 Skills 的最佳实践](#编写-skills-的最佳实践)
- [安全考虑](#安全考虑)
- [展望](#展望)

---

> **更新：** 我们已将 Agent Skills 作为跨平台可移植性的开放标准发布。（2025年12月18日）

随着模型能力提升，我们现在可以构建与完整计算环境交互的通用 agent。例如 Claude Code 可以使用本地代码执行和文件系统跨领域完成复杂任务。但随着这些 agent 变得更强大，我们需要更可组合、可扩展、可移植的方式来为它们装备领域特定的专业知识。

这促使我们创建了 **Agent Skills**：由指令、脚本和资源组成的有组织文件夹，agent 可以动态发现和加载它们以在特定任务上表现更好。Skills 通过将你的专业知识打包为可组合资源来扩展 Claude 的能力，将通用 agent 转变为适合你需求的专门 agent。

为 agent 构建 skill 就像为新员工准备入职指南。不再需要为每个用例构建碎片化的定制 agent，任何人现在都可以通过捕获和分享程序性知识来用可组合能力专门化他们的 agent。

---

## Skills 如何工作

让我们通过一个真实例子来看 Skills 的实际运作：驱动 Claude 最近推出的文档编辑能力的 skill 之一。Claude 已经很擅长理解 PDF，但在直接操作 PDF（如填写表单）方面能力有限。这个 PDF skill 让我们赋予 Claude 这些新能力。

最简单地说，skill 是一个包含 **SKILL.md 文件**的目录。这个文件必须以包含必需元数据（name 和 description）的 YAML frontmatter 开头。

启动时，agent 将每个已安装 skill 的 name 和 description 预加载到 system prompt 中。这个元数据是**渐进式披露（progressive disclosure）** 的第一层：它提供刚好足够的信息让 Claude 知道何时应该使用每个 skill，而不将全部内容加载到上下文中。

文件的实际正文是第二层细节。如果 Claude 认为 skill 与当前任务相关，它会通过将完整 SKILL.md 读入上下文来加载该 skill。

随着 skill 复杂度增长，它们可能包含太多上下文无法放入单个 SKILL.md，或只在特定场景中相关的上下文。在这些情况下，skill 可以在目录中捆绑额外文件并从 SKILL.md 中按名称引用它们。这些额外链接文件是第三层（及更深层）细节，Claude 可以选择仅在需要时导航和发现。

![](images/fig_01.png)

**渐进式披露是使 Agent Skills 灵活且可扩展的核心设计原则。** 像一本组织良好的手册——从目录开始，然后是具体章节，最后是详细附录——skills 让 Claude 仅在需要时加载信息。拥有文件系统和代码执行工具的 agent 在处理特定任务时不需要将整个 skill 读入上下文窗口。这意味着可以捆绑到 skill 中的上下文量实际上是无限的。

---

## 上下文窗口中的触发流程

![](images/fig_02.png)

*图：skill 被用户消息触发时上下文窗口的变化*

操作序列：
1. 开始时，上下文窗口有核心 system prompt 和每个已安装 skill 的元数据，以及用户的初始消息
2. Claude 通过调用 Bash 工具读取 `pdf/SKILL.md` 的内容来触发 PDF skill
3. Claude 选择读取与 skill 捆绑的 `forms.md` 文件
4. 最后，Claude 在从 PDF skill 加载了相关指令后继续处理用户的任务

---

## Skills 中的代码执行

Skills 还可以包含 Claude 根据任务性质自行决定执行的代码作为工具。大语言模型擅长很多任务，但某些操作更适合传统代码执行。例如，通过 token 生成排序列表比直接运行排序算法昂贵得多。除了效率考虑，许多应用需要只有代码才能提供的确定性可靠性。

在我们的例子中，PDF skill 包含一个预写的 Python 脚本，读取 PDF 并提取所有表单字段。Claude 可以运行这个脚本而无需将脚本或 PDF 加载到上下文中。因为代码是确定性的，这个工作流是一致且可重复的。

![](images/fig_03.png)

---

## 编写 Skills 的最佳实践

- **从评估开始：** 通过在代表性任务上运行 agent 并观察它们在哪里挣扎来识别能力差距。然后增量构建 skills 来解决这些不足。
- **为规模而结构化：** 当 SKILL.md 文件变得笨重时，将内容拆分为单独文件并引用它们。如果某些上下文互斥或很少一起使用，保持路径分离将减少 token 使用。代码既可以作为可执行工具也可以作为文档。应该清楚 Claude 是应该直接运行脚本还是将其读入上下文作为参考。
- **从 Claude 的角度思考：** 监控 Claude 在真实场景中如何使用你的 skill 并基于观察迭代。特别注意 skill 的 name 和 description——Claude 会用这些来决定是否在响应当前任务时触发该 skill。
- **与 Claude 迭代：** 在与 Claude 一起工作时，让 Claude 将其成功方法和常见错误捕获为 skill 中的可复用上下文和代码。如果它在使用 skill 完成任务时偏离轨道，让它自我反思哪里出了问题。

---

## 安全考虑

Skills 通过指令和代码为 Claude 提供新能力。虽然这使它们强大，但也意味着恶意 skills 可能在使用环境中引入漏洞，或指导 Claude 泄露数据和采取非预期行动。

我们建议只从受信任的来源安装 skills。从不太受信任的来源安装时，在使用前彻底审计。首先阅读 skill 中捆绑文件的内容以理解它做什么，特别注意代码依赖和捆绑资源（如图片或脚本）。同样注意 skill 中指示 Claude 连接到潜在不受信任外部网络源的指令或代码。

---

## 展望

Agent Skills 目前在 Claude.ai、Claude Code、Claude Agent SDK 和 Claude 开发者平台上受支持。在接下来的几周，我们将继续添加支持创建、编辑、发现、分享和使用 Skills 完整生命周期的功能。

我们特别兴奋于 Skills 帮助组织和个人与 Claude 分享其上下文和工作流的机会。我们还将探索 Skills 如何通过教 agent 涉及外部工具和软件的更复杂工作流来补充 MCP 服务器。

展望更远，我们希望让 agent 能够自己创建、编辑和评估 Skills，让它们将自己的行为模式编纂为可复用能力。

Skills 是一个简单概念，有着相应简单的格式。这种简单性使组织、开发者和最终用户更容易构建定制 agent 并赋予它们新能力。
