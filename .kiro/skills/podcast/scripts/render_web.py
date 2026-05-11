#!/usr/bin/env python3
"""将 Markdown 转换为网页浏览版 HTML（完整页面，带锚点导航）。

与 render_wechat.py 共用解析逻辑，区别：
- 高亮色 #a0220d（深红）
- 保留外部链接（可点击跳转）
- 完整 HTML 页面壳（viewport + 背景色 #faf8f5 + 返回索引链接）
- TOC 锚点可点击跳转
- h2/h3 自动生成 id

用法：
    python render_web.py <input.md> <output.html>
"""

import re
import sys
import unicodedata
from pathlib import Path

from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

# ─── 样式配置 ─────────────────────────────────────────────────────────

ACCENT = "#a0220d"

STYLES = {
    "section": (
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
        "font-size:15px;color:#2c2c2c;padding:2em;max-width:42em;margin:0 auto;"
        "box-sizing:border-box;word-wrap:break-word;line-height:2;"
    ),
    "h1": (
        "margin-top:2em;margin-bottom:0.8em;font-size:20px;font-weight:bold;color:#1a1a1a;"
        "border-bottom:1px solid #eee;padding-bottom:0.4em;"
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
    ),
    "h2": (
        "margin-top:2em;margin-bottom:0.8em;font-size:18px;font-weight:bold;color:#1a1a1a;"
        "border-bottom:1px solid #f0f0f0;padding-bottom:0.3em;"
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
    ),
    "h3": (
        f"margin-top:1.5em;margin-bottom:0.6em;font-size:16px;font-weight:bold;color:#1a1a1a;"
        f"border-left:3px solid {ACCENT};padding-left:0.6em;"
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
    ),
    "h4": (
        f"margin-top:1.2em;margin-bottom:0.5em;font-size:15px;font-weight:bold;color:#1a1a1a;"
        f"border-left:3px solid {ACCENT};padding-left:0.6em;"
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
    ),
    "p": "margin-bottom:1.5em;line-height:2;letter-spacing:0.5px;",
    "strong": f"color:{ACCENT};font-weight:bold;",
    "em": "font-style:italic;",
    "blockquote": (
        "border-left:3px solid #cbcbcb;padding:0.8em 1em;margin:1.5em 0;"
        "background:#f3f1ed;color:#555;font-size:14px;"
    ),
    "blockquote_p": "margin:0;line-height:1.9;",
    "code_inline": (
        "font-size:13px;padding:2px 5px;background:#f0ede8;border-radius:3px;"
        "font-family:Menlo,Monaco,Consolas,monospace;color:#d14;"
    ),
    "code_block": (
        "display:block;padding:1em;margin:1.5em 0;font-size:12px;"
        "line-height:1.6;background:#2e3440;color:#d8dee9;border-radius:4px;"
        "font-family:Menlo,Monaco,Consolas,monospace;white-space:pre-wrap;word-wrap:break-word;"
    ),
    "ul": "margin:1em 0;padding-left:2em;",
    "li": "margin-bottom:0.5em;line-height:2;",
    "img": "max-width:100%;margin:1.5em auto;display:block;border-radius:4px;",
    "hr": "border:none;border-top:1px solid #eee;margin:2em 0;",
    "a": f"color:{ACCENT};text-decoration:none;border-bottom:1px solid {ACCENT};",
    "separator": "text-align:center;color:#ccc;margin:2em 0;letter-spacing:0.5em;",
    "toc_a": f"color:{ACCENT};text-decoration:none;",
    "back_link": f"display:block;margin-bottom:1.5em;font-size:14px;color:{ACCENT};text-decoration:none;",
}


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slugify(text):
    """生成 heading id：去除时间戳 [MM:SS]，转小写，非字母数字转连字符。"""
    text = re.sub(r'\[?\d{1,2}:\d{2}\]?', '', text).strip()
    # 去除 markdown 格式
    text = re.sub(r'[*_`\[\]()]', '', text)
    # 保留中文、字母、数字
    result = []
    for ch in text:
        if ch.isalnum() or unicodedata.category(ch).startswith('Lo'):
            result.append(ch)
        elif ch in (' ', '-', '_'):
            result.append('-')
    slug = '-'.join(filter(None, ''.join(result).split('-')))
    return slug.lower() if slug else 'section'


def render_inline(text):
    """处理行内元素：bold, italic, code, links, images."""
    # Images
    text = re.sub(
        r'!\[([^\]]*)\]\(([^)]+)\)',
        lambda m: f'<img style="{STYLES["img"]}" src="{m.group(2)}" alt="{m.group(1)}" />',
        text
    )
    # Links — 保留外部链接（可点击），页内锚点不加 target="_blank"
    def _render_link(m):
        href = m.group(2)
        target = '' if href.startswith('#') else ' target="_blank"'
        return f'<a style="{STYLES["a"]}" href="{href}"{target}>{m.group(1)}</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _render_link, text)
    # Bold
    text = re.sub(
        r'\*\*([^*]+)\*\*',
        lambda m: f'<strong style="{STYLES["strong"]}">{m.group(1)}</strong>',
        text
    )
    # Italic
    text = re.sub(
        r'\*([^*]+)\*',
        lambda m: f'<em style="{STYLES["em"]}">{m.group(1)}</em>',
        text
    )
    # Inline code
    text = re.sub(
        r'`([^`]+)`',
        lambda m: f'<code style="{STYLES["code_inline"]}">{escape_html(m.group(1))}</code>',
        text
    )
    return text


def md_to_web_html(md_text):
    """将 Markdown 转为网页浏览版 HTML。"""
    # 去掉 <style> 块
    md_text = re.sub(r'<style>.*?</style>', '', md_text, flags=re.DOTALL)

    lines = md_text.split('\n')
    html_parts = []
    i = 0

    # 第一遍：不再自动生成 TOC（Markdown 源文件自带索引章节）
    # 仅收集 headings 用于生成 id
    heading_ids = []
    for line in lines:
        h_match = re.match(r'^(#{2,3})\s+(.+)$', line)
        if h_match:
            raw_text = h_match.group(2)
            hid = slugify(raw_text)
            heading_ids.append(hid)

    toc_html = ''

    # 用于去重 id
    id_counts = {}

    def unique_id(hid):
        if hid in id_counts:
            id_counts[hid] += 1
            return f"{hid}-{id_counts[hid]}"
        id_counts[hid] = 0
        return hid

    # 第二遍：渲染内容
    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        # 分隔线
        if re.match(r'^-{3,}\s*$', line.strip()) or re.match(r'^\*{3,}\s*$', line.strip()):
            html_parts.append(f'<p style="{STYLES["separator"]}">· · ·</p>')
            i += 1
            continue

        # 标题
        h_match = re.match(r'^(#{1,4})\s+(.+)$', line)
        if h_match:
            level = len(h_match.group(1))
            raw_text = h_match.group(2)
            text = render_inline(raw_text)
            tag = f"h{level}" if level <= 4 else "h4"
            style = STYLES.get(tag, STYLES["h4"])
            if level in (2, 3):
                hid = unique_id(slugify(raw_text))
                html_parts.append(f'<{tag} id="{hid}" style="{style}">{text}</{tag}>')
            else:
                html_parts.append(f'<{tag} style="{style}">{text}</{tag}>')
            i += 1
            continue

        # 代码块
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1
            code_content = '\n'.join(code_lines)
            try:
                lexer = get_lexer_by_name(lang) if lang else TextLexer()
            except Exception:
                lexer = TextLexer()
            formatter = HtmlFormatter(nowrap=True, noclasses=True, style='nord')
            highlighted = highlight(code_content, lexer, formatter)
            html_parts.append(f'<pre style="{STYLES["code_block"]}">{highlighted}</pre>')
            continue

        # 引用块
        if line.strip().startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(re.sub(r'^>\s?', '', lines[i]))
                i += 1
            quote_content = ' '.join(quote_lines)
            quote_html = render_inline(quote_content)
            html_parts.append(
                f'<blockquote style="{STYLES["blockquote"]}">'
                f'<p style="{STYLES["blockquote_p"]}">{quote_html}</p>'
                f'</blockquote>'
            )
            continue

        # 无序列表
        if re.match(r'^[-*]\s+', line.strip()):
            items = []
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i].strip()):
                item_text = re.sub(r'^[-*]\s+', '', lines[i].strip())
                items.append(f'<li style="{STYLES["li"]}">{render_inline(item_text)}</li>')
                i += 1
            html_parts.append(f'<ul style="{STYLES["ul"]}">{"".join(items)}</ul>')
            continue

        # 表格
        if line.strip().startswith('|') and '|' in line.strip()[1:]:
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row = lines[i].strip()
                if re.match(r'^\|[\s\-:|]+\|$', row):
                    i += 1
                    continue
                cells = [c.strip() for c in row.strip('|').split('|')]
                table_rows.append(cells)
                i += 1
            if table_rows:
                tbl = '<table style="width:100%;border-collapse:collapse;margin:1.5em 0;font-size:14px;">'
                for ri, row in enumerate(table_rows):
                    tbl += '<tr>'
                    for cell in row:
                        tag = 'th' if ri == 0 else 'td'
                        cell_style = "border:1px solid #e0e0e0;padding:8px 10px;line-height:1.8;"
                        if ri == 0:
                            cell_style += "background:#f5f5f5;font-weight:bold;"
                        tbl += f'<{tag} style="{cell_style}">{render_inline(cell)}</{tag}>'
                    tbl += '</tr>'
                tbl += '</table>'
                html_parts.append(tbl)
            continue

        # 图片单独一行
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line.strip())
        if img_match:
            img_src = img_match.group(2)
            img_alt = img_match.group(1)
            html_parts.append(
                f'<p style="text-align:center;margin:1.5em 0;">'
                f'<img style="{STYLES["img"]}" src="{img_src}" alt="{img_alt}" /></p>'
            )
            i += 1
            continue

        # 普通段落
        para_lines = []
        while i < len(lines) and lines[i].strip():
            if re.match(r'^#{1,4}\s+', lines[i]):
                break
            if re.match(r'^-{3,}\s*$', lines[i].strip()):
                break
            if re.match(r'^\*{3,}\s*$', lines[i].strip()):
                break
            if lines[i].strip().startswith('```'):
                break
            if lines[i].strip().startswith('>'):
                break
            if re.match(r'^[-*]\s+', lines[i].strip()):
                break
            if re.match(r'^!\[', lines[i].strip()):
                break
            if lines[i].strip().startswith('|') and '|' in lines[i].strip()[1:]:
                break
            para_lines.append(lines[i].strip())
            i += 1

        if para_lines:
            para_text = ' '.join(para_lines)
            para_html = render_inline(para_text)
            html_parts.append(f'<p style="{STYLES["p"]}">{para_html}</p>')

    content = '\n'.join(html_parts)

    # 完整 HTML 页面壳
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>笔记</title>
<style>
body {{ margin:0; padding:0; background:#faf8f5; }}
a {{ color:{ACCENT}; }}
</style>
</head>
<body>
<section style="{STYLES["section"]}">
<a style="{STYLES["back_link"]}" href="index.html">← 返回索引</a>
{toc_html}
{content}
</section>
</body>
</html>'''


def main():
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <input.md> <output.html>")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    md_text = md_path.read_text(encoding="utf-8")
    # 将 images/ 相对路径改为 images/{article_stem}/ 以避免扁平目录下冲突
    article_stem = md_path.stem
    md_text = re.sub(
        r'!\[([^\]]*)\]\(images/',
        lambda m: f'![{m.group(1)}](images/{article_stem}/',
        md_text
    )
    html = md_to_web_html(md_text)
    out_path.write_text(html, encoding="utf-8")
    print(f"已生成: {out_path} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
