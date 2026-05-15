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

# 托管 Deep Agents：最快的生产级 Deep Agent 上线路径

> 原文：[Introducing Managed Deep Agents](https://www.langchain.com/blog/introducing-managed-deep-agents)
> 来源：LangChain Blog | 2026-05-13
> 作者：Victor Moreira

---

## 索引

- [核心要点](#核心要点)
- [为什么需要 Managed Deep Agents](#为什么需要-managed-deep-agents)
- [托管 Runtime](#托管-runtime)
- [Agent 上下文与文件](#agent-上下文与文件)
- [工具与沙箱](#工具与沙箱)
- [LangSmith 可观测性](#langsmith-可观测性)
- [工作原理](#工作原理)
- [适用场景](#适用场景)
- [开始使用](#开始使用)

---

## 核心要点

- 构建 agent 越来越容易，**运维 agent 仍然是难点**。长时间运行的 agent 需要持久执行、工具访问、沙箱、记忆和追踪——自己搭建这些会占用构建实际 agent 的时间。
- Managed Deep Agents 给开源 harness 一个在 LangSmith 中的**持久化运行环境**。你把 agent 定义留在自己的 repo 里，我们处理 runtime：线程、checkpointing、streaming、上下文和可观测性。
- **Context Hub** 给 agent 一个托管的地方来存储和更新它所知道的内容，让它能从真实使用中改进——而不仅仅是从部署时放进 prompt 的内容。

---

## 为什么需要 Managed Deep Agents

构建一个有用的 agent 越来越容易。在生产环境中运行它们仍然很难。

长时间运行的 agent 需要的不仅仅是一次模型调用。它们需要持久执行、streaming、记忆、文件、工具访问、人工审批、沙箱、追踪，以及一种随时间改进的方式。团队可以自己构建这些基础设施，但在 agent 还没有触达用户之前，这就已经是很大的负担了。你最终要在 agent 本身之外维护 runtime 基础设施、文件存储、工具配置、沙箱执行、线程状态、追踪和反馈循环。

Managed Deep Agents 将运维层打包在开源 Deep Agents harness 周围，让开发者可以**专注于 agent 行为**，而不是重建它周围的 runtime。

---

## 托管 Runtime

Managed Deep Agents 让你无需搭建自定义 agent server 就能创建托管的 Deep Agent。Runtime 支持持久线程、streaming 运行、checkpointing 和 human-in-the-loop 工作流。

你可以使用 API 来创建 agent、更新配置、创建线程、从你自己的产品或平台工作流中 stream 运行。API 面在 `/v1/deepagents` 下。

---

## Agent 上下文与文件

Managed Deep Agents 保持熟悉的 Deep Agents 项目结构，包括 `AGENTS.md`、`skills/`、`subagents/` 和 `tools.json`。这些文件定义了 agent 的行为方式、可用工具、可加载的专门技能，以及可以委派工作的子 agent。Managed Deep Agents 在 LangSmith 中存储和版本化这些文件，让 agent 定义可以随时间演进。

**Context Hub** 给 agent 一个托管的地方来跨运行保留和更新它需要的上下文。这对需要跟踪用户偏好、项目细节、研究笔记、操作流程或其他工作上下文的 agent 很重要。

你可以选择启用 **LangSmith Engine** 来审查 agent traces，发现 agent prompts 和代码中的 bug 和改进空间。在运行之间，agent 可以回顾对话、从真实使用中学习、更新 Context Hub 文件。随着时间推移，这让 agent 能从它实际做的工作中改进。

例如，对于一个支持分诊 agent，LangSmith Engine 可以注意到用户不断询问同一个内部流程，然后更新它的操作笔记。

---

## 工具与沙箱

工具通过 `tools.json` 配置——与 Deep Agents 使用的模型相同。你可以在 `tools.json` 中定义的任何工具上启用 Human-in-the-loop。

Managed Deep Agents 还支持**沙箱支持的执行**，用于需要代码、shell 命令和文件 I/O 的工作流。这对需要分析数据、操作文件、运行脚本或创建产出物的 agent 很有用。

不需要为每个 agent 重建工具和沙箱设置，你可以把配置保留在托管 runtime 中，通过 LangSmith 操作它。

---

## LangSmith 可观测性

Managed Deep Agents 的运行自动在 LangSmith 中被追踪。团队可以检查工具调用、调试行为、审查中间步骤，理解 agent 如何随时间改进。

这给开发者提供了他们已经用于 agent 和 LLM 应用的相同可观测性工作流，现在直接连接到托管 runtime。

---

## 工作原理

上线路径是 API-first。你用 Managed Deep Agents API 创建或更新 agent，然后上传或引用定义它的文件——包括指令、skills、subagents 和工具配置。

从那里，你可以创建线程并从你的应用 stream 运行，无需部署自定义 agent server。agent 运行时，你可以在 LangSmith 中检查 traces 和 agent 上下文。

---

## 适用场景

Managed Deep Agents 为需要长时间工作、使用工具、保留上下文和产出产出物的 agent 设计。几个例子：

- **支持和分诊 agent**：跨长时间线程工作，跟踪先前上下文，需要时升级，从重复问题中更新自己的操作笔记
- **研究 agent**：收集来源、写笔记、保留中间发现，跨多个 session 产出交付物
- **Coding agent**：需要文件系统、shell 命令、工具访问和可恢复执行来处理较长任务
- **数据分析 agent**：运行代码、保留产出物，跨探索性工作流维护上下文
- **内部运维 agent**：从重复使用中改进自己的上下文，如入职助手、政策 agent 或工作流协调器

这些 agent 需要的不仅仅是一个 prompt 和一次工具调用。它们需要一个能支持**持久工作**的 runtime。

---

## 开始使用

Managed Deep Agents 是想要 Deep Agents + LangSmith 托管 runtime 基础设施的团队的最快路径。你可以把 agent 定义留在自己的 repo 里，然后用 API 在 LangSmith 中创建和操作托管 agent。这意味着开发者可以用开源 harness 构建，同时依赖 LangSmith 提供持久执行、托管上下文、沙箱支持的工作流——全部集成 LangSmith 可观测性。

Managed Deep Agents 目前在 private beta 中。如果你在构建需要持久执行、工具、沙箱、追踪和托管生产路径的 deep agent，可以加入 private beta 等待列表。

---
