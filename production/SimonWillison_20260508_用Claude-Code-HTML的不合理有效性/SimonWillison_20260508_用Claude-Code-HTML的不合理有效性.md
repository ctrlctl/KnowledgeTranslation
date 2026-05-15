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

Thariq Shihipar（Anthropic 的 Claude Code 团队）写了一篇发人深省的文章，主张用 **HTML 而非 Markdown** 作为向 Claude 请求的输出格式。文章塞满了有趣的示例（收集在[这个网站](https://www.claudecodegallery.com/)上）和 prompt 建议，比如：

> 帮我审查这个 PR，创建一个描述它的 HTML artifact。我对 streaming/backpressure 逻辑不太熟悉，所以重点关注那部分。渲染实际的 diff，带内联边注，按严重程度颜色编码发现，以及其他任何能很好传达概念的东西。

从 GPT-4 时代起，我一直默认要求大多数东西用 Markdown，因为当时 8,192 token 的限制意味着 Markdown 相对 HTML 的 token 效率非常值得。Thariq 的这篇文章让我重新考虑了这一点，尤其是对于输出。

**让 Claude 用 HTML 做解释意味着它可以加入 SVG 图表、交互式小部件、页内导航，以及各种让信息更易于浏览的巧妙方式。**

我去年 12 月写过[《构建 HTML 工具的有用模式》](https://simonwillison.net/2024/Dec/21/useful-patterns-for-building-html-tools/)，但那篇主要聚焦于交互式工具，比如我 tools.simonwillison.net 网站上的那些。我很兴奋开始更多地尝试用丰富的 HTML 解释来回应临时 prompt。

---

## 在 copy.fail 上试试

[copy.fail](https://copy.fail/) 描述了一个最近发现的 Linux 安全漏洞，包括一个作为混淆 Python 分发的概念验证。我试着让 GPT-5.5 创建一个 HTML 解释：

```bash
curl https://copy.fail/exp | llm -m gpt-5.5 -s \
  'Explain this code in detail. Reformat it, expand out any confusing bits
   and go deep into what it does and how it works. Output HTML, neatly styled
   and using capabilities of HTML and CSS and JavaScript to make the explanation
   rich and interactive and as clear as possible'
```

[这是生成的 HTML 页面](https://static.simonwillison.net/static/2026/copy-fail-explained.html)。效果相当好，虽然我应该强调解释漏洞本身而不是围绕它的 Python 框架。
