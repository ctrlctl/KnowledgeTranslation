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

# Quantifying Infrastructure Noise in Agentic Coding Evals：量化 Agentic 编码评估中的基础设施噪声

> 原文：[Quantifying Infrastructure Noise in Agentic Coding Evals](https://www.anthropic.com/engineering/infrastructure-noise)
> 来源：Anthropic Engineering | 2026-02-05
> 作者：Anthropic

---

## 核心发现

基础设施配置可以使 agentic 编码基准测试波动数个百分点——有时超过排行榜上顶级模型之间的差距。

在内部实验中，Terminal-Bench 2.0 上资源最多和最少的配置之间差距为 **6 个百分点**（p < 0.01）。

---

## 为什么 Agentic 评估不同于静态评估

**静态基准测试**直接评分模型输出——运行时环境不影响结果。

**Agentic 编码评估**不同：模型被给予完整环境，在其中编写程序、运行测试、安装依赖、多轮迭代。运行时不再是被动容器，而是问题解决过程的组成部分。**两个资源预算和时间限制不同的 agent 不是在做同一份考试。**

---

## 关键变量

- **CPU 和 RAM：** 更多资源 = 更快的编译和测试 = 更多迭代机会
- **时间限制：** 更长的超时让 agent 可以尝试更多策略
- **网络访问：** 能否安装额外依赖影响解题策略
- **磁盘 I/O：** 影响大型项目的构建速度

---

## 启示

1. **排行榜分数需要谨慎解读**——几个百分点的差距可能完全由基础设施差异解释
2. **评估需要标准化基础设施**——不仅指定资源，还要强制执行
3. **强制方法论本身会改变基准测试实际测量的内容**
4. **报告评估结果时应包含基础设施配置细节**
