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

# 为不同模型调优深度Agent

> 原文：[Tuning Deep Agents Different Models](https://www.langchain.com/blog/tuning-deep-agents-different-models)
> 来源：LangChain Blog | 2026-04-30
> 作者：LangChain

---

## 索引

- [核心观点](#核心观点)
- [为什么这很重要](#为什么这很重要)
- [效果测量](#效果测量)
- [每个模型改了什么](#每个模型改了什么)
- [Harness Profile 如何工作](#harness-profile-如何工作)

---

## 核心观点

Deep Agents 之前以通用方式设计，旨在跨模型家族良好工作。现在添加了**模型特定的 profile**来调整 prompt、工具和中间件。这允许更好地符合特定模型家族的 prompting 指南。为 OpenAI、Anthropic 和 Google 模型开箱即用地提供 profile，在 tau2-bench 子集上比默认 harness **提升了 10-20 分**。

此前，`deepagents` 附带一组旨在跨所有 LLM 良好工作的固定 prompt、工具和中间件。构建者可以换入不同模型或用额外工具扩展 harness，但基础 prompt、工具和中间件是固定的，未针对每个模型优化。

**一个 harness 不可能对每个模型都是最优的。** 所以 LangChain 让按模型变化 harness 变得容易。

---

## 为什么这很重要

不同模型家族有不同的最佳实践：
- 工具调用格式和约定不同
- 规划和推理的 prompt 策略不同
- 中间件需求不同

通过 harness profile，构建者可以：
- 按 agent 管理 profile
- 版本化它们
- 轻松测试配置差异

---

## 效果测量

在 tau2-bench（多轮工具使用 + 指令遵循）的精选子集上测量性能。使用前沿模型尚未饱和的更难任务的精选子集，以更好地测量 harness 级别变化对 agent 的影响。

使用 Codex 和 Claude prompting 指南作为每个 profile 应用什么变化的来源。

---

## 每个模型改了什么

**Codex** 的主要变化包括：
- 针对 Codex 特定的工具调用格式优化
- 调整规划和执行指令

**Opus** 的主要变化全部集中在工具使用和规划的 prompting 上。例如，向 prompt 添加了关于工具使用模式和规划策略的特定片段。

---

## Harness Profile 如何工作

Harness profile 是一个声明式覆盖层，用于 harness 中按模型变化的部分：system prompt 前缀/后缀、工具包含和命名、中间件选择、subagent 配置和 skills。

为模型或提供商注册一个 profile（或从 YAML 加载现有的），`create_deep_agent` 在你切换模型时自动适配。重要的是，你的调用点不变。

为 OpenAI、Anthropic 和 Google 模型提供默认值。你可以覆盖它们、在其上叠加自己的，或作为插件分发 profile。

也可以在 YAML 中声明 profile：

```yaml
# 示例 profile 声明
model: anthropic/claude-opus
prompt_prefix: "..."
tools:
  - name: web_search
    enabled: true
middleware:
  - planning_middleware
```

目标是无论你选择哪个模型，Deep Agents 都给你工具和默认值来为你的任务创建最佳 harness。
