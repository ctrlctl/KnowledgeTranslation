<style>
body, .markdown-body { font-family: "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, serif; font-size: 15px; line-height: 2; max-width: 38em; margin: 0 auto; padding: 2em; color: #2c2c2c; background: #faf8f5; }
</style>

> 原文：[Using skills to accelerate OSS maintenance](https://developers.openai.com/blog/skills-agents-sdk)
> 来源：OpenAI Developers Blog | 2026-04-30
> 作者：OpenAI

## 索引

- [概述](#概述)
- [AGENTS.md 的角色](#agentsmd-的角色)
- [验证规则](#验证规则)
- [Skill 描述的重要性](#skill-描述的重要性)
- [将机械操作放入脚本](#将机械操作放入脚本)
- [自动化集成测试](#自动化集成测试)
- [发布检查](#发布检查)
- [用 Codex 做 PR 审查](#用-codex-做-pr-审查)

---

## 概述

本文分享了在 OpenAI Agents SDK（Python 和 JavaScript）仓库中使用 Codex Skills 加速开源维护的实践经验。Skills 在这些仓库中最有效的方式是成为仓库正常工作流的一部分。

核心模式：
- **AGENTS.md** 告诉 Codex 哪些工作流是必需的
- **description** 告诉它何时路由到这些工作流
- **scripts/** 处理确定性部分
- **模型**处理上下文相关部分

---

## AGENTS.md 的角色

AGENTS.md 定义了强制性 skill 使用规则：

- 编辑运行时或 API 变更前使用 `$implementation-strategy`
- 运行时代码、测试、示例或构建行为变更时运行 `$code-change-verification`
- OpenAI API 或平台工作时使用 `$openai-knowledge`
- 实质性代码工作准备好审查时使用 `$pr-draft-summary`

AGENTS.md 不仅用于 skill 触发。Python 仓库还在其中记录了公共 API 兼容性规则：保持导出构造函数参数和 dataclass 字段的位置含义。

---

## 验证规则

`$code-change-verification` 的规则不是"总是运行长验证栈"，而是"**当运行时代码、测试、示例或构建行为变更时运行，且在通过前不标记工作完成**"。

条件部分让纯文档工作保持轻量。强制部分确保 SDK 代码变更经过仓库的标准验证步骤。实际验证栈编码在 skill 本身中。

---

## Skill 描述的重要性

description 是路由契约的一部分——Codex 在读取 skill 其余部分之前的主要路由信号。

差的描述："Run the mandatory verification stack in the OpenAI Agents JS monorepo."

好的描述："Run the mandatory verification stack **when changes affect runtime code, tests, or build/test behavior** in the OpenAI Agents JS monorepo."

更具体的版本告诉模型三件事：何时适用、什么类型的变更应触发、检查是否可选。如果路由感觉不可靠，先修复元数据再添加更多代码。

---

## 将机械操作放入脚本

可靠的分工：
- **解释、比较和报告**留给模型（读源码推断预期行为、比较日志与预期、判断兼容性风险、产出解释）
- **确定性、重复的 shell 工作**放入 scripts/（运行验证命令、启动示例运行、收集日志、暴露 start/stop/status 等命令）

如果模型每次都要重新发现相同的 shell 配方，那通常是该配方应该成为脚本的信号。

---

## 自动化集成测试

两层验证：
1. **examples-auto-run**：自动运行仓库内示例，记录 stdout/stderr，然后让 Codex 逐个比较日志与源代码的预期行为。比简单的脚本级 pass/fail 更准确。
2. **integration-tests**（JS 仓库）：发布包到本地 Verdaccio registry，在 Node.js、Bun、Deno、Cloudflare Workers 和 Vite React app 中测试安装和运行。

---

## 发布检查

release-review 工作流找到上一个 release tag，diff 到最新 main，让 Codex 检查向后兼容性、回归和缺失的迁移说明。

审查从"安全发布"开始，只在 diff 显示具体证据时切换到阻止。每个阻止决定必须附带具体的解除阻止清单。

---

## 用 Codex 做 PR 审查

Codex GitHub PR auto review 已成为这些仓库中大多数代码变更的常规审查工具。对于直接的程序 bug、回归和缺失测试，依赖 Codex 作为必需审查路径在实践中已足够安全。

**人工审查仍然重要**，但针对不同类别：API/架构选择、影响产品预期的行为变更、命名和迁移决策、需要跨维护者对齐的变更。

AGENTS.md 也可以编码这种分工：告诉 Codex 什么对正确性审查重要，Codex 一致地应用该指导。
