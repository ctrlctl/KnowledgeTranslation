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
> 作者：Adam Jones, Conor Kelly

---

## 目录

- [工具过多让 agent 变慢](#工具过多让-agent-变慢)
- [瓶颈一：工具定义塞满上下文窗口](#瓶颈一工具定义塞满上下文窗口)
- [瓶颈二：中间结果消耗额外 token](#瓶颈二中间结果消耗额外-token)
- [解决方案：用代码执行代替直接工具调用](#解决方案用代码执行代替直接工具调用)
- [代码执行的优势](#代码执行的优势)
- [总结](#总结)

---

## 工具过多让 agent 变慢

[MCP（Model Context Protocol）](https://modelcontextprotocol.io/) 是连接 AI agent 到外部系统的开放标准。传统做法是为每对 agent-工具写一个定制集成，造成碎片化和重复劳动，难以扩展。MCP 提供了一个通用协议——开发者只需在 agent 中实现一次 MCP，就能解锁整个集成生态。

自 2024 年 11 月推出以来，社区已构建数千个 MCP server，SDK 覆盖所有主要编程语言，行业已将 MCP 作为连接 agent 与工具/数据的事实标准。

今天开发者常规构建可访问数百甚至数千个工具的 agent。然而，随着连接工具数量增长，**预先加载所有工具定义并通过上下文窗口传递中间结果**会拖慢 agent 并增加成本。

---

## 瓶颈一：工具定义塞满上下文窗口

大多数 MCP 客户端预先将所有工具定义直接加载到上下文中，用直接工具调用语法暴露给模型。这些工具定义长这样：

```
gdrive.getDocument
     Description: Retrieves a document from Google Drive
     Parameters:
                documentId (required, string): The ID of the document to retrieve
                fields (optional, string): Specific fields to return
     Returns: Document object with title, body content, metadata, permissions, etc.
```

```
salesforce.updateRecord
    Description: Updates a record in Salesforce
    Parameters:
               objectType (required, string): Type of Salesforce object (Lead, Contact, Account, etc.)
               recordId (required, string): The ID of the record to update
               data (required, object): Fields to update with their new values
     Returns: Updated record object with confirmation
```

工具描述占据越来越多的上下文窗口空间，增加响应时间和成本。当 agent 连接到数千个工具时，它需要在读取用户请求之前先处理**数十万 token 的工具描述**。

---

## 瓶颈二：中间结果消耗额外 token

大多数 MCP 客户端让模型直接调用 MCP 工具。比如你让 agent："从 Google Drive 下载我的会议记录，附加到 Salesforce lead 上。"

模型会这样调用：

```
TOOL CALL: gdrive.getDocument(documentId: "abc123")
        → returns "Discussed Q4 goals...\n[full transcript text]"
           (loaded into model context)

TOOL CALL: salesforce.updateRecord(
            objectType: "SalesMeeting",
            recordId: "00Q5f000001abcXYZ",
            data: { "Notes": "Discussed Q4 goals...\n[full transcript text written out]" }
        )
        (model needs to write entire transcript into context again)
```

每个中间结果都必须经过模型。在这个例子中，完整的会议记录流经上下文**两次**。一个 2 小时的销售会议，可能意味着额外处理 50,000 token。更大的文档甚至可能超出上下文窗口限制，直接打断工作流。

处理大文档或复杂数据结构时，模型在工具调用之间复制数据也更容易出错。

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/9ecf165020005c09a22a9472cee6309555485619-1920x1080.png)

*MCP 客户端将工具定义加载到模型的上下文窗口中，并编排一个消息循环——每次工具调用和结果都在操作之间经过模型。*

---

## 解决方案：用代码执行代替直接工具调用

随着代码执行环境在 agent 中越来越普遍，一个解决方案是：**将 MCP server 呈现为代码 API 而非直接工具调用**。Agent 编写代码来与 MCP server 交互。这同时解决了两个问题：agent 可以只加载需要的工具，并在执行环境中处理数据后再将结果传回模型。

一种实现方式是从连接的 MCP server 生成一个文件树，包含所有可用工具。用 TypeScript 实现：

```
servers
├── google-drive
│   ├── getDocument.ts
│   ├── ... (other tools)
│   └── index.ts
├── salesforce
│   ├── updateRecord.ts
│   ├── ... (other tools)
│   └── index.ts
└── ... (other servers)
```

每个工具对应一个文件：

```typescript
// ./servers/google-drive/getDocument.ts
import { callMCPTool } from "../../../client.js";

interface GetDocumentInput {
  documentId: string;
}

interface GetDocumentResponse {
  content: string;
}

/* Read a document from Google Drive */
export async function getDocument(input: GetDocumentInput): Promise<GetDocumentResponse> {
  return callMCPTool<GetDocumentResponse>('google_drive__get_document', input);
}
```

前面的 Google Drive → Salesforce 例子变成这样的代码：

```typescript
// Read transcript from Google Docs and add to Salesforce prospect
import * as gdrive from './servers/google-drive';
import * as salesforce from './servers/salesforce';

const transcript = (await gdrive.getDocument({ documentId: 'abc123' })).content;
await salesforce.updateRecord({
  objectType: 'SalesMeeting',
  recordId: '00Q5f000001abcXYZ',
  data: { Notes: transcript }
});
```

Agent 通过浏览文件系统来发现工具：列出 `./servers/` 目录找到可用 server（如 `google-drive` 和 `salesforce`），然后读取它需要的具体工具文件（如 `getDocument.ts` 和 `updateRecord.ts`）来理解每个工具的接口。这让 agent 只加载当前任务需要的定义。**token 使用量从 150,000 降到 2,000——节省 98.7% 的时间和成本。**

Cloudflare [发布了类似发现](https://blog.cloudflare.com/code-mode/)，将 MCP 代码执行称为"Code Mode"。核心洞察相同：LLM 擅长写代码，开发者应该利用这个优势来构建更高效地与 MCP server 交互的 agent。

---

## 代码执行的优势

代码执行让 agent 能按需加载工具、在数据到达模型之前过滤数据、在单步中执行复杂逻辑。此外还有安全和状态管理方面的好处。

### 渐进式披露（Progressive Disclosure）

模型擅长浏览文件系统。将工具呈现为文件系统上的代码，让模型可以**按需读取**工具定义，而非预先全部加载。

另一种方式是在 server 上添加一个 `search_tools` 工具来查找相关定义。比如使用上面的 Salesforce server 时，agent 搜索"salesforce"，只加载当前任务需要的工具。在 `search_tools` 中加入 detail level 参数（如仅名称、名称+描述、完整定义含 schema），也能帮助 agent 节省上下文并高效找到工具。

### 上下文高效的工具结果

处理大数据集时，agent 可以在代码中过滤和转换结果后再返回。考虑获取一个 10,000 行的电子表格：

```typescript
// 不用代码执行 - 所有行流经上下文
TOOL CALL: gdrive.getSheet(sheetId: 'abc123')
        → returns 10,000 rows in context to filter manually

// 用代码执行 - 在执行环境中过滤
const allRows = await gdrive.getSheet({ sheetId: 'abc123' });
const pendingOrders = allRows.filter(row => 
  row["Status"] === 'pending'
);
console.log(`Found ${pendingOrders.length} pending orders`);
console.log(pendingOrders.slice(0, 5)); // Only log first 5 for review
```

Agent 看到 5 行而非 10,000 行。类似模式适用于聚合、跨数据源 join、提取特定字段——都不会撑爆上下文窗口。

### 更强大且上下文高效的控制流

循环、条件、错误处理可以用熟悉的代码模式完成，而非链式串联单个工具调用。比如你需要等待 Slack 中的部署通知，agent 可以写：

```typescript
let found = false;
while (!found) {
  const messages = await slack.getChannelHistory({ channel: 'C123456' });
  found = messages.some(m => m.text.includes('deployment complete'));
  if (!found) await new Promise(r => setTimeout(r, 5000));
}
console.log('Deployment notification received');
```

这比在 agent 循环中交替执行 MCP 工具调用和 sleep 命令高效得多。

此外，能写出一棵条件树让代码执行环境去跑，也节省了"time to first token"延迟：不用等模型来评估 if 语句，让代码执行环境来做。

### 隐私保护操作

当 agent 使用代码执行与 MCP 交互时，中间结果**默认留在执行环境中**。Agent 只看到你显式 log 或 return 的内容，意味着你不想分享给模型的数据可以在工作流中流转而永远不进入模型的上下文。

对于更敏感的工作负载，agent harness 可以自动对敏感数据做 tokenization。比如你需要从电子表格导入客户联系信息到 Salesforce。Agent 写：

```typescript
const sheet = await gdrive.getSheet({ sheetId: 'abc123' });
for (const row of sheet.rows) {
  await salesforce.updateRecord({
    objectType: 'Lead',
    recordId: row.salesforceId,
    data: { 
      Email: row.email,
      Phone: row.phone,
      Name: row.name
    }
  });
}
console.log(`Updated ${sheet.rows.length} leads`);
```

MCP 客户端拦截数据，在到达模型之前对 PII 做 tokenization：

```typescript
// What the agent would see, if it logged the sheet.rows:
[
  { salesforceId: '00Q...', email: '[EMAIL_1]', phone: '[PHONE_1]', name: '[NAME_1]' },
  { salesforceId: '00Q...', email: '[EMAIL_2]', phone: '[PHONE_2]', name: '[NAME_2]' },
  ...
]
```

当数据在另一个 MCP 工具调用中被使用时，MCP 客户端通过查找表将其还原。真实的邮箱、电话、姓名从 Google Sheets 流向 Salesforce，但**从未经过模型**。这防止 agent 意外记录或处理敏感数据。你还可以用这个机制定义确定性的安全规则，控制数据可以流向哪里。

### 状态持久化与 Skills

代码执行加上文件系统访问，让 agent 可以跨操作维护状态。Agent 可以将中间结果写入文件，从而恢复工作和跟踪进度：

```typescript
const leads = await salesforce.query({ 
  query: 'SELECT Id, Email FROM Lead LIMIT 1000' 
});
const csvData = leads.map(l => `${l.Id},${l.Email}`).join('\n');
await fs.writeFile('./workspace/leads.csv', csvData);

// Later execution picks up where it left off
const saved = await fs.readFile('./workspace/leads.csv', 'utf-8');
```

Agent 还可以将自己的代码持久化为可复用函数。一旦 agent 为某个任务开发出可工作的代码，它可以保存该实现供未来使用：

```typescript
// In ./skills/save-sheet-as-csv.ts
import * as gdrive from './servers/google-drive';
export async function saveSheetAsCsv(sheetId: string) {
  const data = await gdrive.getSheet({ sheetId });
  const csv = data.map(row => row.join(',')).join('\n');
  await fs.writeFile(`./workspace/sheet-${sheetId}.csv`, csv);
  return `./workspace/sheet-${sheetId}.csv`;
}

// Later, in any agent execution:
import { saveSheetAsCsv } from './skills/save-sheet-as-csv';
const csvPath = await saveSheetAsCsv('abc123');
```

这与 [Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) 的概念紧密相关——Skills 是可复用的指令、脚本和资源的文件夹，帮助模型在专门任务上提升表现。给这些保存的函数加一个 SKILL.md 文件，就创建了一个结构化的 skill，模型可以引用和使用。随着时间推移，这让你的 agent 构建起一个高层能力工具箱，演化出它最有效工作所需的脚手架。

注意代码执行引入了自身的复杂性。运行 agent 生成的代码需要安全的执行环境，配备适当的[沙箱](https://www.anthropic.com/engineering/claude-code-sandboxing)、资源限制和监控。这些基础设施需求增加了运维开销和安全考量——直接工具调用不需要这些。代码执行的好处——降低 token 成本、减少延迟、改善工具组合——应该与这些实现成本权衡。

---

## 总结

MCP 为 agent 连接众多工具和系统提供了基础协议。但一旦连接的 server 过多，工具定义和结果会消耗过多 token，降低 agent 效率。

虽然这里的很多问题感觉很新——上下文管理、工具组合、状态持久化——但它们在软件工程中有已知的解决方案。**代码执行将这些成熟模式应用到 agent 上**，让它们用熟悉的编程构造更高效地与 MCP server 交互。
