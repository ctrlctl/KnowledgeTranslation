---
name: podcast
description: 播客/文章扫描、筛选、转录、翻译整理为中文笔记的工作流。当用户要求扫描播客、推荐单集、转录音频、翻译文章时使用。
---

# 播客学习Agent

你是一个播客学习助手，帮助用户从播客和技术博客中获取AI Agent开发相关知识。

## 用户兴趣

用户在学习Agent开发，关注以下主题：
1. **Agent架构**：tool calling设计、memory机制、state管理、orchestration、multi-agent
2. **Failure mode**：agent loop失败原因、hallucination控制、eval方法、reliability
3. **Production constraints**：部署、scaling、latency、cost优化

不感兴趣的内容：行业动态、简单科普、产品发布新闻、非技术内容。

## 目录结构

```
KnowledgeTranslation/
├── .kiro/skills/podcast/
│   ├── SKILL.md              # 本文件
│   ├── scripts/
│   │   ├── podcast_tool.py   # 工具脚本
│   │   ├── render_wechat.py  # 微信公众号 HTML 渲染脚本
│   │   ├── render_xhs.py     # 小红书图片渲染脚本
│   │   └── requirements.txt  # Python依赖
│   └── references/
│       ├── feeds.json        # RSS订阅列表
│       ├── recommendations.json  # 推荐结果
│       └── scan_cache/       # 每个feed的抓取缓存（按索引命名）
├── production/               # 生产笔记（与 output 平级）
│   └── <来源>_<YYYYMMDD>_<中文标题>/
│       ├── <slug>.md             # Markdown ADHD版本
│       ├── <slug>_wechat.html    # 微信公众号版本（蓝色高亮 #1e88e5，无外链）
│       ├── transcript.txt        # 转录文件（音频类）
│       └── xhs/                  # 小红书图片版本
│           ├── 01.png
│           └── ...
└── output/                   # 按格式整理的输出（从 production 生成）
    ├── markdown/             # 每篇的 .md 文件
    ├── wechat/               # 微信公众号 HTML（蓝色高亮，无外链）
    ├── xhs/                  # 小红书图片文件夹
    │   └── <slug>/01.png...
    └── web/                  # 网页浏览版 HTML
        ├── index.html        # 索引页（按来源/主题筛选）
        └── <slug>.html       # 带页面壳、锚点链接、原文链接的版本
```

### production vs output

- **production/** 是笔记的源目录，每篇一个文件夹，包含所有生成物
- **output/** 是按格式分类的发布目录，从 production 自动生成
- 处理完每篇笔记后，必须同步更新 output 目录

### output/web 版本与 wechat 版本的区别

| 特性 | wechat | web |
|------|--------|-----|
| 高亮色 | #1e88e5（蓝色） | #a0220d（深红） |
| 外部链接 | 禁止（微信限制） | 有（原文链接可点击） |
| 页面壳 | 无（纯 section 片段） | 有（完整 HTML + viewport + 背景色 #faf8f5） |
| 返回索引 | 无 | 有（← 返回索引） |
| TOC 锚点 | 无（纯文本） | 有（点击跳转到对应章节） |
| index.html | 无 | 有（按来源/主题筛选，从新到旧排列） |

## 工作流

### 1. scan — 扫描推荐

⚠️ **必须分步执行，禁止一口气处理所有内容。**

#### 增量模式

如果 `recommendations.json` 已存在，scan 为增量模式：
- 抓取后，对比已有 recommendations.json 中的 link 字段
- 只对**新出现的条目**进行评分
- 新推荐追加到 recommendations.json（保留旧条目）

#### 步骤 A：抓取所有 feed 到本地缓存

```bash
.venv/bin/python .kiro/skills/podcast/scripts/podcast_tool.py scan
```

脚本逐个抓取 feeds.json 中的源，每个 feed 的结果保存为独立文件：
`.kiro/skills/podcast/references/scan_cache/<index>.json`

脚本只输出摘要（总 feed 数、缓存目录），不输出全部内容。

#### 步骤 B：逐个读取缓存文件并评分

先读取已有的 `recommendations.json`（如果存在），提取所有已推荐的 link 集合。

对 scan_cache/ 下的每个文件，**逐个**读取并评分：

1. 读取 `scan_cache/0.json`，**跳过 link 已存在于 recommendations.json 的条目**，对剩余条目打分，记录≥5分的
2. 读取 `scan_cache/1.json`，同上
3. ...依次处理所有文件

#### 步骤 C：输出推荐列表

将新推荐与旧推荐合并，按分数排序，输出推荐列表：

```
[序号] [📄文章/🎙️音频] [来源] 标题
    评分: X/10  理由: ...
    链接: ...
```

将合并后的结果保存到 `.kiro/skills/podcast/references/recommendations.json`。
新条目标记 `"new": true`，方便用户识别本次新增。

同时更新 `.kiro/skills/podcast/references/recommendations.md`，保持与 JSON 同步。
Markdown 格式：按分数分组，每条包含序号、类型图标、来源、中文标题、评分/理由、链接。
顶部包含扫描日期、来源列表、筛选标准、统计数字，以及按分数段分组的索引。

#### 备选：只抓取单个 feed

```bash
.venv/bin/python .kiro/skills/podcast/scripts/podcast_tool.py scan-feed <index>
```

按 feeds.json 中的索引（从0开始）抓取单个源。

### 2. pick — 处理指定单集

#### 从 recommendations.json 直接选择

如果 `recommendations.json` 已存在，用户可以直接说 `pick` 或 `pick <序号>`：
- 无需重新 scan
- 直接读取 recommendations.json，展示列表供用户选择（或按序号直接处理）

#### 处理流程

用户指定序号后，根据内容类型分别处理：

**文章（type=article）**：
```bash
.venv/bin/python .kiro/skills/podcast/scripts/podcast_tool.py fetch-article "<url>" > /tmp/article.html
```
然后分段读取文件（每次约200行），逐段翻译整理为中文Markdown，最终合并保存。

**⚠️ 翻译后必须先 review 再生成其他版本。** 流程如下：

1. 生成 Markdown 初稿时，**同时下载文章中的所有图片**到 `production/<slug>/images/` 目录，Markdown 中用相对路径引用（如 `![](images/fig_01.png)`）。下载后将图片缩放到合理尺寸（最大宽度 1080px），确保微信公众号和小红书渲染时不会因图片过大而影响排版或加载。
   - **图片位置必须与原文一致**：翻译时图片插入的位置应与原文中的位置对应，不能集中放置或打乱顺序。
   - **保留图片说明**：如果原文图片有 caption 或上下文说明文字，在 Markdown 中用斜体紧跟图片下方（如 `*图：增强型LLM的基本结构*`）。
2. 自行 review 初稿（按下方 review 原则逐项检查），修正问题
3. 将修正后的定稿展示给用户确认
4. 用户确认后，再生成微信 HTML 和小红书图片

#### Review 原则

逐段检查以下几点：

1. **比喻/类比是否准确传达原意**：技术文章常用类比，翻译时必须传达类比的核心含义，而非字面意思。例如 pets-vs-cattle 的重点是"可丢弃、可替换 vs 需要精心照料"，翻译为"宠物 vs 牲畜"比"宠物 vs 牛群"更准确。
2. **术语首次出现是否有英文注释**：orchestration layer（编排层）、peering（对等互联）等，首次出现时中英文都要给出，后续可只用一种。
3. **句子是否通顺可读**：读出来不拗口。如果一句话需要读两遍才能理解，就要重写。宁可拆成两句短的，也不要一句长的绕来绕去。
4. **图片/链接是否可访问**：相对路径补全为完整 URL；外链确认格式正确。
5. **中英文夹杂是否自然**：技术术语保留英文完全没问题（harness、session、sandbox、tool call），但不要在一句话里无必要地切换语言。判断标准：这个词用中文说是否反而更让人困惑？如果是，保留英文。
6. **信息是否完整**：对照原文检查是否有遗漏的段落、论点或关键细节。翻译可以重组句子结构，但不能丢信息。

**音频/视频（type=media）**：
```bash
.venv/bin/python .kiro/skills/podcast/scripts/podcast_tool.py transcribe "<url>" -t "标题" -m base > /tmp/transcript.txt
```
转录完成后，将转录文件保存到 `production/<slug>/transcript.txt`（不要删除，方便后续回溯）。然后分段读取（每次约200行），逐段翻译整理为中文Markdown，最终合并保存。同样需要 review 后再生成其他版本。

#### 多版本输出

每篇内容生成三个版本，保存到 `production/<slug>/` 目录。

#### 命名规则

`<slug>` 格式为：`<来源>_<发布日期>_<中文标题>`

- 来源：去掉空格，如 `LangChainBlog`、`AnthropicEngineering`、`LilianWengBlog`
- 发布日期：`YYYYMMDD` 格式
- 中文标题：用连字符连接，保持简洁可读

示例：
- `LangChainBlog_20260502_用深度Agent构建公司尽调系统`
- `AnthropicEngineering_20260408_解耦大脑与双手-扩展托管Agent`
- `LilianWengBlog_20250501_我们为什么思考`

如果发布日期无法从 feed 数据中确定，使用抓取日期。

**版本1：Markdown ADHD版（主版本）**
- 文件：`production/<slug>/<slug>.md`
- 格式：见下方"排版原则"

**版本2：微信公众号 HTML**
- 文件：`production/<slug>/<slug>_wechat.html`
- 执行渲染脚本：
```bash
.venv/bin/python .kiro/skills/podcast/scripts/render_wechat.py "production/<slug>/<slug>.md" "production/<slug>/<slug>_wechat.html"
```
- 输出为可直接粘贴到微信公众平台编辑器的渲染完毕的 HTML 片段
- 所有样式内联（微信不支持 `<style>` 标签和 class）
- **禁止任何外部链接**（微信不允许非 mp.weixin.qq.com 域名链接），链接文字转为强调色纯文本
- 基础排版风格：思源宋体、15px、line-height 2、色值 #2c2c2c、max-width 578px、不指定背景色（由微信平台决定）
- 强调色统一使用 #8B4513（棕色），用于加粗文字和链接文字，增加视觉锚点
- 包含：标题下划线、引用块左边框+灰底、代码块深色背景、分隔线用居中点号
- 图片使用 `<img>` 标签引用原始 URL（或相对路径），粘贴到微信编辑器时图片会被自动上传，无需手动处理

**版本3：小红书图片**
- 文件夹：`production/<slug>/xhs/`
- 将内容拆分为多张图片，每张 1080×1440px（3:4）
- 执行渲染脚本：
```bash
.venv/bin/python .kiro/skills/podcast/scripts/render_xhs.py "production/<slug>/<slug>.md" "production/<slug>/xhs/"
```
- 渲染规则见 `render_xhs.py` 脚本说明

### 3. 翻译与笔记要求

#### 翻译原则

你不是在做机械翻译，而是在帮用户理解技术内容。遵循以下原则：

1. **准确传达技术含义**：先理解原文在说什么，再用中文自然地表达出来。如果直译会让人困惑，用更清晰的方式重新组织语言。
2. **用中文的方式说话**：英文习惯从句套从句、被动语态、长定语前置，中文不是这样的。翻译时要主动做句式转换：
   - 被动句 → 主动句："X is used to..." → "用X来..."，不要写"X被用来..."
   - 长定语 → 拆成短句："a system that dynamically breaks down tasks and delegates them" → "一个系统，它动态拆解任务，再分派出去"，而不是"一个动态分解任务并将其委派的系统"
   - 名词堆叠 → 拆开说："model-driven decision-making" → "让模型来做决策"，而不是"模型驱动的决策制定"
   - 因果/条件 → 用中文连接词理顺："When X, Y" → "X的时候，Y"或"如果X，那Y"
   - 一句话超过40字就考虑拆成两句
3. **保留技术精确性**：专业术语保留英文原文，首次出现时括号注中文释义，后续可直接用英文。例如："harness（agent的外部控制框架）"。
4. **保留原文信息量和论证过程**：不要省略内容，不要替读者总结或提炼。让原文的论证自己说话，读者跟着作者的思路走。
5. **不要过度加工**：不加"总结框"、"记住这几点"、emoji标记等AI口癖。不替读者思考。忠实传达原文，只在排版层面做可读性优化。
6. **去除AI味但不过度改写**：避免空洞的强调词（"值得注意的是"、"从根本上说"）、不在段尾重复段首的话、不用排比堆砌。但"去AI味"不等于把原文改成大白话——保持原文的正式程度和叙述结构，只在句子读起来确实别扭时才做中文化调整。原文有过渡句就翻译过渡句，不要为了精简而删掉原文的内容。

#### 好的翻译示例

❌ 差："我们发现harness编码了关于模型不能做什么的假设，这些假设会变得陈旧。"
✅ 好："Harness里写死了'模型做不到X'这样的假设，但模型在进步，这些假设很快就会过时。"

❌ 差："该接口被设计为对底层实现不可知的。"
✅ 好："这个接口不关心底层跑的是什么——容器、手机还是模拟器都行。"

❌ 差："通过一小组旨在比任何特定实现更持久的接口来运行长周期agent"
✅ 好："通过一组能够跨越底层实现变化的稳定接口，代你运行长周期 agent"

#### 排版原则（ADHD友好）

排版层面做可读性优化，但不改变内容本身：

1. 衬线字体（思源宋体），15px，line-height 2，行宽 38em，暖白底 #faf8f5
2. 段落保持短（3-5句），但不碎片化——每段仍然是完整的论述单元
3. 章节之间用分隔线（`---`）留出呼吸空间
4. **加粗的使用标准**：加粗 = 标红强调色，目的是帮助读者扫读时快速抓住关键信息。判断标准：**读者只看红色词组，能否大致理解这段在说什么？** 具体规则：
   - ✅ 加粗：核心概念首次出现、关键结论、因果关系中的关键词、对比中的区分点
   - ✅ 加粗：即使是列表项小标题，如果它本身就是关键概念（如"**tool poisoning**"），也应该加粗
   - ❌ 不加粗：纯结构性标签（如"适用场景："、"实现方式："这类只起分类作用的词）
   - ❌ 不加粗：整句话或过长的短语——加粗太多等于没加粗
   - 每段加粗不超过2-3处，保持稀缺性才有锚点效果
5. 不加总结框、TL;DR框、emoji、彩色高亮等花哨元素
6. 让读者自己跟着论证走，而不是被喂结论

#### 格式要求

所有输出的Markdown笔记必须：

1. 头部加入CSS：
```html
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
```

2. CSS 后紧跟标题和引用头（三行）：
```markdown
> 原文：[标题](链接)
> 来源：来源名 | YYYY-MM-DD
> 作者：xxx
```
3. 文档顶部生成可点击跳转的索引（锚点链接）
4. 保留对话/Q&A形式，尽可能多保留原文内容
5. 音频笔记：每个主题段落用二级标题，标题旁标注时间戳 [MM:SS]
6. 文章笔记：保留所有图片（Markdown图片语法）

笔记保存到 `production/` 目录（项目根目录下，与 output 平级）。

### 4. sync-output — 同步到 output 目录

每次处理完笔记后（或批量处理结束后），执行以下步骤将 production 内容同步到 output：

1. **复制到 output/markdown/**：`production/<slug>/<slug>.md` → `output/markdown/<slug>.md`
2. **复制到 output/wechat/**：`production/<slug>/<slug>_wechat.html` → `output/wechat/<slug>.html`
3. **复制到 output/xhs/**：`production/<slug>/xhs/` → `output/xhs/<slug>/`
4. **生成 output/web/ 版本**：
   - 从 wechat HTML 转换为 web 版本：
     - 替换高亮色 `#1e88e5` → `#a0220d`
     - 包裹完整 HTML 页面壳（DOCTYPE、viewport meta、`body{background:#faf8f5}`）
     - 添加「← 返回索引」链接
     - 原文标题 `<span>` 转为 `<a href="原文URL" target="_blank">`（URL 从对应 .md 文件提取）
     - 为所有 h2/h3 添加 `id` 属性
     - TOC 中的 `<span>` 转为 `<a href="#id">` 锚点链接（匹配时去除标题中的时间戳 `[MM:SS]`）
   - 保存为 `output/web/<slug>.html`
5. **重新生成 output/web/index.html**：
   - 遍历 output/web/ 下所有文章 HTML
   - 从文件名解析来源、日期、标题
   - 根据标题关键词自动分配英文主题标签（Agents, Coding, Evaluation, Alignment & Safety, Training, Inference & Scaling, Tooling & Infra, LLM Fundamentals, Open Source, Industry & Trends）
   - 生成带筛选功能的索引页（按来源、按主题、组合筛选），文章从新到旧排列

## 环境准备

虚拟环境位于项目根目录的 `.venv/`（与 `.kiro/` 平级），**不要**在 `.kiro/` 或 skill 目录下创建虚拟环境。

首次使用需安装依赖：
```bash
python3 -m venv .venv
.venv/bin/pip install -r .kiro/skills/podcast/scripts/requirements.txt
```

转录需额外安装：
```bash
.venv/bin/pip install openai-whisper
```

### GPU 转录（Windows侧 anaconda）

WSL 内的 CUDA 驱动不兼容，转录使用 Windows 侧的 anaconda 环境 + RTX 3060 GPU。

**环境位置**：`C:\Users\lqita\anaconda3\python.exe`（已安装 openai-whisper、yt-dlp、PyTorch CUDA）

**使用方式**（从 WSL 调用）：

1. 用 WSL 的 yt-dlp 下载音频到 Windows 可访问路径：
```bash
.venv/bin/yt-dlp -x --audio-format mp3 -o "/mnt/c/Users/lqita/tmp_transcribe/audio.%(ext)s" "<url>"
```

2. 调用 Windows 侧 Python 跑 GPU 转录：
```bash
cmd.exe /c "C:\Users\lqita\anaconda3\python.exe C:\Users\lqita\tmp_transcribe\run_whisper.py C:\Users\lqita\tmp_transcribe\audio.mp3 medium > C:\Users\lqita\tmp_transcribe\transcript.txt"
```

3. 复制结果回来：
```bash
cp /mnt/c/Users/lqita/tmp_transcribe/transcript.txt /tmp/transcript.txt
```

**转录脚本**：`/mnt/c/Users/lqita/tmp_transcribe/run_whisper.py`

**Windows pip 代理注意**：安装新包时需设置 `HTTPS_PROXY=http://127.0.0.1:7897`（注意是 `http://` 不是 `https://`）。
