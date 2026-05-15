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

# 用 Eval 系统化测试 Agent 技能

> 原文：[Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills)
> 来源：OpenAI Developers Blog | 2026-03-01
> 作者：OpenAI

---

## 索引

- [1. 写 skill 之前先定义成功标准](#1-写-skill-之前先定义成功标准)
- [2. 创建 skill](#2-创建-skill)
- [3. 手动触发 skill 暴露隐藏假设](#3-手动触发-skill-暴露隐藏假设)
- [4. 用小而精的 prompt 集尽早捕获回归](#4-用小而精的-prompt-集尽早捕获回归)
- [5. 从轻量级确定性 grader 开始](#5-从轻量级确定性-grader-开始)
- [6. 用 Codex 和 rubric 做定性检查](#6-用-codex-和-rubric-做定性检查)
- [7. 随 skill 成熟扩展 eval](#7-随-skill-成熟扩展-eval)
- [8. 关键要点](#8-关键要点)

---

## 1. 写 skill 之前先定义成功标准

在写 skill 本身之前，先用你能实际衡量的术语写下"成功"意味着什么。一个有用的思考方式是把检查分成几类：

- **结果目标**：任务完成了吗？应用能运行吗？
- **过程目标**：Codex 是否调用了 skill 并遵循了你预期的工具和步骤？
- **风格目标**：输出是否遵循了你要求的规范？
- **效率目标**：它是否没有反复折腾就到达了目标（例如不必要的命令或过多的 token 使用）？

保持这个列表小而聚焦于必须通过的检查。目标不是提前编码每个偏好，而是捕获你最关心的行为。

在本文中，指南评估的是一个设置 demo 应用的 skill。有些检查是具体的——它运行了 `npm install` 吗？它创建了 `package.json` 吗？指南把这些与结构化的风格 rubric 配对来评估规范和布局。这种混合是有意的。你想要的是**快速、有针对性的信号**，尽早暴露特定回归，而不是最后一个单一的通过/失败判定。

---

## 2. 创建 skill

Codex skill 是一个包含 SKILL.md 文件的目录，文件包含 YAML front matter（`name`、`description`），后面是定义 skill 行为的 Markdown 指令，以及可选的资源和脚本。

**name 和 description 比看起来更重要。** 它们是 Codex 决定是否调用 skill 的主要信号，以及何时把 SKILL.md 的其余部分注入 agent 的 context。如果这些模糊或过载，skill 就不会可靠触发。

最快的入门方式是使用 Codex 内置的 skill 创建器（它本身也是一个 skill）：

```
$skill-creator
```

创建器会问你 skill 做什么、什么时候应该触发、以及它是纯指令型还是脚本支持型（纯指令型是默认推荐）。

---

## 示例 skill

本文使用一个刻意最小化的示例：一个以可预测、可重复方式设置小型 React demo 应用的 skill。

这个 skill 会：
- 用 Vite 的 React + TypeScript 模板搭建项目
- 用官方 Vite 插件方式配置 Tailwind CSS
- 强制一个最小、一致的文件结构
- 定义清晰的"完成定义"，让成功易于评估

```yaml
---
name: setup-demo-app
description: Scaffold a Vite + React + Tailwind demo app with a small, consistent project structure.
---
```

```markdown
## When to use this
Use when you need a fresh demo app for quick UI experiments or reproductions.

## What to build
Create a Vite React TypeScript app and configure Tailwind. Keep it minimal.

## Steps
1. Scaffold with Vite: npm create vite@latest demo-app -- --template react-ts
2. Install dependencies: cd demo-app && npm install
3. Install and configure Tailwind using the Vite plugin
4. Implement the minimal UI: Header + Card components

## Definition of done
- npm run dev starts successfully
- package.json exists
- src/components/Header.tsx and src/components/Card.tsx exist
```

这个示例 skill 故意采取了有主见的立场。没有清晰的约束，就没有具体的东西可以评估。

---

## 3. 手动触发 skill 暴露隐藏假设

因为 skill 调用高度依赖 SKILL.md 中的 name 和 description，首先要检查的是 `setup-demo-app` skill 是否在你期望时触发。

早期，通过 `/skills` 斜杠命令或 `$` 前缀显式激活 skill，在真实仓库或临时目录中运行，观察它在哪里出问题。这是你暴露遗漏的地方：skill 完全不触发、触发太积极、或运行了但偏离预期步骤的情况。

在这个阶段，你不是在优化速度或打磨。你在寻找 skill 做出的**隐藏假设**：

- **触发假设**：像"set up a quick React demo"这样的 prompt 应该调用 `setup-demo-app` 但没有，或者更通用的 prompt（"add Tailwind styling"）意外触发了它。
- **环境假设**：skill 假设它在空目录中运行，或者 npm 可用且优先于其他包管理器。
- **执行假设**：agent 跳过 `npm install` 因为它假设依赖已安装，或者在 Vite 项目存在之前就配置 Tailwind。

准备好让这些运行可重复时，切换到 `codex exec`。它为自动化和 CI 设计：进度流到 stderr，只把最终结果写到 stdout，让运行更容易脚本化、捕获和检查。

```bash
codex exec --full-auto \
  'Use the $setup-demo-app skill to create the project in this directory.'
```

这第一次动手操作更多是关于**发现边界情况**而不是验证正确性。你在这里做的每个手动修复——添加缺失的 `npm install`、纠正 Tailwind 设置、收紧触发描述——都是未来 eval 的候选，这样你可以在大规模评估之前锁定预期行为。

---

## 4. 用小而精的 prompt 集尽早捕获回归

你不需要大型基准测试就能从 eval 中获得价值。对于单个 skill，**10-20 个 prompt 的小集合**就足以暴露回归并尽早确认改进。

从一个小 CSV 开始，随着开发或使用中遇到真实失败逐步增长。每行应代表一个你关心 `setup-demo-app` skill 是否应该激活的场景，以及激活时成功是什么样的。

例如，初始的 `evals/setup-demo-app.prompts.csv`：

| id | should_trigger | prompt |
|---|---|---|
| test-01 | true | Create a demo app named `devday-demo` using the $setup-demo-app skill |
| test-02 | true | Set up a minimal React demo app with Tailwind for quick UI experiments |
| test-03 | true | Create a small demo app to showcase the Responses API |
| test-04 | false | Add Tailwind styling to my existing React app |

每个用例测试的东西略有不同：

- **显式调用**（test-01）：直接命名 skill，确保直接使用不会因 skill 的 name/description/instructions 变更而中断。
- **隐式调用**（test-02）：描述 skill 目标场景但不提名字，测试 SKILL.md 中的 name 和 description 是否足够强让 Codex 自行选择。
- **上下文调用**（test-03）：添加领域上下文但仍需要相同的底层设置，检查 skill 在现实的、略有噪声的 prompt 中是否触发。
- **负面控制**（test-04）：不应调用 `setup-demo-app`。这是一个常见的相邻请求，可能意外匹配 skill 的描述。包含至少一个 `should_trigger=false` 用例有助于捕获**假阳性**。

随着你发现遗漏——未能触发 skill 的 prompt，或输出偏离预期的情况——把它们作为新行添加。随时间推移，这个小 CSV 变成 skill 必须持续正确处理的场景的活记录。

---

## 5. 从轻量级确定性 grader 开始

这是评估步骤的核心：使用 `codex exec --json`，让你的 eval harness 可以对**实际发生的事情**打分，而不仅仅是最终输出看起来是否正确。

启用 `--json` 时，stdout 变成结构化事件的 JSONL 流。这让编写与你关心的行为直接绑定的确定性检查变得简单，例如：

- 它运行了 `npm install` 吗？
- 它创建了 `package.json` 吗？
- 它是否按预期顺序调用了预期命令？

这些检查故意轻量。它们在你添加任何基于模型的评分之前，给你**快速、可解释的信号**。

---

## 最小 Node.js 运行器

一个"够用"的方法：

1. 对每个 prompt，运行 `codex exec --json --full-auto "<prompt>"`
2. 把 JSONL trace 保存到磁盘
3. 解析 trace 并对事件运行确定性检查

```javascript
// evals/run-setup-demo-app-evals.mjs
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import path from "node:path";

function runCodex(prompt, outJsonlPath) {
  const res = spawnSync("codex", [
    "exec", "--json", "--full-auto", prompt,
  ], { encoding: "utf8" });
  mkdirSync(path.dirname(outJsonlPath), { recursive: true });
  writeFileSync(outJsonlPath, res.stdout, "utf8");
  return { exitCode: res.status ?? 1, stderr: res.stderr };
}

function parseJsonl(jsonlText) {
  return jsonlText.split("\n").filter(Boolean).map((line) => JSON.parse(line));
}

// 确定性检查：agent 是否运行了 npm install？
function checkRanNpmInstall(events) {
  return events.some(
    (e) => (e.type === "item.started" || e.type === "item.completed")
      && e.item?.type === "command_execution"
      && typeof e.item?.command === "string"
      && e.item.command.includes("npm install")
  );
}

// 确定性检查：package.json 是否被创建？
function checkPackageJsonExists(projectDir) {
  return existsSync(path.join(projectDir, "package.json"));
}
```

这里的价值在于一切都是**确定性的、可调试的**。如果检查失败，你可以打开 JSONL 文件看到确切发生了什么。每个命令执行都按顺序作为 `item.*` 事件出现。这让回归容易解释和修复。

---

## 6. 用 Codex 和 rubric 做定性检查

确定性检查回答"它做了基本的事吗？"但不回答"它是按你想要的方式做的吗？"

对于像 `setup-demo-app` 这样的 skill，很多要求是定性的：组件结构、样式规范、Tailwind 是否按预期配置。这些很难仅用文件存在检查或命令计数来捕获。

一个务实的解决方案是在 eval 管道中添加第二个**模型辅助步骤**：

1. 运行 setup skill（写代码到磁盘）
2. 对结果仓库运行只读的风格检查
3. 要求结构化响应，让 harness 可以一致地打分

Codex 通过 `--output-schema` 直接支持这一点，它把最终响应约束为你定义的 JSON Schema。

### 小型 rubric schema

```json
{
  "type": "object",
  "properties": {
    "overall_pass": { "type": "boolean" },
    "score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "pass": { "type": "boolean" },
          "notes": { "type": "string" }
        },
        "required": ["id", "pass", "notes"]
      }
    }
  },
  "required": ["overall_pass", "score", "checks"]
}
```

### 风格检查 prompt

```bash
codex exec \
  "Evaluate the demo-app repository against these requirements:
  - Vite + React + TypeScript project exists
  - Tailwind is configured via @tailwindcss/vite and CSS imports tailwindcss
  - src/components contains Header.tsx and Card.tsx
  - Components are functional and styled with Tailwind utility classes
  Return a rubric result as JSON with check ids: vite, tailwind, structure, style." \
  --output-schema ./evals/style-rubric.schema.json \
  -o ./evals/artifacts/test-01.style.json
```

`--output-schema` 的好处是：你得到的不是难以解析或比较的自由文本，而是一个可预测的 JSON 对象，eval harness 可以跨多次运行打分。

---

## 7. 随 skill 成熟扩展 eval

核心循环就位后，你可以在对 skill 最重要的方向上扩展 eval。从小处开始，只在真正增加信心的地方加入更深的检查：

- **命令计数和折腾**：计算 JSONL trace 中的 `command_execution` 项，捕获 agent 开始循环或重复运行命令的回归。
- **Token 预算**：跟踪 `usage.input_tokens` 和 `usage.output_tokens`，发现意外的 prompt 膨胀，跨版本比较效率。
- **构建检查**：skill 完成后运行 `npm run build`，作为更强的端到端信号，捕获损坏的导入或错误配置的工具。
- **运行时冒烟检查**：启动 `npm run dev` 并用 curl 访问开发服务器，或运行轻量级 Playwright 检查。选择性使用——增加信心但耗时。
- **仓库清洁度**：确保运行不生成不需要的文件，`git status --porcelain` 为空（或匹配显式允许列表）。
- **沙箱和权限回归**：验证 skill 仍然可以在不超出预期权限的情况下工作。

模式是一致的：**从解释行为的快速检查开始，只在减少风险时才添加更慢、更重的检查。**

---

## 8. 关键要点

这个小型 `setup-demo-app` 示例展示了从"感觉更好了"到"有证据"的转变：运行 agent，记录发生了什么，用一小组检查来评分。

一旦这个循环存在，每次调整都更容易确认，每次回归都变得清晰。

关键要点：

- **衡量重要的东西。** 好的 eval 让回归清晰、失败可解释。
- **从可检查的完成定义开始。** 用 `$skill-creator` 引导，然后收紧指令直到成功是明确的。
- **基于行为做 eval。** 用 `codex exec --json` 捕获 JSONL，对 `command_execution` 事件写确定性检查。
- **规则不够时用 Codex。** 用 `--output-schema` 添加结构化的、基于 rubric 的评分来可靠地评判风格和规范。
- **让真实失败驱动覆盖。** 每个手动修复都是信号。把它变成测试，让 skill 持续做对。
