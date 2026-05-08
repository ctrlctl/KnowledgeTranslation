#!/usr/bin/env python3
"""将 Markdown 转换为微信公众号可直接粘贴的渲染 HTML。

模仿 md.doocs.org 的输出风格：所有样式内联，无外部依赖。

用法：
    python render_wechat.py <input.md> <output.html>
"""

import re
import sys
from pathlib import Path

# ─── 样式配置（模拟微信公众号渲染风格）─────────────────────────────────

STYLES = {
    "section": (
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
        "font-size:15px;color:#333;padding:0 10px;max-width:578px;margin:0 auto;"
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
        "font-family:'Noto Serif SC','Source Han Serif CN','STSong','SimSun',Georgia,serif;"
    ),
    "p": "margin-bottom:1.5em;line-height:2;letter-spacing:0.5px;",
    "strong": "color:#1a1a1a;font-weight:bold;",
    "em": "font-style:italic;",
    "blockquote": (
        "border-left:3px solid #cbcbcb;padding:0.8em 1em;margin:1.5em 0;"
        "background:#f8f8f8;color:#666;font-size:14px;"
    ),
    "blockquote_p": "margin:0;line-height:1.9;",
    "code_inline": (
        "font-size:13px;padding:2px 5px;background:#f5f5f5;border-radius:3px;"
        "font-family:Menlo,Monaco,Consolas,monospace;color:#d14;"
    ),
    "code_block": (
        "display:block;overflow-x:auto;padding:1em;margin:1.5em 0;font-size:12px;"
        "line-height:1.6;background:#2b2b2b;color:#f8f8f2;border-radius:4px;"
        "font-family:Menlo,Monaco,Consolas,monospace;"
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
    # 微信需手动上传图片，显示文件名提示
    text = re.sub(
        r'!\[([^\]]*)\]\(([^)]+)\)',
        lambda m: (
            f'<p style="text-align:center;margin:1.5em 0;color:#999;font-size:13px;">'
            f'[ 插入图片：{m.group(2).split("/")[-1]} ]</p>'
        ),
        text
    )
    # Links — 微信公众号不允许非 mp.weixin.qq.com 域名链接，全部转为纯文本
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: f'<span style="color:#576b95;">{m.group(1)}</span>',
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
        h_match = re.match(r'^(#{1,3})\s+(.+)$', line)
        if h_match:
            level = len(h_match.group(1))
            text = render_inline(h_match.group(2))
            tag = f"h{level}"
            style = STYLES.get(tag, STYLES["h3"])
            html_parts.append(f'<{tag} style="{style}">{text}</{tag}>')
            i += 1
            continue

        # 代码块
        if line.strip().startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(escape_html(lines[i]))
                i += 1
            i += 1  # skip closing ```
            code_content = '\n'.join(code_lines)
            html_parts.append(f'<pre style="{STYLES["code_block"]}">{code_content}</pre>')
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

        # 图片单独一行
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line.strip())
        if img_match:
            img_name = img_match.group(2).split("/")[-1]
            html_parts.append(
                f'<p style="text-align:center;margin:1.5em 0;color:#999;font-size:13px;">'
                f'[ 插入图片：{img_name} ]</p>'
            )
            i += 1
            continue

        # 普通段落（收集连续非空行，但遇到特殊行停止）
        para_lines = []
        while i < len(lines) and lines[i].strip():
            if re.match(r'^#{1,3}\s+', lines[i]):
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
    html = md_to_wechat_html(md_text)
    out_path.write_text(html, encoding="utf-8")
    print(f"已生成: {out_path} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
