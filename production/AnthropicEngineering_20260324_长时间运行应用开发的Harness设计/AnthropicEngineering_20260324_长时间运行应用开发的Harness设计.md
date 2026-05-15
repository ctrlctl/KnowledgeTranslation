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

# 长时间运行应用开发的 Harness 设计

> 原文：[Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
> 来源：Anthropic Engineering | 2026-03-24
> 作者：Prithvi Rajasekaran

---

## 索引

- [背景：长时间运行 Agent 的挑战](#背景长时间运行-agent-的挑战)
- [前端设计实验：Generator-Evaluator 循环](#前端设计实验generator-evaluator-循环)
- [应用到全栈开发](#应用到全栈开发)
- [三 Agent 架构的实际效果](#三-agent-架构的实际效果)
- [简化 Harness](#简化-harness)
- [更新后的 Harness 测试：DAW](#更新后的-harness-测试daw)
- [展望](#展望)

---

作者：Prithvi Rajasekaran，Anthropic Labs 团队成员。

过去几个月我一直在研究两个相互关联的问题：让 Claude 产出高质量的前端设计，以及让它在没有人类干预的情况下构建完整应用。这项工作源于我们早期在前端设计技能和长时间运行 coding agent harness 上的努力，我和同事通过 prompt engineering 和 harness 设计将 Claude 的性能提升到远超基线——但两者最终都触及了天花板。

为了突破，我寻找了在两个截然不同的领域都适用的新型 AI 工程方法——一个由主观品味定义，另一个由可验证的正确性和可用性定义。受 GAN（生成对抗网络）的启发，我设计了一个带有 **generator 和 evaluator agent** 的多 agent 结构。构建一个能可靠评分——且有品味的——evaluator，意味着首先要开发一套标准，将"这个设计好吗？"这样的主观判断转化为具体的、可评分的条件。

然后我将这些技术应用到长时间运行的自主编码中，从早期 harness 工作中带来两个教训：将构建分解为可处理的块，以及使用结构化工件在 session 之间传递上下文。最终结果是一个**三 agent 架构——planner、generator 和 evaluator**——在多小时的自主编码 session 中产出丰富的全栈应用。

---

## 背景：长时间运行 Agent 的挑战

我们之前展示过 harness 设计对长时间运行 agentic 编码的有效性有重大影响。在早期实验中，我们用 initializer agent 将产品规格分解为任务列表，coding agent 一次实现一个功能，然后通过工件传递上下文跨 session。

但一些问题持续存在。对于更复杂的任务，agent 仍然会随时间偏离轨道。我们观察到两种常见失败模式：

第一种是模型在冗长任务中随着 context window 填满而**失去连贯性**。一些模型还表现出"**context anxiety**"（上下文焦虑），在它们认为接近 context 限制时过早地开始收尾工作。**Context reset**——完全清除 context window 并启动新 agent，结合携带前一个 agent 状态和下一步的结构化交接——解决了这两个问题。这与 compaction 不同，compaction 是在原地总结对话早期部分让同一个 agent 在缩短的历史上继续。虽然 compaction 保持了连续性，但它不给 agent 一个干净的起点，这意味着 context anxiety 仍然可能持续。

第二个问题是**自我评估**。当被要求评估自己产出的工作时，agent 倾向于自信地赞美工作——即使对人类观察者来说质量明显平庸。这个问题在设计等主观任务上尤其突出。将做工作的 agent 与评判工作的 agent 分离是解决这个问题的强力杠杆。调优一个独立的 evaluator 使其持怀疑态度，比让 generator 对自己的工作持批判态度要容易得多。

---

## 前端设计实验：Generator-Evaluator 循环

我从前端设计开始实验，因为自我评估问题在这里最明显。没有任何干预时，Claude 通常倾向于安全、可预测的布局——技术上功能正常但视觉上平淡无奇。

两个洞察塑造了我为前端设计构建的 harness。第一，虽然美学不能完全简化为分数，但可以通过编码设计原则和偏好的评分标准来改进。第二，通过将前端生成与前端评分分离，我们可以创建一个驱动 generator 产出更强输出的反馈循环。

我编写了四个评分标准给 generator 和 evaluator agent：

1. **设计质量**：设计是否感觉像一个连贯的整体而非部件的集合？
2. **原创性**：是否有自定义决策的证据，还是模板布局、库默认值和 AI 生成模式？
3. **工艺**：技术执行——排版层次、间距一致性、色彩和谐、对比度。
4. **功能性**：独立于美学的可用性。

我强调设计质量和原创性超过工艺和功能性。Claude 在工艺和功能性上默认就得分不错，但在设计和原创性上经常产出平淡的输出。标准明确惩罚高度通用的"AI slop"模式。

我在 Claude Agent SDK 上构建了循环。Generator agent 首先基于用户 prompt 创建 HTML/CSS/JS 前端。我给 evaluator 提供了 Playwright MCP，让它在评分前直接与实时页面交互。每个周期运行 5-15 次迭代，完整运行可达四小时。

在一个值得注意的例子中，我提示模型为一个荷兰艺术博物馆创建网站。到第九次迭代，它产出了一个干净的深色主题着陆页。然后在第十个周期，它完全抛弃了这种方法，将网站重新想象为一个空间体验：一个用 CSS 透视渲染的棋盘格地板的 3D 房间，艺术品以自由形式挂在墙上，通过门廊导航而非滚动或点击。这是我之前从未在单次生成中见过的创造性飞跃。

---

## 应用到全栈开发

有了这些发现，我将这种 GAN 启发的模式应用到全栈开发。Generator-evaluator 循环自然映射到软件开发生命周期，其中代码审查和 QA 扮演与设计 evaluator 相同的结构角色。

我构建了一个三 agent 系统：

- **Planner**：接受简单的 1-4 句 prompt 并扩展为完整产品规格。我提示它对范围要有雄心，聚焦产品上下文和高层技术设计而非详细技术实现。
- **Generator**：以 sprint 方式工作，每次从规格中拿起一个功能。每个 sprint 用 React、Vite、FastAPI 和 SQLite 栈实现应用。
- **Evaluator**：使用 Playwright MCP 像用户一样点击运行中的应用，测试 UI 功能、API 端点和数据库状态。对每个 sprint 按标准评分，任何标准低于阈值则 sprint 失败。

每个 sprint 前，generator 和 evaluator 协商一个 **sprint contract**：在写任何代码之前就商定"完成"对这块工作意味着什么。

---

## 三 Agent 架构的实际效果

我用以下 prompt 测试：*"创建一个 2D 复古游戏制作器，包含关卡编辑器、精灵编辑器、实体行为和可玩测试模式。"*

| Harness | 时长 | 成本 |
|---------|------|------|
| Solo（单 agent） | 20 分钟 | $9 |
| 完整 harness | 6 小时 | $200 |

Harness 贵了 20 倍以上，但输出质量差异立即可见。Solo 运行的应用看起来符合预期，但点击后问题开始出现：布局浪费空间、工作流僵硬、最关键的是游戏本身坏了——实体出现在屏幕上但不响应输入。

Harness 运行从同一个单句 prompt 开始，但 planner 将其扩展为跨十个 sprint 的 16 功能规格。应用立即展现出更多打磨和流畅度。精灵编辑器更丰富、更全功能。最大的区别在游戏模式——我实际上能移动实体并玩游戏。

从日志中可以清楚看到 evaluator 让实现与规格保持一致。每个 sprint 它都遍历 sprint contract 的测试标准，通过 Playwright 操作运行中的应用，对任何偏离预期行为的地方提 bug。

---

## 简化 Harness

第一组结果令人鼓舞，但也笨重、慢且昂贵。逻辑上的下一步是找到简化 harness 而不降低性能的方法。

一个通用原则是：**harness 中的每个组件都编码了关于模型不能自己做什么的假设，这些假设值得压力测试**——因为它们可能不正确，也因为随着模型改进它们会很快过时。

随着 Opus 4.6 的发布，有充分理由期望它需要比 4.5 更少的脚手架。我开始移除 sprint 结构——Opus 4.6 可以原生处理这种分解。我将 evaluator 移到运行结束时的单次 pass，而不是每个 sprint 评分。

实际含义是：**evaluator 不是一个固定的是/否决策。当任务超出当前模型能可靠独立完成的范围时，它才值得成本。**

---

## 更新后的 Harness 测试：DAW

我用以下 prompt 测试更新后的 harness：*"在浏览器中使用 Web Audio API 构建一个全功能 DAW。"*

| Agent & 阶段 | 时长 | 成本 |
|-------------|------|------|
| Planner | 4.7 分钟 | $0.46 |
| Build（第 1 轮） | 2 小时 7 分钟 | $71.08 |
| QA（第 1 轮） | 8.8 分钟 | $3.24 |
| Build（第 2 轮） | 1 小时 2 分钟 | $36.89 |
| QA（第 2 轮） | 6.8 分钟 | $3.09 |
| Build（第 3 轮） | 10.9 分钟 | $5.88 |
| QA（第 3 轮） | 9.6 分钟 | $4.06 |
| **总计** | **3 小时 50 分钟** | **$124.70** |

Generator 模型在规划应用和 agent 设计、连接 agent、测试后交给 QA 方面做得很好。QA agent 仍然捕获了真实的差距，指出核心 DAW 功能是仅展示的而没有交互深度。

最终应用远非专业音乐制作程序，但有一个功能性音乐制作程序的所有核心部件：工作的编排视图、混音器和传输控制在浏览器中运行。我能够完全通过提示组装一个短歌曲片段：agent 设置了节拍和调性、铺设了旋律、构建了鼓轨、调整了混音器电平并添加了混响。

---

## 展望

随着模型持续改进，我们大致可以期望它们能够工作更长时间、处理更复杂的任务。在某些情况下，这意味着围绕模型的 scaffold 随时间变得不那么重要。另一方面，模型越好，开发能实现超越模型基线的复杂任务的 harness 的空间就越大。

几个值得带走的教训：

- 始终实验你正在构建的模型，阅读它在真实问题上的 trace，调优其性能
- 对于更复杂的任务，有时可以通过分解任务并对问题的每个方面应用专门化 agent 来获得提升
- 当新模型发布时，重新审视 harness，剥离不再承重的部分，添加新部分以实现之前不可能的更大能力

我的信念是：**有趣的 harness 组合空间不会随着模型改进而缩小。相反，它在移动**，AI 工程师的有趣工作是持续找到下一个新颖的组合。

---

### 致谢

特别感谢 Mike Krieger、Michael Agaby、Justin Young、Jeremy Hadfield、David Hershey、Julius Tarng、Xiaoyi Zhang、Barry Zhang、Orowa Sidker、Michael Tingley、Ibrahim Madha、Martina Long 和 Canyon Robbins 对这项工作的贡献。感谢 Jake Eaton、Alyssa Leonard 和 Stef Sequeira 帮助塑造这篇文章。
