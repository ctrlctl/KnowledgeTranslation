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

# 用 Claude Code：HTML 的不合理有效性

> 原文：[Using Claude Code: The Unreasonable Effectiveness of HTML](https://simonwillison.net/2026/May/8/unreasonable-effectiveness-of-html/)
> 来源：Simon Willison | 2026-05-08
> 作者：Simon Willison

---

## 核心观点

Thariq Shihipar（Anthropic Claude Code 团队成员）发表了一篇引人深思的文章，主张在向 Claude 请求输出时用 **HTML 替代 Markdown**。

文章中充满了有趣的示例（收集在 thariqs.github.io/html-effectiveness 上）和 prompt 建议，比如：

> `Help me review this PR by creating an HTML artifact that describes it. I'm not very familiar with the streaming/backpressure logic so focus on that. Render the actual diff with inline margin annotations, color-code findings by severity and whatever else might be needed to convey the concept well.`

---

## Simon 的反思

Simon 从 GPT-4 时代起就默认用 Markdown 请求大多数输出——当时 8,192 token 的限制意味着 Markdown 相对 HTML 的 token 效率非常值得。

Thariq 的文章让他重新考虑了这一点，**尤其是对于输出**。让 Claude 用 HTML 解释意味着它可以嵌入 SVG 图表、交互式小部件、页内导航，以及各种让信息更易浏览的方式。

Simon 去年 12 月写过关于构建 HTML 工具的有用模式，但那主要聚焦于交互式工具（如他 tools.simonwillison.net 站点上的那些）。现在他很兴奋要开始更多地尝试用**富 HTML 解释**来响应临时 prompt。

---

## 实际尝试

Simon 用 copy.fail（一个描述最近发现的 Linux 安全漏洞的站点，包含作为混淆 Python 分发的 PoC）做了测试：

```bash
curl https://copy.fail/exp | llm -m gpt-5.5 -s 'Explain this code in detail. Reformat it, expand out any confusing bits and go deep into what it does and how it works. Output HTML, neatly styled and using capabilities of HTML and CSS and JavaScript to make the explanation rich and interactive and as clear as possible'
```

生成的 HTML 页面效果相当好——深色主题的技术文档，包含安全提示框、高层摘要、分步解释、以及"为什么代码看起来奇怪"的模式-目的对照表。不过他认为应该更强调解释漏洞本身而非周围的 Python 框架。

---

## 启示

从 Markdown 到 HTML 的转变反映了一个更大的趋势：随着 token 限制不再是瓶颈，**输出格式的选择应该优先考虑信息传达的丰富度**而非 token 效率。HTML 让 LLM 能利用完整的 web 技术栈——CSS 布局、SVG 可视化、JavaScript 交互——来更好地解释复杂概念。
