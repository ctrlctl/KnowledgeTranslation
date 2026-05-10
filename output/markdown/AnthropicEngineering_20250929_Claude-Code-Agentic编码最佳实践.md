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

> 原文：[Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices)
> 来源：Anthropic Engineering | 2025-09-29
> 作者：Anthropic

## 索引

- [核心约束：上下文窗口](#核心约束上下文窗口)
- [给 Claude 验证自身工作的方式](#给-claude-验证自身工作的方式)
- [先探索，再计划，再编码](#先探索再计划再编码)
- [配置环境](#配置环境)
- [管理会话](#管理会话)
- [自动化与扩展](#自动化与扩展)
- [避免常见失败模式](#避免常见失败模式)

---

## 核心约束：上下文窗口

大多数最佳实践基于一个约束：**Claude 的上下文窗口填满得很快，性能随之下降**。

上下文窗口保存整个对话，包括每条消息、Claude 读取的每个文件和每个命令输出。单次调试会话或代码库探索可能生成和消耗数万 token。当上下文接近满时，Claude 可能开始"遗忘"早期指令或犯更多错误。

---

## 给 Claude 验证自身工作的方式

包含测试、截图或预期输出，让 Claude 能自我检查。这是**你能做的最高杠杆的事情**。

Claude 在能验证自身工作时表现显著更好——运行测试、比较截图、验证输出。没有明确的成功标准，它可能产出看起来对但实际不工作的东西。

策略示例：
- "写一个 validateEmail 函数。测试用例：user@example.com 为 true，invalid 为 false。实现后运行测试"
- "[粘贴截图] 实现这个设计。截图结果并与原始对比。列出差异并修复"
- "构建失败，错误是 [粘贴错误]。修复并验证构建成功。解决根本原因，不要压制错误"

---

## 先探索，再计划，再编码

将研究和规划与实现分开，避免解决错误的问题。推荐工作流四阶段：

1. **探索**：进入 plan mode，Claude 读取文件回答问题但不做修改
2. **计划**：让 Claude 创建详细实现计划
3. **实现**：退出 plan mode，让 Claude 编码并对照计划验证
4. **提交**：让 Claude 用描述性消息提交并创建 PR

Plan mode 有用但也增加开销。范围清晰的小任务直接做；规划在你不确定方法、修改多个文件或不熟悉代码时最有用。

---

## 配置环境

### 写有效的 CLAUDE.md

`/init` 生成基于项目结构的起始 CLAUDE.md，然后逐步完善。CLAUDE.md 是 Claude 在每次对话开始时读取的特殊文件，包含 bash 命令、代码风格和工作流规则。

保持简洁。对每一行问："删除这行会导致 Claude 犯错吗？"如果不会，删掉。**臃肿的 CLAUDE.md 会导致 Claude 忽略你的实际指令。**

✅ 包含：Claude 猜不到的 bash 命令、与默认不同的代码风格规则、测试指令、仓库礼仪、架构决策、环境怪癖、常见陷阱

❌ 排除：Claude 读代码就能搞清楚的东西、标准语言约定、详细 API 文档（改为链接）、频繁变化的信息、长解释、逐文件描述

### 配置权限

三种减少中断的方式：
- **Auto mode**：分类器模型审查命令，只阻止看起来有风险的
- **权限白名单**：允许已知安全的特定工具
- **沙箱**：OS 级隔离，限制文件系统和网络访问

### 创建 Skills

在 `.claude/skills/` 中创建 SKILL.md 文件，给 Claude 领域知识和可复用工作流。Claude 在相关时自动应用，或你可以用 `/skill-name` 直接调用。

### 创建自定义 Subagent

在 `.claude/agents/` 中定义专门助手，Claude 可以委派隔离任务给它们。Subagent 在自己的上下文中运行，有自己的工具集。

---

## 管理会话

### 尽早频繁纠正

注意到 Claude 偏离轨道时立即纠正。最好的结果来自紧密的反馈循环。

- **Esc**：中途停止 Claude，上下文保留
- **Esc + Esc 或 /rewind**：恢复之前的对话和代码状态
- **/clear**：在不相关任务之间重置上下文

如果你在同一会话中纠正 Claude 超过两次同一问题，上下文已被失败方法搞乱。`/clear` 并用更具体的 prompt 重新开始。

### 积极管理上下文

- 任务之间频繁使用 `/clear`
- 自动压缩触发时，Claude 总结最重要的内容
- 用 `/compact <instructions>` 更精细控制
- 用 `/btw` 问快速问题，答案不进入对话历史

### 用 Subagent 做调查

委派研究："use subagents to investigate X"。它们在独立上下文中探索，保持主对话干净。

由于上下文是根本约束，subagent 是最强大的工具之一。当 Claude 研究代码库时会读大量文件，全部消耗你的上下文。Subagent 在独立上下文窗口中运行并报告摘要。

---

## 自动化与扩展

### 非交互模式

`claude -p "prompt"` 用于 CI、pre-commit hooks 或脚本。

### 多 Claude 会话并行

- **Worktrees**：在隔离的 git checkout 中运行独立 CLI 会话
- **Agent teams**：多个会话的自动协调
- **Writer/Reviewer 模式**：一个 Claude 实现，另一个审查

### Fan out 跨文件

循环调用 `claude -p` 处理每个文件，用 `--allowedTools` 限定权限。

---

## 避免常见失败模式

- **厨房水槽会话**：一个任务中混入不相关内容。修复：任务间 `/clear`
- **反复纠正**：Claude 做错，你纠正，还是错。修复：两次失败后 `/clear`，写更好的初始 prompt
- **过度指定的 CLAUDE.md**：太长导致 Claude 忽略一半。修复：无情修剪
- **信任-验证鸿沟**：看起来合理但不处理边缘情况。修复：始终提供验证
- **无限探索**：不限定范围的"调查"。修复：缩小范围或用 subagent
