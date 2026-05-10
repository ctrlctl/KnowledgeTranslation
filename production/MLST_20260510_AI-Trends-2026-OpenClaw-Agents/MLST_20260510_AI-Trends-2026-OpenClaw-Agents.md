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

# AI Trends 2026：OpenClaw Agents、推理 LLM 与实用视角

> 原文：[AI Trends 2026: OpenClaw Agents, Reasoning LLMs, and More with Sebastian Raschka - #762](https://twimlai.com/podcast/twimlai/ai-trends-2026-openclaw-agents-reasoning-llms)
> 来源：Machine Learning Street Talk (TWIML) | 2026-05-10
> 嘉宾：Sebastian Raschka（独立 LLM 研究者）

---

## 索引

- [一年回顾：推理革命与工具使用](#一年回顾推理革命与工具使用)
- [Harness 工程比模型本身更重要](#harness-工程比模型本身更重要)
- [OpenClaw 的意义：让普通人看到 Agent 能做什么](#openclaw-的意义让普通人看到-agent-能做什么)
- [LLM 最实用的方式：开发确定性工具](#llm-最实用的方式开发确定性工具)
- [One-shot 神话与社交媒体的幸存者偏差](#one-shot-神话与社交媒体的幸存者偏差)
- [2026 三大趋势：推理、推理时扩展、Agentic 循环](#2026-三大趋势推理推理时扩展agentic-循环)
- [可验证奖励：推理训练的核心引擎](#可验证奖励推理训练的核心引擎)

---

## 一年回顾：推理革命与工具使用 [02:10]

Sebastian 认为过去一年最大的两个变化：

1. **推理训练**（reasoning）——架构没变，还是 LLM，但后训练技术让模型能解决更复杂的问题。DeepSeek R1 是标志性事件。
2. **工具使用**（tool use）——从"让 LLM 从记忆中回答一切"转向"让 LLM 调用计算器、搜索引擎等工具"。这需要专门训练，但能显著降低幻觉率。

推理 = 给 LLM 更多"思考时间"。工具使用 = 让 LLM 不再硬算，而是用正确的工具。两者结合是过去一年进步的主要来源。

---

## Harness 工程比模型本身更重要 [06:23]

Sebastian 的假设：如果把最好的开源模型放进 ChatGPT/Claude/Gemini 的界面里，你几乎能得到相同质量的体验。**很多使用场景的价值来自模型外面的工具包装**，而非模型本身。

这就是去年流行起来的"harness engineering"概念——界面从简单聊天框演变为：上传文件、访问整个 git 目录、自动运行单元测试、查看 file diff。没有单一突破，但所有小改进加起来让 LLM 显著更强。

推理模式的改进也是渐进的：一年前你几乎总要用最高推理模式（等 5 分钟），现在中等模式就够用了。auto 模式让模型自己决定需要多少思考——这是生活质量的巨大提升。

---

## OpenClaw 的意义：让普通人看到 Agent 能做什么 [14:30]

Sebastian 把 OpenClaw（原名 Motebot）类比为 AlphaGo——不是因为技术突破，而是因为它**让非技术人群兴奋起来**。

他个人还没有让 agent 管理日历和邮件——"有点信任问题"。但他认为 OpenClaw 的价值在于展示 LLM 能做什么，让更多人开始尝试。

---

## LLM 最实用的方式：开发确定性工具 [16:35]

Sebastian 和主持人 Sam 都发现：LLM 给他们带来最大价值的方式不是直接执行任务，而是**帮他们开发确定性工具**。

Sebastian 的例子：
- 用 LLM 写了一个原生 macOS app，给播客音频添加章节标记
- 写了一个 app 从 arXiv 链接批量提取论文标题、日期、作者
- 给自己网站加了暗色模式（一直拖延了很久的事）

关键洞察：**LLM 不做日常任务本身，而是开发做任务的工具**。对于确定性任务，用 LLM 来执行是浪费——用 LLM 来开发一个确定性工具才是正确用法。

"如果你只有锤子，一切看起来都像钉子"——要认清问题的本质，选择最佳工具。

---

## One-shot 神话与社交媒体的幸存者偏差 [28:04]

Sam 提出一个观察：社交媒体上到处是"我 one-shot 了这个"的帖子，但他自己去试同样的事情，结果往往很糟糕。

Sebastian 同意：即使是简单的 macOS app（PDF 转 PNG/WebP），也需要多次迭代才能让所有按钮正确工作。可能的解释：
- 也许那些人的 prompt 写得特别好
- 也许只是运气好（幸存者偏差）
- 也许他们没展示失败的尝试

结论：**"one-shot"不代表今天 LLM 的真实工作方式。** 迭代仍然是常态。

---

## 2026 三大趋势：推理、推理时扩展、Agentic 循环 [30:04]

Sebastian 预测 2026 年的三个主要方向：

1. **推理训练**——后训练算法持续改进（他列出了 15 种不同的改进方法，包括 token-level log probs、Nvidia 的 GDPO 等）。研发重心已从预训练转向后训练，因为预训练已经很成熟，而后训练还有大量低垂果实。

2. **推理时扩展**（inference scaling）——更复杂的技术来在推理阶段获得更好结果，部分与训练相关但主要是使用阶段的优化。

3. **Agentic 循环**——从 turn-by-turn 交互转向让 LLM 在循环中运行，公司会加倍投入优化这个循环。

---

## 可验证奖励：推理训练的核心引擎 [33:42]

推理训练的核心是**可验证奖励**（verifiable rewards）——有些任务可以确定性地验证答案是否正确：

- **数学**：让模型用 `\boxed{}` 格式输出答案，用 SymPy/Wolfram Alpha 符号化比较
- **代码**：检查代码是否编译通过、测试是否通过

优势：你可以让 LLM 生成 60000 个答案，然后瞬间计算所有答案的奖励——不需要人类评估。这比 RLHF 可扩展得多。

这只是开始。未来会扩展到更多类型的奖励：格式奖励（think tags）、风格奖励等。关键是找到更多可以自动验证的任务维度。

Sebastian 认为学习编程和数学仍然有价值——不是因为 LLM 不能做，而是因为**理解底层原理让你更高效地使用 LLM**。他加暗色模式的例子：让 LLM 生成后，自己直接改 CSS 比反复 prompt "往左移一点"要快得多。
