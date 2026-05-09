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

# Code Execution with MCP：用 MCP 实现代码执行，构建更高效的 Agent

> 原文：[Code execution with MCP: Building more efficient agents](https://www.anthropic.com/engineering/code-execution-with-mcp)
> 来源：Anthropic Engineering | 2025-11-04
> 作者：Anthropic

---

## 目录

- [问题：工具过多导致 token 消耗过大](#问题工具过多导致-token-消耗过大)
- [两个效率瓶颈](#两个效率瓶颈)
- [解决方案：代码执行代替直接工具调用](#解决方案代码执行代替直接工具调用)
- [工作原理](#工作原理)
- [优势](#优势)

---

## 问题：工具过多导致 token 消耗过大

MCP（Model Context Protocol）是连接 AI agent 到外部系统的开放标准。自 2024 年 11 月推出以来，社区已构建数千个 MCP server，SDK 覆盖所有主要编程语言。

今天开发者常规构建可访问数百甚至数千个工具的 agent。然而，随着连接工具数量增长，预先加载所有工具定义并通过上下文窗口传递中间结果会拖慢 agent 并增加成本。

---

## 两个效率瓶颈

### 1. 工具定义过载上下文窗口

大多数 MCP 客户端预先将所有工具定义直接加载到上下文中。当 agent 连接到数千个工具时，需要在读取请求之前处理数十万 token 的工具描述。

### 2. 中间工具结果消耗额外 token

大多数 MCP 客户端让模型直接调用 MCP 工具。每次工具调用的完整结果都回到上下文窗口。

例如，"从 Google Drive 下载会议记录并附加到 Salesforce lead"这个任务：
- 模型调用 `gdrive.getDocument` → 完整文档内容进入上下文
- 模型调用 `salesforce.updateRecord` → 又一次完整响应进入上下文

文档内容可能有数千 token，但 agent 真正需要的只是将内容从 A 传到 B。

---

## 解决方案：代码执行代替直接工具调用

与其让 agent 直接调用工具（每次调用的定义和结果都占用上下文），不如让 agent **编写代码来调用工具**。

Agent 不再一个个调用工具并将结果传回上下文，而是编写一段脚本，在沙箱中执行多个工具调用，只将最终结果返回上下文。

---

## 工作原理

1. Agent 接收用户请求
2. Agent 编写代码（如 Python/TypeScript），代码中调用 MCP 工具
3. 代码在沙箱中执行，直接在工具之间传递数据
4. 只有最终结果（或摘要）返回到 agent 的上下文

```python
# Agent 生成的代码示例
doc = mcp.gdrive.getDocument(documentId="abc123")
mcp.salesforce.updateRecord(
    objectType="Lead",
    recordId="xyz789",
    data={"meeting_notes": doc.body}
)
return {"status": "success", "doc_title": doc.title}
```

中间的完整文档内容从未进入 agent 的上下文窗口。

---

## 优势

1. **减少 token 消耗：** 中间结果在代码执行环境中流转，不回到上下文
2. **减少工具定义负担：** Agent 不需要预先加载所有工具定义，可以通过代码动态发现和调用
3. **更好的扩展性：** 可以处理更多工具而不降低性能
4. **更自然的编排：** 代码天然支持条件逻辑、循环、错误处理——比顺序工具调用更灵活

**核心洞察：** 直接工具调用是 agent 与工具交互的最简单模式，但不是最高效的。当工具数量增长时，让 agent 编写代码来编排工具调用，可以显著减少 token 消耗并提高效率。
