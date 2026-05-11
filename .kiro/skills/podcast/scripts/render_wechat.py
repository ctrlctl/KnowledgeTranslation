#!/usr/bin/env python3
"""将 Markdown 转换为微信公众号可直接粘贴的渲染 HTML。

模仿 md.doocs.org 的输出风格：所有样式内联，无外部依赖。

用法：
    python render_wechat.py <input.md> <output.html>
"""

import re
import sys
from pathlib import Path

from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

# ─── 样式配置（模拟微信公众号渲染风格）─────────────────────────────────

STYLES = {
    "section": (
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
        "font-size:15px;color:#2c2c2c;padding:0 10px;max-width:578px;margin:0 auto;"
        "box-sizing:border-box;word-wrap:break-word;"
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
        "margin-top:1.5em;margin-bottom:0.6em;font-size:16px;font-weight:bold;color:#1a1a1a;"
        "border-left:3px solid #1e88e5;padding-left:0.6em;"
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
    ),
    "h4": (
        "margin-top:1.2em;margin-bottom:0.5em;font-size:15px;font-weight:bold;color:#1a1a1a;"
        "border-left:3px solid #1e88e5;padding-left:0.6em;"
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
    ),
    "p": "margin-bottom:1.5em;line-height:2;letter-spacing:0.5px;",
    "strong": "color:#1e88e5;font-weight:bold;",
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
    "a": "color:#576b95;text-decoration:none;border-bottom:1px solid #576b95;",
    "separator": "text-align:center;color:#ccc;margin:2em 0;letter-spacing:0.5em;",
}


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_inline(text):
    """处理行内元素：bold, italic, code, links, images."""
    # Images (must be before links)
    # 输出 <img> 标签，粘贴到微信编辑器时图片会被自动上传
    text = re.sub(
        r'!\[([^\]]*)\]\(([^)]+)\)',
        lambda m: (
            f'<img style="{STYLES["img"]}" src="{m.group(2)}" alt="{m.group(1)}" />'
        ),
        text
    )
    # Links — 微信公众号不允许外部链接，转为加粗纯文本（无链接色）
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: f'<span style="color:#1e88e5;font-weight:bold;">{m.group(1)}</span>',
        text
    )
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


def md_to_wechat_html(md_text):
    """将 Markdown 转为微信公众号 HTML。"""
    # 去掉 <style> 块
    md_text = re.sub(r'<style>.*?</style>', '', md_text, flags=re.DOTALL)

    lines = md_text.split('\n')
    html_parts = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 空行
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
            text = render_inline(h_match.group(2))
            tag = f"h{level}" if level <= 4 else "h4"
            style = STYLES.get(tag, STYLES["h4"])
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
            i += 1  # skip closing ```
            code_content = '\n'.join(code_lines)
            # 语法高亮
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

        # 普通段落（收集连续非空行，但遇到特殊行停止）
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

    # 包裹在 section 中
    content = '\n'.join(html_parts)
    return f'<section style="{STYLES["section"]}">\n{content}\n</section>'


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
    html = md_to_wechat_html(md_text)
    out_path.write_text(html, encoding="utf-8")
    print(f"已生成: {out_path} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
