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

# 用深度Agent构建公司尽调系统

> 原文：[Building A Company Due Diligence Agent With Deep Agents](https://www.langchain.com/blog/building-a-company-due-diligence-agent-with-deep-agents-langsmith-and-parallel)
> 来源：LangChain Blog | 2026-05-02
> 作者：LangChain

---

**索引**

- [概览](#概览)
- [定义Parallel研究工具](#定义parallel研究工具)
- [定义研究Subagent](#定义研究subagent)
- [创建编排Agent](#创建编排agent)
- [流式执行进度](#流式执行进度)
- [为什么可观测性对FSI很重要](#为什么可观测性对fsi很重要)
- [合规和审计今天如何工作](#合规和审计今天如何工作)
- [Trace展示了什么](#trace展示了什么)
- [引用和置信度](#引用和置信度)

---

公司尽调（due diligence）是金融服务中随处可见的工作流。PE分析师筛选交易、银行信贷团队评估借款人、合规团队入职新实体、保险承保人评估商业投保人。研究遵循一致的模式：拿一家公司，从多个维度调查它，产出一份结构化情报报告，其中每个声明都有来源追踪。

本cookbook构建了一个自动化该工作流的agent，结合LangChain的**Deep Agents**进行编排和**Parallel的Task API**进行网络研究。Deep Agents处理规划、subagent委派和上下文管理。Parallel处理实际研究，返回带有逐字段引用、推理trace和校准置信度分数（通过Basis）的结构化发现。当一个研究方向的发现引发新问题时，Parallel的交互式研究功能让agent可以在前一个研究线程的完整上下文中链接后续查询。

---

## 概览

Agent编排五个研究方向，每个由专门的subagent处理：

- **公司概况**——法律实体结构、关键高管、创立历史、员工数、办公地点
- **财务健康**——融资历史、收入信号、估值指标、盈利标记
- **诉讼和监管**——诉讼、SEC文件、制裁筛查、监管行动、和解
- **新闻和声誉**——近期媒体报道、领导层变动、争议标记、媒体情绪
- **竞争格局**——识别前三名直接竞争对手和目标公司的定位

竞争格局返回命名列表后，编排器为每个竞争对手分别派发一个**竞争对手分析subagent**，并行运行——这是典型的Deep Agents扇出模式，每个实例在自己的隔离上下文中运行。

编排器然后读取每份工作底稿，交叉引用矛盾和低置信度发现，在出现差异时通过Parallel的Search API进行临时查询，并撰写带有风险标记和引用追踪的最终报告。

尽调需要这种多步架构，因为**早期发现会改变接下来需要调查什么**。如果公司概况揭示目标是子公司，财务分析需要覆盖母公司。如果诉讼扫描发现SEC调查，风险评估就会改变。Deep Agents的规划工具让编排器在发现改变研究计划时能够适应。

在Rivian Automotive（NASDAQ: RIVN）上端到端验证：九次调用，约23分钟。

---

## 定义Parallel研究工具

我们定义两个工具。第一个包装Parallel的Task API用于带Basis感知置信度处理的结构化研究。第二个使用LangChain集成的web搜索工具用于综合期间的快速事实查询。

```python
@tool
def research_task(query: str, output_description: str,
                  previous_interaction_id: Optional[str] = None) -> dict:
    """通过Parallel的Task API运行结构化网络研究。
    返回带有逐字段引用和置信度分数（Basis）的发现。"""
    runner = ParallelTaskRunTool(
        processor="pro-fast",
        task_output_schema=output_description,
    )
    result = runner.invoke({"input": query})
    parsed = parse_basis(result)
    # ...返回findings、citations_by_field、interaction_id
    # 如果有低置信度字段，附加low_confidence_warning
```

工具在原始API调用之外做三件事：调用`parse_basis(result)`提取逐字段引用和低置信度字段名称；将这些名称作为显式`low_confidence_warning`浮现在工具返回值中，让调用subagent的推理循环可以决定是否链接后续查询；返回`interaction_id`以便链接调用可以通过`previous_interaction_id`锚定到同一研究线程。

---

## 定义研究Subagent

每个研究方向获得自己的subagent，带有专门的system prompt和对`research_task`工具的访问。

```python
corporate_profile_subagent = {
    "name": "corporate-profile",
    "description": "研究公司结构、领导层、创立历史和员工数",
    "system_prompt": """你是公司研究分析师。给定一家公司，
    使用research_task工具查找法律实体名称、关键高管、
    总部位置、员工数、公司结构等。
    如果结果包含low_confidence_warning，
    使用返回的interaction_id链接后续查询来验证标记的字段。""",
    "tools": [research_task],
}
```

Phase-2扇出subagent为竞争格局识别的每个竞争对手调用一次：

```python
competitor_analysis_subagent = {
    "name": "competitor-analysis",
    "description": "为一个命名的竞争对手生成聚焦的概况",
    "tools": [research_task],
}
```

---

## 创建编排Agent

主agent协调subagent、审查发现中的矛盾、并产出最终报告。我们用`FilesystemBackend`支持它，使工作底稿和最终备忘录持久化到磁盘。

```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[quick_search],
    subagents=[
        corporate_profile_subagent,
        financial_health_subagent,
        litigation_subagent,
        news_reputation_subagent,
        competitive_landscape_subagent,
        competitor_analysis_subagent,
    ],
    system_prompt=diligence_instructions,
    backend=FilesystemBackend(root_dir=REPORTS_DIR, virtual_mode=True),
)
```

编排器的流程：规划研究→Phase 1并行派发五个subagent→Phase 2按竞争对手扇出→审查和交叉引用→综合最终报告（含执行摘要、风险标记、引用追踪）。

---

## 流式执行进度

对于长时间运行的尽调，流式传输agent的进度以实时看到规划、工具调用和subagent活动。传入`subgraphs=True`接收subagent执行内部的事件。

---

## 为什么可观测性对FSI很重要

在FSI中，监管机构、审计师和风险团队越来越期望公司能重建AI辅助输出是如何产生的，特别是当这些输出影响重大商业决策时。

六个月后，内部审计师、合规审查员、模型风险团队、投资委员会或监管机构可能会问AI辅助的尽调备忘录是如何产生的。哪些来源支撑了每个重大结论？附加了什么置信度？人类在哪里审查或覆盖了输出？agent的过程是否记录得足够好以便重建？

在FSI中，"agent给了我一个答案"不是可辩护的控制姿态。这就是为什么trace在FSI中特别重要：

- **日志记录越来越被强制要求**。EU AI Act要求高风险AI系统的自动事件日志
- **决策可解释性需要逐声明的锚定**。当AI输入影响受监管决策时，机构必须解释该输入是如何形成的
- **第三方AI需要持续监督**。Trace记录了发送给每个提供商什么、返回了什么、以及这些输出如何影响最终备忘录
- **运营韧性依赖快速根因分析**

---

## 合规和审计今天如何工作

FSI团队已经有一套证明研究备忘录如何产生的系统：分析师工作底稿、引用列表、来源审批、版本历史和合规审查。当审查员问一个结论是如何得出的，分析师可以走过推理过程。

AI agent改变了这个模型。"分析师"不再只是一个人。它是LLM调用、工具调用、检索来源、中间输出和状态转换的图。除非这些步骤在运行时被捕获，最终备忘录可能存活，但产生它的过程可能消失。**Trace恢复了附着点。它成为机器侧的工作底稿。**

---

## Trace展示了什么

打开任何运行，你首先看到的是编排器的计划：一个四阶段TODO，在任何subagent运行之前布局研究策略。

Phase 1然后并行派发所有五个研究subagent。点击trace中任何任务节点，你可以看到那个subagent在做什么：它发出的prompt、它进行的Parallel调用、以及返回的来源。

Phase 1完成后，编排器扇出按竞争对手的分析（Phase 2），交叉引用工作底稿中的矛盾（Phase 3），并综合最终备忘录（Phase 4）。每个工具调用都被捕获。

---

## 引用和置信度

对于合规审查员，相关视图是`parallel_task_run`内的**basis payload**。Parallel为每个输出附加来源URL、置信度标签（高/中/低）和一行推理trace解释答案是如何组装的。

在上面展示的Rivian公司概况调用中，agent的中等置信度输出锚定在四个来源：Rivian在SEC.gov上的10-K和2026年年报、第三方复制的2026年代理声明、以及Wikipedia。两个一手SEC文件、一个二手复制和一个三手来源的组合——这正是合规审查员想要标记的锚定模式。

有了trace，**锚定是逐声明可检查的**，像这样的来源模式在跨运行中变得可纠正。没有这一层的工作底稿会平铺列出相同的四个URL，没有哪个是一手来源的信号。
