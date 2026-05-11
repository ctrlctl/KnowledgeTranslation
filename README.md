# 播客学习Agent

从播客和技术博客中筛选、转录、翻译AI Agent开发相关内容，整理为中文Markdown笔记。

## 快速开始

```bash
# 1. Clone
git clone git@github.com:ctrlctl/KnowledgeTranslation.git
cd KnowledgeTranslation

# 2. 安装依赖
python3 -m venv .venv
.venv/bin/pip install feedparser yt-dlp openai-whisper

# 3. 确认ffmpeg已安装（Whisper需要）
ffmpeg -version
# 没有的话：sudo apt install ffmpeg
```

## 使用方式

### 方式一：通过Kiro Agent（推荐）

```bash
kiro-cli chat
/agent swap podcast-agent
```

然后直接对话：
- `scan` — 扫描所有订阅源，AI打分推荐
- `pick 1 3 5` — 处理推荐列表中的指定条目

Agent会自动判断内容类型：
- 📄 文章 → 抓取网页 → 翻译为中文Markdown
- 🎙️ 音频 → 下载 → Whisper转录 → 翻译为中文Markdown

### 方式二：直接用脚本

```bash
# 扫描RSS和网页，输出JSON
.venv/bin/python .kiro/skills/podcast/scripts/podcast_tool.py scan

# 抓取文章HTML
.venv/bin/python .kiro/skills/podcast/scripts/podcast_tool.py fetch-article "<url>"

# 转录音频（模型可选：tiny/base/small/medium/large）
.venv/bin/python .kiro/skills/podcast/scripts/podcast_tool.py transcribe "<url>" -t "标题" -m small
```

## 目录结构

```
.kiro/
├── agents/podcast-agent.json          # Kiro Agent配置
└── skills/podcast/
    ├── SKILL.md                       # Agent行为定义
    ├── scripts/
    │   ├── podcast_tool.py            # 工具脚本
    │   └── requirements.txt
    └── references/
        ├── feeds.json                 # 订阅源列表
        ├── recommendations.json       # 推荐结果（结构化）
        └── recommendations.md         # 推荐结果（可读）
production/                            # 生产笔记输出
output/                                # 按格式分类的发布目录
```

## 订阅源管理

编辑 `.kiro/skills/podcast/references/feeds.json`：

```json
// RSS源
{"name": "Practical AI", "url": "https://feeds.transistor.fm/..."}

// 网页抓取源
{"name": "Anthropic Engineering", "source": "web", "url": "https://www.anthropic.com/engineering", "link_pattern": "/engineering/"}
```

## 笔记格式

所有笔记自动包含：
- 衬线字体CSS排版
- 可点击跳转的索引
- 专业术语保留英文（括号注中文）
- 音频笔记带时间戳，文章笔记保留图片

## Whisper模型选择

| 模型 | 精度 | 1小时音频(GPU) | 1小时音频(CPU) |
|------|------|----------------|----------------|
| base | 85-90% | ~3分钟 | ~20分钟 |
| small | 92-95% | ~7分钟 | ~50分钟 |
| medium | 95-97% | ~15分钟 | ~2-3小时 |

有GPU的电脑用 `small` 或 `medium`，无GPU用 `base`。
