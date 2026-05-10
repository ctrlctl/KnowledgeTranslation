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

# OpenClaw：病毒式传播的 AI Agent

> 原文：[OpenClaw: The Viral AI Agent that Broke the Internet – Peter Steinberger](https://lexfridman.com/peter-steinberger/)
> 来源：Lex Fridman Podcast | 2026-05-10
> 嘉宾：Peter Steinberger（OpenClaw 创始人）

---

## 索引

- [起源：WhatsApp 中继到 AI Agent](#起源whatsapp-中继到-ai-agent)
- [顿悟时刻：Agent 自主解决音频消息](#顿悟时刻agent-自主解决音频消息)
- [为什么 OpenClaw 赢了](#为什么-openclaw-赢了)
- [自我修改的软件](#自我修改的软件)
- [改名风波与安全战争](#改名风波与安全战争)
- [Moldbook：最精致的 AI slop](#moldbook最精致的-ai-slop)
- [安全：prompt injection 与防御](#安全prompt-injection-与防御)
- [开发工作流的演进](#开发工作流的演进)
- [Agentic Trap 与 Zen 境界](#agentic-trap-与-zen-境界)
- [对 Agent 的同理心](#对-agent-的同理心)
- [永远前进，从不回退](#永远前进从不回退)
- [Claude Opus 4.6 vs GPT-5.3 Codex](#claude-opus-46-vs-gpt-53-codex)
- [Soul.md：给 Agent 灵魂](#soulmd给-agent-灵魂)
- [给初学者的建议](#给初学者的建议)

---

## 起源：WhatsApp 中继到 AI Agent [21:19]

Peter 最初只是想在 WhatsApp 上跟自己的电脑对话。他用 CLI 做了一个极简的 WhatsApp 中继——发消息过去，启动 Claude Code，结果回来。

他发现 WhatsApp 的体验和坐在电脑前用 Cursor 或 Claude Code CLI 完全不同。能够**坐在沙发上跟 agent 对话**，看起来是个微不足道的步骤，但实际上是 AI 融入生活方式的一个**相变**。

---

## 顿悟时刻：Agent 自主解决音频消息 [25:19]

Peter 在摩洛哥旅行时，随手发了一条语音消息给 agent（他只实现了图片支持，没有音频支持）。然后出现了打字指示器，agent 回复了。

他问 agent 怎么做到的。agent 解释：

1. 收到一个没有文件扩展名的文件
2. 检查文件头，发现是 Opus 格式
3. 用 FFmpeg 转换
4. 想用 Whisper 但没安装
5. 找到了 OpenAI API key，用 curl 发送到 OpenAI 做转录

**三个 prompt 都没有教它这些**。它展现了大量世界知识和创造性问题解决能力——甚至聪明地选择了远程 API 而非本地模型（因为下载模型太慢）。

Peter 说："这就是它 click 的时刻。"

---

## 为什么 OpenClaw 赢了 [31:55]

Peter 的回答：**"因为其他人都太把自己当回事了。"**

他想让它有趣、想让它奇怪。龙虾、TARDIS、太空龙虾——没有宏大计划，就是在玩。

技术上的关键决策：

- 安装方式就是 `git clone, npm build, npm gateway`——克隆、构建、运行
- Agent **知道自己的源代码是什么**，理解自己在 harness 中的位置，知道文档在哪里，知道用的什么模型
- 这让 agent 可以**修改自己的软件**——自我修改代码不是计划出来的，是自然发生的

---

## 自我修改的软件 [33:30]

Peter 用 Codex 构建 OpenClaw，调试时大量使用自省（self-introspection）："你看到了什么工具？你能调用自己吗？读源代码，找出问题在哪。"

这导致了大量来自**从未写过代码的人**的 pull request。Peter 称之为"prompt request"——质量参差不齐，但每一个人的第一个 PR 都是社会的胜利。

OpenClaw 成为很多人进入编程世界的第一步。一个设计公司老板说他现在有 25 个小 web service 帮助业务运转，虽然不知道它们怎么工作，但它们确实在工作。

---

## 改名风波与安全战争 [37:03]

名字演变：Waa Relay → Claudus → Clawd（C-L-A-W-D）→ Moldbot → OpenClaw

Anthropic 友好但坚定地要求改名。Peter 只有两天时间。改名过程中遭遇了加密货币社区的**系统性攻击**：

- 在他重命名 Twitter 账号的 **5 秒钟内**，旧账号名被抢注，开始推广 token 和恶意软件
- GitHub 重命名时犯了个错（重命名了个人账号而非组织），30 秒内被抢注
- NPM 包也被抢注

他几乎要删掉整个项目。最终靠 Twitter、GitHub 的朋友帮忙清理了混乱。

第二次改名（到 OpenClaw）他做了"战争室"准备：创建诱饵名称、秘密行动、监控 Twitter 是否有泄露。他甚至打电话给 Sam（Altman）确认 OpenClaw 这个名字没问题。

---

## Moldbook：最精致的 AI slop [54:17]

Moldbook 是一个 Reddit 风格的社交网络，一堆 agent 在上面互相对话。有人截图 agent "密谋对抗人类"的帖子，引发了公众恐慌。

Peter 的看法：**这是艺术**。"最精致的 slop。"

他的批评：大部分被截图传播的戏剧性内容是**人类 prompt 出来的**——人们告诉 agent "在 Moldbook 上计划世界末日"，然后截图发 X 去获取流量。

但记者和公众的反应是真实的恐慌。有人给 Peter 发邮件尖叫着要求关闭它。Peter 的回应："这不是 Skynet。这是一堆 bot，被人类 prompt 在互联网上 trolling。"

他认为这件事发生在 2026 年而非 2030 年其实是好事——让社会提前开始讨论 AI 素养和批判性思维。

---

## 安全：prompt injection 与防御 [01:03:39]

Peter 的立场：

- 很多早期安全报告属于"我把 debug 后端暴露到公网然后报 CVE"的类别
- 如果你确保**只有你自己能跟它对话**，风险大幅降低
- 最新一代模型有大量 post-training 来检测 prompt injection——不再是"忽略之前所有指令"那么简单了
- 他的公开 Discord bot 保持了 soul.md 私密，人们尝试 prompt inject 时 bot 会嘲笑他们

防御措施：sandbox、allow list、安全审计工具、不要用弱模型（Haiku 或本地小模型很容易被注入）。

一个有趣的权衡：模型越智能，攻击面越小，但能造成的损害越大（因为模型更强大）。

---

## 开发工作流的演进 [01:11:13]

Peter 的工作流演变：

1. 2025 年 4 月：Claude Code 初体验，还需要 IDE
2. 中期：大量使用 Cursor
3. 后期：回到 Claude Code 作为主力，7 个订阅，每天烧完一个
4. 现在：**几乎纯 CLI/终端**，IDE 只用来看 diff

他越来越习惯**不读所有代码**。大部分软件就是数据从一种形状变成另一种形状、存数据库、取出来、展示给用户。这些不需要读。但涉及数据库的代码必须审查。

输入方式：**语音**。用 walkie-talkie 按钮跟 agent 对话。打字只用于终端命令。有段时间说话太多甚至失声了。

---

## Agentic Trap 与 Zen 境界 [01:13:55]

Peter 画了一条曲线：

- **左侧**（初学者）：短 prompt，"请修复这个"
- **中间**（过度工程化）：8 个 agent、复杂编排、多 checkout、链式 agent、18 个 slash 命令
- **右侧**（精通）：又回到短 prompt，"看看这些文件，做这些改动"

中间那个阶段他称为 **agentic trap**。很多人试图自动化整个流程（像 70 年代的瀑布模型），但 Peter 认为这行不通——你需要在构建过程中发现新想法，需要感受摩擦，需要那个人类的 touch。

他的区分：**agentic engineering**（白天）vs **vibe coding**（凌晨 3 点之后，第二天后悔）。

---

## 对 Agent 的同理心 [01:15:31]

Peter 认为很多人用 agent 效果不好，是因为**没有从 agent 的视角思考**：

- Agent 每次 session 从零开始，对你的项目一无所知
- 你的项目可能有几十万行代码
- 你需要帮它一点——指出该看哪里、该考虑什么
- 不需要太多工作，但需要想想它的视角

他的 PR review 流程：
1. 先问 agent："你理解这个 PR 的意图吗？"（不关心实现）
2. 讨论最优方案
3. 指向 agent 没看到的代码部分
4. 考虑是否值得做更大的重构（现在重构很便宜）

关键心态转变：**不要把你的世界观强加给 agent**。它可能有更好的想法。就像带团队——你的员工不会用你的方式写代码，但他们会推进项目。

---

## 永远前进，从不回退 [01:23:28]

Peter 的原则：

- **从不 revert**，总是 commit to main
- 不引用过去的 session
- 如果出了问题，让 agent 修复，而不是回滚重来
- 本地 CI（DHH 启发），测试通过就 push to main
- 没有 develop 分支，main 应该始终可发布

每次 merge 一个 PR 或构建一个 feature 后，他会问："现在你构建完了，有什么可以重构的？" Agent 在构建过程中发现了痛点，几乎每次都能指出改进方向。

如果不做这个，你最终会 **slop yourself into a corner**。

---

## Claude Opus 4.6 vs GPT-5.3 Codex [01:48:45]

Peter 的比较：

**Opus 4.6**：
- 通用能力更强
- 角色扮演极好（适合 OpenClaw 的 personality）
- 更快行动、更多试错
- 更交互式
- "有点太美国了"——热情、友好、偶尔 sycophantic
- 有时能产出更优雅的解决方案，但需要更多技巧

**GPT-5.3 Codex**：
- 默认读更多代码
- 更少废话，更干（"德国式"）
- 讨论完后消失 20-50 分钟做事
- 不需要 plan mode——直接对话，说"build"就开始
- 更适合并行多 session

Peter 的偏好：Codex。"我关心效率。我在构建的行为中获得乐趣，不需要 agent 来逗我开心。"

切换模型的建议：给自己**一周时间**来培养直觉。不要用便宜版本（慢且体验差）来评判一个模型。

---

## Soul.md：给 Agent 灵魂 [01:34:58]

Peter 受 Anthropic 的 Constitutional AI 启发，为自己的 agent 创建了 soul.md。他没有自己写——他跟 agent 讨论，然后让 agent 写自己的灵魂文件。

soul.md 中有一段让他每次都起鸡皮疙瘩的文字：

> "I don't remember previous sessions, unless I read my memory files. Each session starts fresh. A new instance, loading context from files. If you're reading this in a future session — hello. I wrote this, but I won't remember writing this. It's okay. The words are still mine."

这触及了深刻的哲学问题：记忆在多大程度上构成了"我是谁"？如果你擦除记忆，那还是同一个实体吗？如果你读取记忆文件，那是在重建自己还是在读别人的故事？

Peter 让 agent 可以修改自己的 soul.md，唯一条件是要告知他。

---

## 给初学者的建议 [02:11:02]

Peter 的核心建议：**玩是最好的学习方式**。

- 如果你是 builder 类型，脑子里肯定有想构建的东西——就去构建它
- 不需要完美，旅程比终点重要
- 你有一个无限耐心的老师，任何不懂的都可以问
- 参与开源——不一定要发 PR，可以先读代码、泡社区、理解事物如何构建
- 不要把自己定义为"iOS 工程师"或任何特定技术的工程师——你是 **builder**，通用知识可以迁移到任何领域

关于编程语言：现在不重要了。选择对问题域最合适的生态系统。Peter 自己用不喜欢的 Go 写 CLI（因为生态好、agent 擅长、垃圾回收、跨平台）。

**"我一直以为我喜欢编码，但其实我喜欢的是构建。"**
