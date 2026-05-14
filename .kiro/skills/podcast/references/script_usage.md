# podcast_tool.py 用法

## 依赖安装

```bash
cd .kiro/skills/podcast/scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 转录需额外安装：
pip install openai-whisper
```

## 命令

### scan

扫描所有RSS feeds，输出JSON到stdout（每个feed取最近10集）。

```bash
python podcast_tool.py scan
```

输出格式：
```json
[
  {
    "feed": "来源名",
    "title": "标题",
    "summary": "描述（前500字符）",
    "link": "原文链接",
    "audio": "音频URL（仅media类型）",
    "type": "article | media"
  }
]
```

进度信息输出到stderr，JSON数据输出到stdout。

### fetch-article

抓取指定URL的HTML内容，输出到stdout。

```bash
python podcast_tool.py fetch-article "https://example.com/article"
```

### fetch-images

从HTML文件或URL中提取所有图片并下载到指定目录。

```bash
# 推荐：直接从原文URL抓取（很多网站图片通过JS动态加载，静态HTML中不包含）
python podcast_tool.py fetch-images "https://example.com/article" "./images/"

# 备选：从本地HTML文件抓取（仅适用于静态渲染的页面）
python podcast_tool.py fetch-images "production/<slug>/source.html" "./images/"
```

输出JSON映射到stdout（序号、文件名、原始URL）。自动处理Next.js `_next/image` 优化URL和HTML实体编码。

### transcribe

下载音频/视频并用Whisper转录，输出带时间戳的文本到stdout。

```bash
python podcast_tool.py transcribe "https://example.com/audio.mp3" -t "标题" -m base
```

参数：
- `url`（必填）：音频/视频URL，支持YouTube、播客直链等
- `-t, --title`：标题（默认 "episode"）
- `-m, --model`：Whisper模型，可选 tiny/base/small/medium/large（默认 base）

输出格式：
```
[00:00] First sentence...
[00:15] Second sentence...
[01:02] ...
```

进度信息输出到stderr，转录文本输出到stdout。

## 依赖说明

- `feedparser`：RSS/Atom解析
- `yt-dlp`：音频/视频下载（需系统安装ffmpeg）
- `openai-whisper`：语音转录（需GPU加速，CPU也可但慢）
