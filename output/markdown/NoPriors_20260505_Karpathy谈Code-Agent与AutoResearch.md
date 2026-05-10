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

# Andrej Karpathy 谈 Code Agent、AutoResearch 与 Loopy 时代

> 原文：[Andrej Karpathy on Code Agents, AutoResearch, and the Loopy Era of AI](https://traffic.megaphone.fm/PDP8703207384.mp3)
> 来源：No Priors | 2026-05-05
> 嘉宾：Andrej Karpathy

---

## 索引

- [AI 精神病：能力跃迁后的状态](#ai-精神病能力跃迁后的状态)
- [并行化与 token 吞吐量](#并行化与-token-吞吐量)
- [OpenClaw 与 Claw 实体](#openclaw-与-claw-实体)
- [Dobby：家庭自动化 Claw](#dobby家庭自动化-claw)
- [软件的未来：API 优先，Agent 是胶水](#软件的未来api-优先agent-是胶水)
- [AutoResearch：把自己从循环中移除](#autoresearch把自己从循环中移除)
- [Program.md 的元优化](#programmd-的元优化)
- [可验证性的边界](#可验证性的边界)
- [模型的锯齿状能力](#模型的锯齿状能力)
- [开源与前沿实验室的动态平衡](#开源与前沿实验室的动态平衡)
- [物理世界 vs 数字世界](#物理世界-vs-数字世界)
- [MicroGPT 与教育的未来](#microgpt-与教育的未来)

---

## AI 精神病：能力跃迁后的状态 [01:28]

Karpathy 说自己从 2025 年 12 月起就处于持续的"AI 精神病"状态。那个月发生了某种翻转——他从 80/20（自己写代码 vs 委托给 agent）变成了 20/80，现在可能更极端。他说自己**从 12 月起大概没手动写过一行代码**。

这种精神病的核心是：一切都感觉是 **skill issue**。不是能力不够，而是你还没找到正确的方式把现有工具串起来。没给 agents.md 写好指令、没配好 memory 工具——总觉得是自己的问题。

---

## 并行化与 token 吞吐量 [05:07]

Karpathy 的新焦虑：当一个 agent 在跑的时候，你应该同时启动更多 agent。如果你不受 token 预算限制，那**你自己就是系统的瓶颈**。

他把这比作 PhD 时代的 GPU 焦虑——GPU 空闲就意味着浪费 flops。现在不是 flops，是 **tokens**。你的 token 吞吐量是多少？你能调度多少 token？

如果 Claude Code 的额度用完了，就切到 Codex。订阅没用完就意味着你没有最大化自己的 token 吞吐。

---

## OpenClaw 与 Claw 实体 [06:38]

Karpathy 区分了几个层次：

1. **单个 agent session**（Claude Code / Codex）
2. **多个 agent 协作**——一个做研究、一个写代码、一个做计划
3. **Claw**——一种新层次的持久化实体。它不是你交互式参与的东西，而是有自己的 sandbox、自己的循环、在你不看的时候也在做事。有比默认 context compaction 更复杂的 memory 系统。

Peter Steinberger（OpenClaw 创始人）同时在至少五个方面做了创新：personality/soul document、memory 系统、WhatsApp 单一入口、自我修改能力、社区体验。

---

## Dobby：家庭自动化 Claw [09:25]

Karpathy 在一月份经历了一段"Claw 精神病"，构建了一个管理家庭的 Claw，叫 Dobby（家养小精灵）。

过程：他告诉 agent "我觉得家里有 Sonos"，agent 就去做了局域网 IP 扫描，找到了 Sonos 系统（没有密码保护），逆向工程了 API，三个 prompt 后音乐就从书房响起来了。

同样的方式接管了灯光、HVAC、窗帘、泳池/spa、安防摄像头。摄像头用变化检测 + Qwen 视觉模型，有人来就通过 WhatsApp 发图片通知他。

关键洞察：他以前用六个不同的 app 来控制这些系统。现在 Dobby 用自然语言统一控制一切。这指向一个未来——**app 不应该存在，应该只有 API，agent 是智能胶水**。

---

## 软件的未来：API 优先，Agent 是胶水 [13:09]

Karpathy 认为行业需要大规模重构：**客户不再是人类，而是代表人类行动的 agent**。

现在这需要一些 vibe coding，但他觉得一两年后这会变成 table stakes——任何 AI（包括开源模型）都能做到。barrier 会持续下降，最终变成"代你运行的临时软件"。

---

## AutoResearch：把自己从循环中移除 [16:26]

核心理念：要最大化 token 吞吐，你不能在循环里。你需要安排好一切让它完全自主运行。**你投入极少的 token，大量的事情在你的名义下发生。**

AutoResearch 就是这个理念的具体实现：给定目标、给定指标、给定边界，然后放手。

Karpathy 用他的 NanoChat 项目做实验。他已经用传统方式（两个十年的研究经验）把模型调得相当好了。然后让 AutoResearch 跑了一晚上——它发现了他遗漏的调优：value embeddings 的 weight decay、Adam betas 不够精细，而且这些参数之间有交互效应。

**单线程的 AutoResearch 就能在已经调好的 repo 上找到改进。** 前沿实验室有数万 GPU，很容易想象如何大规模并行化这种自动化。

---

## Program.md 的元优化 [20:59]

Program.md 是 Karpathy 用 Markdown 写的"AutoResearch 应该怎么工作"的指令。

递归的想法：不同的 program.md 会产生不同的进展速度。你可以想象：

- 多个"研究组织"（每个由一组 Markdown 文件描述）
- 有的做更少 standup、有的更冒险
- 一旦有了代码，就可以调优代码
- 看哪些改进来自哪里，然后让模型写出更好的 program.md

**每个研究组织本质上就是一组 Markdown 文件**，描述所有角色和连接方式。这是可以优化的代码。

层层递进：LLM → Agent → Claw 实体 → 多个 Claw → 对 Claw 的指令 → 对指令的优化。每一层都被视为理所当然后，下一层就出现了。

---

## 可验证性的边界 [23:39]

AutoResearch 的两个重要 caveat：

1. **只适用于有客观指标的领域**。写更高效的 CUDA kernel（行为相同但更快）是完美场景。如果你不能评估它，就不能 auto-research 它。

2. **模型仍然在接缝处爆裂**。如果你走得太远，整个系统实际上净负面。它们改进了很多，但仍然"粗糙"。

---

## 模型的锯齿状能力 [24:38]

Karpathy 的感受：同时在和一个极其聪明的 PhD + 系统程序员以及一个 10 岁小孩对话。人类的能力更耦合，agent 的**锯齿性（jaggedness）**要大得多。

经典例子：你问最先进的模型讲个笑话，得到的还是三四年前的"为什么科学家不信任原子？因为它们组成了一切。" 模型在 agentic 任务上能跑几小时移山倒海，但笑话还是五年前的烂笑话。

原因：笑话在 RL 的可验证域之外，没有被优化。这说明**"代码变好了其他一切也会变好"的前提并不完全成立**。有些东西被优化了，有些没有。你要么在模型被训练的轨道上（光速前进），要么不在（漫无目的）。

---

## 开源与前沿实验室的动态平衡 [49:08]

开源模型落后前沿大约 6-8 个月，而且在收敛。Karpathy 认为这个动态其实挺好：

- 前沿实验室有闭源 AI 做"oracle"
- 开源落后几个月但覆盖大量基础用例
- 对于大多数消费者场景，开源模型已经相当好了，甚至可以本地运行
- 前沿智能的需求会集中在"诺贝尔奖级别的工作"或"把 Linux 从 C 重写为 Rust"这种大项目

他对纯闭源集中化持警惕态度——集中化的历史记录很差。他希望有一个开放的公共工作空间，即使不在能力边缘，也能让整个行业都能使用。

**"意外地，我们其实处在一个还不错的位置。"**

---

## 物理世界 vs 数字世界 [54:44]

Karpathy 的框架：

1. **数字空间**（当前重点）：bits 可以复制粘贴，比加速原子快百万倍。会有大量 unhobbling——以前效率不高的数字信息处理会被提升 100 倍。
2. **物理-数字接口**（下一步）：传感器（看世界）和执行器（对世界做事）。很多有趣的公司会出现在这个接口上——材料科学的实验设备、生物学的传感器、为 AI 收集训练数据的人。
3. **物理世界**（最大市场但最慢）：原子比 bits 难百万倍。机器人需要大量资本投入和时间。TAM 可能比数字空间更大，但会滞后。

他预测会出现**信息市场**——agent 为了做决策（赌博市场、股票）需要实时物理世界数据，应该有机制让人类为 agent 提供传感数据并获得报酬。

---

## MicroGPT 与教育的未来 [01:01:34]

MicroGPT 是 Karpathy 十多年来"把 LLM 训练精简到本质"的最新成果：200 行 Python，包含数据集、神经网络架构（50 行前向传播）、自动微分引擎（100 行）、Adam 优化器（10 行）、训练循环。

关键转变：以前他会做视频逐行讲解。现在他意识到**不需要了**——200 行已经足够简单，任何人都可以让 agent 用各种方式解释。

他的新角色：**向 agent 解释，而非向人解释**。如果 agent 理解了，它就能做路由，针对每个人的水平和语言做无限耐心的个性化教学。

教育的未来：
- 不再是给人写 HTML 文档，而是给 agent 写 Markdown 文档
- 不再是讲座和指南，而是 skill（指导 agent 如何教授某个主题的课程脚本）
- 他的贡献是那"几个 bit"——agent 无法自己想出来的精简和本质（他试过让 agent 写 MicroGPT，写不出来）
- 其他一切——教学、解释、适配——都是 agent 的领域

**"我不再向人解释东西了。我向 agent 解释。"**
