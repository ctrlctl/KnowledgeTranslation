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

> 原文：[Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler)
> 来源：Anthropic Engineering | 2026-02-05
> 作者：Nicholas Carlini

## 索引

- [概述](#概述)
- [让 Claude 持续运行](#让-claude-持续运行)
- [并行运行 Claude](#并行运行-claude)
- [经验教训](#经验教训)
- [评估结果](#评估结果)
- [展望](#展望)

---

## 概述

作者用 16 个并行 agent 从零开始编写一个基于 Rust 的 C 编译器，能够编译 Linux 内核。经过近 2,000 次 Claude Code 会话和 $20,000 的 API 成本，agent 团队产出了一个 10 万行的编译器，可以在 x86、ARM 和 RISC-V 上构建 Linux 6.9。

编译器本身是有趣的产物，但文章重点在于**为长时间运行的自主 agent 团队设计 harness** 的经验：如何编写让 agent 在无人监督下保持正轨的测试，如何组织工作使多个 agent 能并行推进，以及这种方法的天花板在哪里。

---

## 让 Claude 持续运行

现有的 agent 脚手架（如 Claude Code）需要操作者在线协作。如果你要求解决一个长而复杂的问题，模型可能解决一部分就停下来等待输入。

为了引出持续、自主的进展，作者构建了一个简单循环的 harness：

```bash
#!/bin/bash
while true; do
  COMMIT=$(git rev-parse --short=6 HEAD)
  LOGFILE="agent_logs/agent_${COMMIT}.log"
  claude --dangerously-skip-permissions \
    -p "$(cat AGENT_PROMPT.md)" \
    --model claude-opus-X-Y &> "$LOGFILE"
done
```

在 agent prompt 中，告诉 Claude 要解决什么问题，要求它把问题拆成小块、跟踪进度、找出下一步该做什么，并持续工作直到完美。

---

## 并行运行 Claude

并行运行多个实例解决单 agent harness 的两个弱点：

1. 单个 Claude Code 会话一次只能做一件事，调试多个问题时并行更高效
2. 多个 agent 允许**专业化分工**——一些解决实际问题，其他维护文档、监控代码质量或解决专门子任务

实现方式很简单：创建一个裸 git repo，为每个 agent 启动一个 Docker 容器。每个 agent 克隆本地副本到 `/workspace`，完成后推送到 upstream。

**同步算法**防止两个 agent 同时解决同一问题：

- Claude 通过写文本文件到 `current_tasks/` 来"锁定"任务
- 如果两个 agent 尝试认领同一任务，git 的同步机制强制第二个 agent 选择不同的任务
- 完成后 pull、merge、push、移除锁

没有使用编排 agent，每个 Claude agent 自行决定如何行动，通常选择"下一个最明显的"问题。

---

## 经验教训

### 编写极高质量的测试

Claude 会自主解决你给它的任何问题，所以**任务验证器必须近乎完美**，否则 Claude 会解决错误的问题。需要找到高质量的编译器测试套件、编写验证器和构建脚本、观察 Claude 犯的错误然后设计新测试。

后期 Claude 开始频繁在实现新功能时破坏现有功能，于是构建了 CI 流水线和更严格的执行机制。

### 站在 Claude 的角度思考

为 Claude 而非自己编写测试 harness，需要重新思考很多假设：

- **上下文窗口污染**：测试 harness 不应打印数千字节无用输出。最多打印几行，重要信息记录到文件。日志应易于自动处理：有错误时写 ERROR 并把原因放在同一行。预计算聚合统计。
- **时间盲**：Claude 无法感知时间，会愉快地花几小时运行测试。Harness 不频繁打印增量进度，包含默认 `--fast` 选项运行 1% 或 10% 随机样本。

### 让并行变容易

当有许多不同的失败测试时，并行化很简单：每个 agent 选择不同的失败测试。

但编译 Linux 内核时卡住了——这是一个巨大的单一任务，每个 agent 都会遇到同一个 bug。解决方案是用 GCC 作为**在线已知正确的编译器 oracle** 来对比：随机用 GCC 编译大部分内核，只用 Claude 的编译器编译剩余文件。如果内核工作，问题不在 Claude 的子集中；如果崩溃，进一步细化。这让每个 agent 并行修复不同文件中的不同 bug。

### 多种 agent 角色

并行也支持专业化：一个 agent 合并重复代码，一个改进编译器性能，一个负责输出高效编译代码，一个从 Rust 开发者角度批评设计，一个负责文档。

---

## 评估结果

经过近两周的 2,000 次 Claude Code 会话，Opus 4.6 消耗了 20 亿输入 token 和 1.4 亿输出 token，总成本略低于 $20,000。

这是一个洁净室实现（Claude 在开发期间没有互联网访问），仅依赖 Rust 标准库。10 万行编译器可以：

- 在 x86、ARM 和 RISC-V 上构建可启动的 Linux 6.9
- 编译 QEMU、FFmpeg、SQLite、PostgreSQL、Redis
- 在大多数编译器测试套件（包括 GCC torture test suite）上达到 99% 通过率
- 编译并运行 Doom

**局限性**：

- 缺少 16 位 x86 编译器（启动 Linux 出 real mode 需要），这部分调用 GCC
- 没有自己的汇编器和链接器
- 不是所有项目都能成功构建
- 生成的代码效率不高（全优化开启仍不如 GCC 全优化关闭）
- Rust 代码质量合理但远非专家水平

---

## 展望

每一代语言模型都开启了新的工作方式。Agent 团队展示了**自主实现整个复杂项目**的可能性。

但完全自主开发伴随真实风险。当人类与 Claude 一起开发时，可以确保一致的质量并实时捕获错误。对于自主系统，看到测试通过就假设工作完成很容易，但这很少是事实。

作者坦言这个实验既令人兴奋又令人不安——没有预料到这在 2026 年初就接近可能。语言模型和交互脚手架的快速进步打开了编写大量新代码的大门，需要新策略来安全导航。
