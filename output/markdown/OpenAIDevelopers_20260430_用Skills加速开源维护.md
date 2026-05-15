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

# 用 Skills 加速开源维护

> 原文：[Using skills to accelerate OSS maintenance](https://developers.openai.com/blog/skills-agents-sdk)
> 来源：OpenAI Developers Blog | 2026-04-30
> 作者：OpenAI

---

## 索引

- [把工作流放在仓库里](#把工作流放在仓库里)
- [AGENTS.md 的角色](#agentsmd-的角色)
- [验证规则](#验证规则)
- [Changeset 验证](#changeset-验证)
- [使用最新文档](#使用最新文档)
- [准备 PR 交接](#准备-pr-交接)
- [Skill 描述的重要性](#skill-描述的重要性)
- [将机械操作放入脚本](#将机械操作放入脚本)
- [自动化集成测试](#自动化集成测试)
- [发布检查](#发布检查)
- [在 CI 中运行工作流](#在-ci-中运行工作流)
- [用 Codex 做 PR 审查](#用-codex-做-pr-审查)
- [总结](#总结)

---

## 把工作流放在仓库里

在这些仓库中，我们用 skill 来捕获仓库特定的工作流。一个 skill 是一小包操作知识：一个 SKILL.md 清单，加上可选的 `scripts/`、`references/` 和 `assets/`。

Codex 定制文档描述了为什么这样做效果好：skill 适合可重复工作流，因为它们可以携带更丰富的指令、脚本和参考资料，而不会预先膨胀 agent 的 context。这与 skill 使用的**渐进式披露模型**一致：

1. 先看到元数据（name 和 description）
2. 只在 skill 被选中时加载 SKILL.md
3. 只在需要时读取 references 或运行 scripts

两个 SDK 仓库都把这些工作流放在代码旁边：

- `.agents/skills` in openai-agents-python
- `.agents/skills` in openai-agents-js

Python 仓库是更简单的基线：

- **code-change-verification**：代码或构建行为变更时运行必需的格式化、lint、类型检查和测试栈
- **docs-sync**：对照代码库审计文档，找出缺失、不正确或过时的文档
- **examples-auto-run**：以自动模式运行示例，带日志和重跑辅助
- **final-release-review**：比较上一个发布标签与当前候选版本，检查发布就绪性
- **implementation-strategy**：在编辑运行时或 API 变更前决定兼容性边界和实现方法
- **openai-knowledge**：通过官方 Docs MCP 工作流拉取当前 OpenAI API 和平台文档
- **pr-draft-summary**：在交接时准备分支名建议、PR 标题和草稿描述
- **test-coverage-improver**：运行覆盖率，找到最大缺口，提出高影响力测试

JavaScript 仓库遵循相同的通用模式，然后为其 npm monorepo 和发布流程添加了几个仓库特定的 skill：

- **changeset-validation**：检查 changeset 和 bump 级别是否实际匹配包 diff
- **integration-tests**：发布包到本地 Verdaccio 注册表，验证跨支持运行时的安装和运行行为
- **pnpm-upgrade**：以协调方式更新 pnpm 工具链和 CI pin

比具体列表更重要的是**模式**。每个 skill 有一个窄契约、一个清晰的触发条件和一个具体的输出。一些最有用的 skill 不是硬门禁。`docs-sync` 和 `test-coverage-improver` 是报告优先的工作流：它们检查当前 diff 或覆盖率产出物，优先处理重要的，在编辑前请求批准。

---

## AGENTS.md 的角色

当仓库在正确时机**要求**使用 skill 时，skill 变得更有用。这就是 AGENTS.md 的作用。

AGENTS.md 指南将这些文件描述为仓库级指令，随代码库一起旅行，在 agent 开始工作前生效。它还建议保持简短。

在 Agents SDK 仓库中，我们用这个空间放 Codex 每次都应遵循的规则，把最高价值的放在顶部。实践中，两个仓库都用简短的 if/then 规则来强制 skill 使用：

- 编辑运行时或 API 变更前，调用 `$implementation-strategy` 先决定兼容性边界和实现方法
- 如果变更影响 SDK 代码、测试、示例或构建行为，调用 `$code-change-verification`
- 如果 JavaScript 包变更影响发布元数据，调用 `$changeset-validation`
- 如果工作涉及 OpenAI API 或平台集成，调用 `$openai-knowledge`
- 工作完成准备交接时，调用 `$pr-draft-summary`

一个紧凑版本：

```markdown
# AGENTS.md

## Mandatory skill usage
- Use $implementation-strategy before editing runtime or API changes
- Run $code-change-verification when runtime code, tests, examples, or build/test behavior changes
- Use $openai-knowledge for OpenAI API or platform work
- Use $pr-draft-summary when substantial code work is ready for review

## Build and test commands
- Python: make format, make lint, make typecheck, make tests
- TypeScript: pnpm i, pnpm build, pnpm -r build-check, pnpm lint, pnpm test
```

AGENTS.md 不仅用于 skill 触发。Python 仓库还在那里记录了公共 API 兼容性规则：保持导出构造函数参数和 dataclass 字段的位置含义，新的可选参数追加到末尾，如果重排不可避免则添加兼容性测试。这是另一个好模式：**把发布关键的兼容性规则和 skill 触发放在同一个地方。**

---

## 验证规则

一个清晰的例子是 `$code-change-verification`。在两个仓库中，规则不是"总是运行一个长验证栈"。规则是"当运行时代码、测试、示例或构建/测试行为变更时运行它，在它通过之前不标记工作完成。"

条件部分让纯文档工作保持轻量。强制部分确保 SDK 代码变更经过仓库的标准验证步骤。

Python 仓库要求：`make format` → `make lint` → `make typecheck` → `make tests`

JavaScript 仓库要求这个确切顺序：`pnpm i` → `pnpm build` → `pnpm -r build-check` → `pnpm -r -F "@openai/*" dist:check` → `pnpm lint` → `pnpm test`

Skill 编码了仓库的"已验证"定义，AGENTS.md 让这个定义可执行。

---

## Changeset 验证

JavaScript 仓库对包变更有一个额外的强制步骤：`$changeset-validation`，围绕 Changesets 构建。

当 `packages/` 下的任何东西变更，或 `.changeset/` 变更时，模型不仅要运行测试。它必须创建或更新正确的 changeset，验证 bump 级别，并确认 changeset 实际匹配 diff。

这个 skill 不仅检查文件是否存在。它让 Codex 判断 git diff，并把验证规则放在共享 prompt 中，让本地运行和 GitHub Actions 使用相同的逻辑。它还编码了仓库特定的策略：

- 当已存在一个时使用现有分支 changeset，而不是创建另一个
- 摘要保持一行 Conventional Commit 风格，可以兼作 commit 标题
- 1.0 之前，避免对正常功能工作做 major bump
- 验证所需的 bump 级别与实际包变更是否匹配

这让 Codex 负责在说工作完成之前验证它创建的发布元数据。

---

## 使用最新文档

两个仓库在工作涉及 OpenAI API 或平台集成时也要求 `$openai-knowledge`。这个 skill 是官方 OpenAI Docs MCP 的薄包装。

它不让模型从记忆中回答，而是告诉 Codex 使用 OpenAI Developer Documentation MCP 服务器来查找 Responses API、tools、streaming、Realtime 和 MCP 等界面的当前文档。

---

## 准备 PR 交接

在实质性工作结束时，两个仓库都使用 `$pr-draft-summary`。这个 skill 只在任务实际完成或准备审查、且变更涉及有意义的代码/测试/示例/文档/构建配置时触发。

它自动收集分支名、工作树状态、变更文件、diff 统计和最近提交，然后产出：

- 分支名建议
- PR 标题
- 草稿 PR 描述

输出格式故意严格。一旦你信任模型来验证和总结自己的工作，让它产出 PR 草稿是自然的最后一步。它保持交接一致，减少编码工作完成后的重复写作。

---

## Skill 描述的重要性

Skill 的 SKILL.md frontmatter 中的 `description` 字段是**路由契约的一部分**。这是结构性的，不是风格性的。

渐进式披露模型说这些字段在启动时为所有 skill 加载。完整的 SKILL.md 正文和任何 `scripts/`、`references/` 或 `assets/` 只在 skill 实际激活时才加载。

在 Agents SDK 仓库中，这使 description 成为 Codex 读取 skill 其余部分之前的主要路由信号之一。

具体例子，来自 `code-change-verification`：

❌ 太模糊：`Run the mandatory verification stack in the OpenAI Agents JS monorepo.`

✅ 更好（实际描述）：`Run the mandatory verification stack when changes affect runtime code, tests, or build/test behavior in the OpenAI Agents JS monorepo.`

更短的版本告诉 Codex skill 做什么，但没说**什么时候**适用、什么类型的变更应该触发它、或者检查是否可选。更具体的版本三者都告诉了模型。

一个实用教训：**花时间在 description 上。如果路由感觉不可靠，先修元数据再加代码。**

---

## 将机械操作放入脚本

下一个问题是什么属于模型、什么应该下推到脚本。一个可靠的分割是：

- **解释、比较和报告**留给模型
- **确定性的、重复的 shell 工作**放进 `scripts/`

在 Agents SDK 仓库中，我们尝试在模型的智能真正有用的地方使用模型，例如：

- 读源代码推断预期行为
- 比较日志与预期行为
- 决定发布 diff 是否包含真正的兼容性风险
- 产出维护者可以据此行动的解释

脚本则处理围绕这些工作的机械操作，例如：

- 按固定顺序运行仓库的必需验证命令
- 启动示例运行、收集每个示例的日志、为失败写重跑文件
- 在发布就绪审查前获取上一个发布标签

如果模型每次都要重新发现相同的 shell 配方，这通常是该配方应该成为脚本的信号。如果任务依赖上下文、权衡或解释，那部分应该留给模型。

---

## 自动化集成测试

两个仓库中最有用的工作流领域之一是自动化集成测试。这里有两个相关层次：

1. 在两个仓库中自动验证仓库内示例
2. 在 JavaScript 仓库中，单独验证发布的包在用户消费方式下安装后仍然工作

在这个设置之前，验证示例部分是手动的。你可以运行示例，但最后一英里往往依赖于目视检查日志或凭检查判断输出是否看起来正确。

第一层是 `examples-auto-run`。为了自动化示例验证，我们首先必须在两个仓库中构建非交互式示例执行的底层支持。这意味着让示例脚本可以在自动模式下运行，包括通常涉及提示或审批的示例。

基础工作包括：

- 自动回答常见交互提示
- 自动批准 HITL、MCP、apply_patch 和 shell 操作
- 把仍不适合自动化的示例放在 auto-skip 列表上
- 为每次示例运行写结构化日志
- 生成重跑文件，让失败可以重试而不重跑所有

一旦基础就位，我们把它组织为 skill，让工作流变得可复用且易于调用。

为了提高验证质量，runner 的工作是执行示例并保存它们的 stdout 和 stderr 到每个示例的日志中。然后 skill 让 Codex 逐个检查这些日志并与源代码比较：

1. 读示例源代码和注释
2. 推断预期流程
3. 打开匹配的日志
4. 比较预期行为与实际 stdout/stderr
5. 对每个成功的示例都这样做，不只是一个样本

这比试图把正确性编码为固定的脚本级断言更准确、更灵活。成功的退出码有用，但对于与真实 API 交互、使用工具或产出结构化输出的示例来说不够。

在 JavaScript 仓库中，还有第二层：单独的 `integration-tests` skill。这个工作流超越了在仓库内运行源示例。它把包发布到本地 Verdaccio 注册表，并在多个环境中测试安装和运行，包括 Node.js、Bun、Deno、Cloudflare Workers 和 Vite React 应用。

这捕获了不同类别的问题：不是"示例在仓库中能运行吗？"而是"包在发布、安装和运行时集成后仍然正确吗？"

---

## 发布检查

发布准备是这个模式有帮助的另一个领域。两个仓库中的发布审查工作流从找到上一个发布标签开始，与最新 main diff，然后让 Codex 检查该 diff 中的：

- 公共 API 和面向用户的 SDK 行为中的向后兼容性问题
- 回归，包括预期行为中的较小变化
- 需要的变更缺少迁移说明或发布说明更新

基于这些发现，skill 做出整体发布就绪判断。

一个具体例子是 openai/openai-agents-python#2480，发布审查整体保持绿色，同时仍然指出 Python 3.9 的移除和它需要的发布说明跟进：

> 发布判断：🟢 可以发布。Minor 版本 bump 包含预期的破坏性变更（移除 Python 3.9），未发现具体回归。
>
> Python 3.9 支持移除 - 风险：🟡 中等。固定在 Python 3.9 的用户将无法安装 0.9.0 版本。
> 行动：确保发布说明清楚指出 Python 3.9 的移除。

Skill 还定义了门禁决策如何做出。审查从"安全发布"开始，只在 diff 显示具体证据表明有真实问题时才切换到阻塞。每个阻塞判断必须附带具体的解除阻塞清单。

这比通用的"请审查发布"更有用。它强制模型对具体 diff 进行推理，并用运维术语解释结果。

---

## 在 CI 中运行工作流

一旦 skill 在本地有用，Codex GitHub Action 让在 CI 中自动化相同工作流变得容易。这在本地工作流已经稳定时效果最好，因为手动使用是你调试指令、完善脚本和发现真实边界情况的地方。

对于公共仓库，触发设计和 skill 本身一样重要。GitHub Action 安全清单建议：

- 限制谁可以启动工作流
- 优先使用可信事件或显式审批
- 清理来自 PR、commit、issue 或评论的 prompt 输入
- 保护 OPENAI_API_KEY
- 把 Codex 作为 job 的最后一步运行

---

## 用 Codex 做 PR 审查

自从 Codex GitHub PR 自动审查可用以来，Codex 在这些仓库的大多数代码变更中一直是有用的审查者。我们把它作为审查的常规部分使用，而不是特殊工具。

对于直接的程序 bug、回归和缺失测试，依赖 Codex 作为必需的审查路径在实践中已经足够安全。它在反复检查相同的正确性模式方面是一致的，并且为小修复和例行改进移除了一个主要瓶颈。

同行审查仍然重要，但针对不同类别的变更。人类审查在主要问题不是"这段代码正确吗？"而是"几个有效选项中我们应该选哪个，以及如何发布？"时仍然必不可少：

- API 或架构变更，有多个合理设计，维护者需要做显式选择
- 影响产品预期、向后兼容承诺或发布策略的行为变更
- 命名、迁移和发布沟通决策
- 需要跨维护者或团队对齐的变更

这也是吞吐量的重要贡献者。重复的审查和验证工作不再为每个低风险变更等待稀缺的审查者时间，而维护者可以专注于他们的判断最重要的高上下文审查。

---

## 总结

在 OpenAI Agents SDK 仓库中，skill 在作为仓库正常工作设置的一部分时效果最好：

- **AGENTS.md** 告诉 Codex 哪些工作流是必需的
- **description** 告诉它何时路由到这些工作流
- **scripts/** 处理确定性部分
- **模型**处理上下文相关部分
- 一旦工作流在本地稳固，**Codex GitHub Action** 可以把相同流程带入 CI

这让这些仓库中的日常工程工作更显式、更可靠。它也让更快地发布小改进变得更容易，因为验证、发布审查和 PR 交接现在遵循相同的可重复流程。

---

## 资源

- [OpenAI Agents SDK for Python](https://github.com/openai/openai-agents-python)
- [OpenAI Agents SDK for JS](https://github.com/openai/openai-agents-js)
- [Skills in Codex](https://developers.openai.com/codex/skills)
- [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Codex GitHub Action](https://developers.openai.com/codex/github-action)
- [Skills in OpenAI API cookbook](https://cookbook.openai.com/examples/agents_sdk/skills_in_openai_api)
