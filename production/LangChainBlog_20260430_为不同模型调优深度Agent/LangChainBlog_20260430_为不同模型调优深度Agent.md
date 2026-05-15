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

**索引**

- [Profile的效果测量结果](#profile的效果测量结果)
- [每个模型改了什么](#每个模型改了什么)
- [Profile底层如何工作](#profile底层如何工作)

---

**TL;DR：** Deep Agents之前以通用方式设计，跨模型系列工作良好。今天我们添加了**模型特定的profile**来调整prompt、工具和中间件。这让我们能更好地遵循特定模型系列的prompting指南。我们为OpenAI、Anthropic和Google模型开箱即用地提供profile，在tau2-bench子集上比默认harness提升了10-20分。

在今天之前，deepagents附带一组旨在跨所有LLM良好工作的prompt、工具和中间件。构建者可以换入不同模型或用额外工具和system prompt扩展harness。但基础prompt、工具和中间件是固定的，没有针对每个模型优化。

这很重要，因为：

**Prompting指南因模型而异。** OpenAI的Codex Prompting Guide规定了特定的工具实现和名称（`apply_patch`、`shell_command`），对Codex模型有显著影响。Anthropic的Claude prompting指导强调不同的惯例。即使在同一系列内，Opus 4.6→4.7迁移指南也标记了值得做的prompt级别更改。

**评估排行榜显示同一模型在不同harness中可以产生非常不同的性能。** Terminal-Bench 2.0是最干净的公开例子。Claude Code harness在Opus 4.6提交中排名最后。我们在之前的工作中看到了类似的harness工程效果：仅通过应用harness层面的更改（如prompt和中间件hook），就将gpt-5.2-codex从52.8%提升到66.5%（从Top 30到Top 5）。

**单一harness不可能对每个模型都是最优的。** 所以我们让按模型变化harness变得容易。

---

## Profile的效果测量结果

为了判断这有多重要，我们在tau2-bench子集（多轮工具使用+指令遵循）上测量了性能。我们使用了前沿模型尚未饱和的更难任务的策划子集，以便更好地衡量harness层面更改对agent的影响。

| 模型 | 基础Deep Agents Harness | 使用自定义Profile |
|------|------------------------|------------------|
| GPT 5.3 Codex | 33% | 53% |
| Claude Opus 4.7 | 43% | 53% |

---

## 每个模型改了什么

我们使用Codex和Claude prompting指南作为每个profile应用什么更改的来源。

**对于Codex，主要更改包括：**

- **工具更改**：用推荐的`apply_patch`工具覆盖deepagents中默认的`file_edit`实现，并将deepagents中的`execute`工具名称别名为`shell_command`
- **Prompt更改**：主要围绕工具调用和规划，使用prompting指南中的细节。例如："在任何tool call之前，决定你需要的所有文件和资源。将读取、搜索和其他独立操作批量化为并行tool call，而不是逐个发出。"

**对于Opus，主要更改都是围绕工具使用和规划的prompt。** 例如：

```
<tool_result_reflection>
收到工具结果后，仔细反思其质量并确定最优下一步，
然后再继续。用你的思考来基于新信息规划和迭代，
然后采取最佳下一步行动。
</tool_result_reflection>

<tool_usage>
当任务依赖于文件、测试或系统输出的状态时，
使用工具直接观察该状态，而不是从记忆中推理它可能包含什么。
读取文件再描述它们。运行测试再声称它们通过。
搜索代码库再断言某个符号存在或不存在。
用工具主动调查是默认工作模式，不是后备方案。
</tool_usage>
```

我们的结论是：**暴露一个按模型自定义harness的接口，是帮助构建者管理每个agent的profile、版本化它们、并轻松测试配置差异的有用原语。**

---

## Profile底层如何工作

Harness profile是harness中按模型变化部分的声明式覆盖层：system prompt前缀/后缀、工具包含和命名、中间件选择、subagent配置和skills。你为模型或提供商注册profile（或从YAML加载现有的），`create_deep_agent`在你换模型时自动适配。重要的是，你的调用点不变。

我们为OpenAI、Anthropic和Google模型提供默认值。你可以覆盖它们、在上面叠加你自己的、或将profile作为插件分发。

```python
from deepagents import HarnessProfile, register_harness_profile

register_harness_profile(
    "openai:gpt-5.4",
    HarnessProfile(
        system_prompt_suffix="Respond in under 100 words.",
        excluded_tools={"execute"},
        excluded_middleware={"SummarizationMiddleware"},
    ),
)
```

或在YAML中声明：

```yaml
# openai.yaml
base_system_prompt: You are helpful.
system_prompt_suffix: Respond briefly.
excluded_tools:
  - execute
  - grep
excluded_middleware:
  - SummarizationMiddleware
```

目标是无论你选择哪个模型，Deep Agents都给你工具和默认值来为你的任务创建最佳harness。
