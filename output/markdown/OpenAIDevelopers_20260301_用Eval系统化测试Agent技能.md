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

# Testing Agent Skills Systematically with Evals：用 Eval 系统化测试 Agent 技能

> 原文：[Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills)
> 来源：OpenAI Developers Blog | 2026-03-01
> 作者：OpenAI

---

## 核心思想

Agent 的 skill（技能）是可以独立测试和改进的能力单元。系统化的 eval 让你能够：

- 隔离和测量每个 skill 的性能
- 识别哪些 skill 是瓶颈
- 在不影响其他 skill 的情况下改进特定 skill
- 跟踪 skill 随时间的性能变化

---

## Skill 评估框架

### 定义 Skill

每个 skill 对应 agent 的一个具体能力：文件编辑、代码搜索、测试运行、git 操作等。

### 为每个 Skill 创建评估集

- 收集真实世界的使用案例
- 定义成功标准（可以是确定性检查或 LLM 判断）
- 包含边缘情况和失败模式

### 运行和分析

- 独立运行每个 skill 的评估
- 追踪通过率、延迟、token 消耗
- 识别回归和改进机会

---

## 实践模式

1. **Skill 隔离测试：** 单独测试每个 skill，不依赖其他 skill 的正确性
2. **组合测试：** 测试 skill 之间的交互——一个 skill 的输出作为另一个的输入
3. **压力测试：** 在极端条件下测试——大文件、复杂代码库、模糊指令
4. **回归套件：** 每次更改后运行，确保没有破坏已有功能

---

## 与 Prompt/Tool 优化的关系

Eval 结果直接指导优化方向：
- Skill 通过率低 → 改进该 skill 的 prompt 或工具描述
- Skill 延迟高 → 优化工具实现或减少不必要的调用
- Skill 间交互失败 → 改进 handoff 逻辑或上下文传递
