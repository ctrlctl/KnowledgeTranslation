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

# 让文档自己测试自己

> 原文：[How We Made Our Docs Test Themselves](https://www.langchain.com/blog/our-docs-test-themselves)
> 来源：LangChain Blog | 2026-04-15
> 作者：Naomi Pentrel

---

## 索引

- [要点](#要点)
- [问题：无法测试的内联代码](#问题无法测试的内联代码)
- [方案：Deep Agents + Skills](#方案deep-agents--skills)
- [SKILL.md 的结构](#skillmd-的结构)

---

## 要点

- 文档中的代码示例**可以被测试**——大多数团队不做只是因为觉得麻烦
- 不需要大量手动工作
- 用 Deep Agents CLI 就能搞定

---

过时的代码示例是文档领域的普遍问题。每个发布教程、API 指南或集成示例的团队，最终都会看到示例随着依赖变化和 API 演进而失效。这个问题不是 LangChain 独有的，但我们的产品——以及整个 AI 和 LLM 领域——迭代速度极快，新模型、更新的 SDK、不断变化的最佳实践，意味着上个月能跑的代码今天可能就不行了。

让代码示例**可测试**能解决这个问题：在 CI 中运行它们，断言它们能正确执行，失效时让构建失败。但要让代码示例变得可测试并不简单，需要一些前期投入。这个设置成本可能让人望而却步，以至于项目永远不会启动。把这项工作**委派给 agent** 是完美的解决方案。

---

## 问题：无法测试的内联代码

内联代码示例写起来很方便：测试代码、复制相关片段、粘贴到 markdown 文件里、发布。问题是它们是静态的——当 API 变了，你可能忘记更新使用该 API 的代码示例。

理想情况下，你希望在代码示例失效时能收到通知，你需要持续集成测试。应用代码的原则——自动化检查、捕获变更和回归、出问题时让构建失败——同样适用于文档：**把代码示例当作必须通过测试的代码来对待**。

要让文档中的代码示例可测试，手动流程是这样的：

1. 将内联代码提取到独立文件
2. 添加 setup 和 teardown 代码
3. 添加标记来指定代码片段范围
4. 用工具提取代码片段
5. 将提取的代码片段作为可复用 snippet 包含在文档中
6. 用 CI 定期运行独立代码片段，以及在示例变更时运行

在 LangChain，我们用 **Deep Agents CLI** 来卸载这个迁移工作流，不需要写代码。

---

## 方案：Deep Agents + Skills

Deep Agents CLI 是一个命令行 agent，你可以和它对话。它的核心能力之一是使用 **skills**（技能）中的信息来执行任务。Skills 是可复用的指令，当任务匹配 skill 描述时 agent 会自动加载。这些 skill 的写法就像给同事写的分步操作说明。

我们就是这么做的。我们把每一步写给 agent 执行：

1. 将代码移到 `src/code-samples/{product}` 下的独立文件，按产品区域组织
2. 添加 setup 和 teardown，使代码片段成为完整可运行的示例
3. 用配置好的 linter 检查代码
4. 添加标记来定义代码片段，使用 `:snippet-start:` 和 `:snippet-end:` 标签；需要在 snippet 中排除的代码用 `:remove-start:` 和 `:remove-end:`
5. 运行代码示例来测试
6. 根据标记生成 snippet，并将生成的文件包含到文档中

这是流程中 agentic 的部分。在此之上，我们还需要一个 GitHub Action 来定期运行测试，测试失败时创建 ticket。

这个 skill 放在文档仓库的隐藏文件夹中：`.deepagents/skills/docs-code-samples/SKILL.md`。设置好之后，任何人都可以在文档仓库中打开 Deep Agents CLI，让 agent 把一个或多个文档中的代码示例变成可测试的。

当你让 Deep Agent "把 `streaming.mdx` 中的内联代码迁移为可测试的代码示例"时，它会使用这个 skill。Agent 创建正确的文件、添加正确的标签、运行正确的命令，并将代码片段包含到文档文件中。

---

## SKILL.md 的结构

`docs-code-samples` skill 位于 `.deepagents/skills/docs-code-samples/SKILL.md`。它的 frontmatter 包含一个 `description`，告诉 agent 何时使用它：

```yaml
---
name: docs-code-samples
description: Use this skill when migrating inline code samples from LangChain
  docs (MDX files) into external, testable code files that are extracted with
  Bluehawk and used as Mintlify snippets.
---
```

Skill 的正文包含 agent 需要的完整上下文：

- 何时使用该 skill
- 目录结构和文件布局
- 分步迁移指令
- 要运行的命令及顺序
- 约定（命名、标签、imports）

完整的 SKILL.md 文件可以在 [LangChain 的 GitHub 仓库](https://github.com/langchain-ai/langchain-docs)中查看。

---

这只是在仓库中使用 skills + Deep Agents 的一个例子。要开始使用 Deep Agents CLI，请查看 [CLI 文档](https://docs.langchain.com/docs/deep-agents/cli)。
