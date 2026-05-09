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

# Shell + Skills + Compaction：长时间运行Agent的实用技巧

> 原文：[Shell + Skills + Compaction: Tips for long-running agents](https://developers.openai.com/blog/skills-shell-tips)
> 来源：OpenAI Developers Blog | 2026-02-11
> 作者：Charlie Guo

---

## 索引

- [心智模型](#心智模型)
- [为什么它们组合更好](#为什么它们组合更好)
- [Tips and Tricks](#tips-and-tricks)
- [三种构建模式](#三种构建模式)

---

我们正在从单轮助手转向处理真实知识工作的长时间运行agent：读取大型数据集、更新文件、编写应用。

基于开发者反馈和我们自己构建Codex及内部agent的经验，我们发布了一组新的agentic原语：

- **Skills**（遵循Agent Skills开放标准）：可复用、版本化的指令，可以挂载到容器中让agent更可靠地执行任务
- **升级版Shell工具**：OpenAI托管的容器，有受控的互联网访问，agent可以安装依赖、运行脚本、写输出
- **服务端Compaction**：自动压缩长agentic运行，永远不会撞到context限制

---

## 心智模型

### Skills："按需加载的程序"

Skill是一组文件加上一个包含frontmatter和指令的 `SKILL.md` 清单。可以理解为：模型在需要做真实工作时可以查阅的**版本化操作手册**。

平台向模型暴露每个skill的 `name`、`description` 和 `path`。模型用这些元数据决定是否调用skill。如果调用，它读取 `SKILL.md` 获取完整工作流。

### Shell工具："Agent的执行环境"

Shell工具让模型在真实终端环境中工作：
- **托管容器**：由OpenAI管理
- **本地shell运行时**：你自己执行（相同的工具语义，但你控制机器）

### Compaction："保持长运行继续"

随着工作流变长，会撞到context window限制。服务端compaction通过管理context window和自动压缩对话历史来保持长运行继续。

两种方式：
- **服务端compaction**：context超过阈值时自动在流中运行
- **独立compact端点**：当你想显式控制compaction时机时使用

---

## 为什么它们组合更好

- **Skills** 减少prompt意大利面——将稳定的程序和示例移入可复用包
- **Shell** 提供完整执行环境——安装代码、运行脚本、写输出
- **Compaction** 在长运行中保持连续性——无需手动context手术

组合起来，你得到**有真实执行的可重复工作流**，而不用把system prompt变成脆弱的巨型文档。

---

## Tips and Tricks

### 1) Skill描述要像路由逻辑写，不是营销文案

Skill的description实际上是模型的**决策边界**。它应该回答：
- 何时应该使用这个？
- 何时不应该使用？
- 输出和成功标准是什么？

实用模式：在description中直接包含"Use when vs. Don't use when"块，保持具体（输入、涉及的工具、预期产物）。

### 2) 添加负面示例和边界情况以减少误触发

一个令人惊讶的失败模式：**让skills可用最初可能降低正确触发率**。

修复方法：负面示例加边界情况覆盖。写几个明确的"不要在...时调用这个skill"的情况（以及应该做什么替代）。

Glean的经验：基于skill的路由最初在定向eval中触发率**下降约20%**，在添加负面示例和边界情况覆盖后恢复。

### 3) 把模板和示例放在skill内部（未使用时基本免费）

如果你一直把模板塞进system prompt，停下来。

Skill内部的模板和示例有两个优势：
- 在需要时精确可用（skill被调用时）
- 不会为无关查询膨胀token

Glean报告这个模式在生产中带来了**最大的质量和延迟提升**——因为那些示例只在skill触发时加载。

### 4) 从一开始就为长运行设计：容器复用 + compaction

长周期agent很少作为one-shot prompt成功。从一开始就规划连续性：
- 跨步骤复用同一容器（稳定依赖、缓存文件、中间输出）
- 传递 `previous_response_id` 让模型在同一线程中继续工作
- 将compaction作为**默认的长运行原语**，而非紧急回退

### 5) 需要确定性时，显式告诉模型使用skill

默认行为是模型决定何时使用skill。但当你运行有明确契约的生产工作流时，直接说：

> "Use the `<skill name>` skill."

这是你能拉的**最简单的可靠性杠杆**。它将模糊路由变成显式契约。

### 6) Skills + 网络是高风险组合（为隔离而设计）

结合skills与开放网络访问创造了**数据泄露的高风险路径**。

强默认姿态：
- Skills：允许
- Shell：允许
- 网络：**仅在最小允许列表下启用**，按请求，用于窄范围任务

### 7) 用 `/mnt/data` 作为产物交接边界

对于托管shell工作流，将 `/mnt/data` 作为写输出的标准位置。

心智模型：**工具写入磁盘，模型推理磁盘内容，开发者从磁盘检索。**

### 8) 理解允许列表是两层系统

- **组织级允许列表**（管理员配置）：设置最大允许目的地
- **请求级 `network_policy`**：必须是组织允许列表的子集

保持组织允许列表小而稳定，请求允许列表更小。

### 9) 用 `domain_secrets` 做认证调用

如果允许的域需要auth header，使用 `domain_secrets` 让模型永远看不到原始凭证。运行时模型看到占位符，sidecar只为批准的目的地注入真实值。

### 10) 云端和本地使用相同API

实用开发循环：
1. **本地开始**（快速迭代、访问内部工具、容易调试）
2. **移到托管容器**（需要可重复性、隔离和部署一致性时）
3. **Skills在两种模式下保持相同**（工作流稳定，即使执行位置变化）

---

## 三种构建模式

### 模式A：安装 → 获取 → 写产物

最简单的托管shell用法：agent安装依赖、获取外部数据、产出具体交付物。

这个模式是真实工作agent的基础——它创造了**干净的审查边界**：你的应用可以向用户展示产物、记录它、diff它、或输入到后续步骤。

### 模式B：Skills + Shell实现可重复工作流

一旦你构建了一两个成功的shell工作流，你会注意到下一个问题：**当prompt漂移时可靠性下降**。

这就是skills的用武之地：
1. 将工作流（步骤、guardrails、模板）编码在skill中
2. 将skill挂载到shell环境
3. 让agent遵循skill确定性地产出产物

特别适合：电子表格分析/编辑、数据集清洗+摘要生成、标准化报告生成。

### 模式C（高级）：Skills作为企业工作流载体

一个早期模式：在单工具调用和多工具编排之间的差距中准确度下降。Skills通过使工具推理更程序化来弥合这个差距，而不膨胀system prompt。

Glean的具体案例：
- 面向Salesforce的skill将eval准确度从 **73% → 85%**
- 减少time-to-first-token **18.1%**

Skills成为**活的SOP（标准操作程序）**：随组织演进而更新，由agent一致执行。

---

## 总结

- 用 **Skills** 编码"如何做"（程序、模板、guardrails）
- 用 **Shell** 执行"做什么"（安装、运行、写产物）
- 用 **Compaction** 保持长运行连贯（无需手动管理context）
