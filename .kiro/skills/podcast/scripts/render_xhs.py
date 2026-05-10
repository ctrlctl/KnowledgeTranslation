#!/usr/bin/env python3
"""渲染Markdown为小红书图片序列（1080x1440px，3:4比例）。

用法：
    python render_xhs.py <input.md> <output_dir/>

依赖：pillow, pygments
"""

import re
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.token import Token

# ─── 配置 ───────────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1440
PADDING_X = 80
PADDING_Y = 100
CONTENT_WIDTH = WIDTH - 2 * PADDING_X
BG_COLOR = "#faf8f5"
TEXT_COLOR = "#2c2c2c"
HEADING_COLOR = "#1a1a1a"
ACCENT_COLOR = "#a0220d"
SEPARATOR_COLOR = "#ddd"

# 字体大小
FONT_SIZE_BODY = 30
FONT_SIZE_H2 = 38
FONT_SIZE_BOLD = 30
LINE_SPACING = 2.2

# 尝试加载字体（优先 Noto Serif CJK，回退到系统字体）
FONT_CANDIDATES = [
    "/mnt/c/Windows/Fonts/NotoSerifSC-VF.ttf",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/local/share/fonts/NotoSerifCJK-Regular.ttc",
    "C:/Windows/Fonts/NotoSerifSC-VF.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]

FONT_CANDIDATES_BOLD = [
    "/mnt/c/Windows/Fonts/NotoSerifSC-VF.ttf",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/local/share/fonts/NotoSerifCJK-Bold.ttc",
    "C:/Windows/Fonts/NotoSerifSC-VF.ttf",
    "C:/Windows/Fonts/simhei.ttf",
]


def load_font(candidates, size, bold=False):
    for path in candidates:
        try:
            f = ImageFont.truetype(path, size)
            # Handle variable fonts (e.g. NotoSerifSC-VF.ttf)
            try:
                axes = f.get_variation_axes()
                if axes:
                    weight = 700 if bold else 400
                    f.set_variation_by_axes([weight])
            except (AttributeError, OSError):
                pass
            return f
        except (OSError, IOError):
            continue
    # 最终回退
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except (OSError, IOError):
        return ImageFont.load_default()


def get_fonts():
    return {
        "body": load_font(FONT_CANDIDATES, FONT_SIZE_BODY, bold=False),
        "bold": load_font(FONT_CANDIDATES_BOLD, FONT_SIZE_BOLD, bold=True),
        "h2": load_font(FONT_CANDIDATES_BOLD, FONT_SIZE_H2, bold=True),
    }


# ─── Markdown 解析 ──────────────────────────────────────────────────────────

def parse_md_to_blocks(md_text):
    """将Markdown解析为渲染块列表。"""
    blocks = []
    # 去掉 <style>...</style> 和 HTML 标签
    md_text = re.sub(r'<style>.*?</style>', '', md_text, flags=re.DOTALL)
    md_text = re.sub(r'<[^>]+>', '', md_text)

    # 去掉链接语法，保留链接文字（但不影响图片语法 ![...](...) ）
    md_text = re.sub(r'(?<!!)\[([^\]]+)\]\([^)]+\)', r'\1', md_text)

    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # 跳过空行
        if not line:
            blocks.append({"type": "spacer", "height": int(FONT_SIZE_BODY * 0.6)})
            i += 1
            continue

        # 标题
        if line.startswith('## '):
            blocks.append({"type": "h2", "text": line[3:].strip()})
            i += 1
            continue
        if line.startswith('### '):
            blocks.append({"type": "h3", "text": line[4:].strip()})
            i += 1
            continue
        if line.startswith('#### '):
            blocks.append({"type": "h3", "text": line[5:].strip()})
            i += 1
            continue
        if line.startswith('# '):
            blocks.append({"type": "h2", "text": line[2:].strip()})
            i += 1
            continue

        # 分隔线
        if re.match(r'^-{3,}$', line) or re.match(r'^\*{3,}$', line):
            blocks.append({"type": "separator"})
            i += 1
            continue

        # 引用块（> 开头）— 每行独立渲染，用小字+灰色
        if line.startswith('>'):
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_text = re.sub(r'^>\s?', '', lines[i]).strip()
                if quote_text:
                    blocks.append({"type": "quote_line", "text": quote_text})
                i += 1
            blocks.append({"type": "spacer", "height": int(FONT_SIZE_BODY * 0.4)})
            continue

        # 列表项（- 或 * 开头，允许前导空格表示子列表）
        if re.match(r'^\s*[-*]\s+', line):
            while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i].strip() if lines[i].strip() else ''):
                item_text = re.sub(r'^[-*]\s+', '', lines[i].strip())
                blocks.append({"type": "list_item", "text": item_text})
                i += 1
            continue

        # 表格（| 开头的行）
        if line.strip().startswith('|') and '|' in line[1:]:
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row = lines[i].strip()
                # 跳过分隔行 |---|---|
                if re.match(r'^\|[\s\-:|]+\|$', row):
                    i += 1
                    continue
                cells = [c.strip() for c in row.strip('|').split('|')]
                table_rows.append(cells)
                i += 1
            if table_rows:
                blocks.append({"type": "table", "rows": table_rows})
            continue

        # 代码块（``` 开头）
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # skip closing ```
            if code_lines:
                blocks.append({"type": "code_block", "text": '\n'.join(code_lines), "lang": lang})
            continue

        # 图片
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line)
        if img_match:
            blocks.append({"type": "image", "path": img_match.group(2)})
            i += 1
            continue

        # 普通段落（收集连续非空行）
        para_lines = []
        while i < len(lines) and lines[i].strip():
            # 遇到标题、分隔线、列表项、表格、代码块时停止
            if re.match(r'^#{1,3}\s+', lines[i]):
                break
            if re.match(r'^-{3,}\s*$', lines[i].strip()):
                break
            if re.match(r'^\*{3,}\s*$', lines[i].strip()):
                break
            if re.match(r'^[-*]\s+', lines[i].strip()):
                break
            if lines[i].strip().startswith('|') and '|' in lines[i][1:]:
                break
            if lines[i].strip().startswith('```'):
                break
            if re.match(r'^!\[', lines[i].strip()):
                break
            para_lines.append(lines[i].strip())
            i += 1
        text = ' '.join(para_lines)
        if text.strip():
            blocks.append({"type": "paragraph", "text": text})
        continue

    return blocks


# ─── 渲染 ───────────────────────────────────────────────────────────────────

def _is_latin(ch):
    """判断字符是否属于不可拆分的英文/数字序列。"""
    return ch.isascii() and (ch.isalnum() or ch in "-_'")


def wrap_text(text, font, max_width, draw):
    """按像素宽度换行，英文单词不拆分。"""
    lines = []
    current_line = ""
    i = 0
    while i < len(text):
        # 收集一个token（连续英文字母/数字 或 单个非英文字符）
        if _is_latin(text[i]):
            word = ""
            while i < len(text) and _is_latin(text[i]):
                word += text[i]
                i += 1
        else:
            word = text[i]
            i += 1

        test = current_line + word
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w > max_width and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)
    return lines


BOLD_COLOR = "#a0220d"  # 加粗文字用深红色强调色
CODE_COLOR = "#d14"    # inline code 用代码红色
CODE_BG = "#f5f5f5"    # code 背景色

# 暖色调语法高亮（匹配深红强调色）
_TOKEN_COLORS = {
    Token.Keyword: "#c678dd",
    Token.Keyword.Constant: "#d19a66",
    Token.Keyword.Type: "#e5c07b",
    Token.Name.Function: "#e06c75",
    Token.Name.Class: "#e5c07b",
    Token.Name.Decorator: "#e06c75",
    Token.Name.Builtin: "#e5c07b",
    Token.Name.Tag: "#e06c75",
    Token.Name.Attribute: "#d19a66",
    Token.String: "#98c379",
    Token.Number: "#d19a66",
    Token.Operator: "#e06c75",
    Token.Comment: "#7f848e",
    Token.Punctuation: "#abb2bf",
    Token.Literal: "#d19a66",
}


def _token_color(ttype):
    """根据 token 类型返回颜色，向上查找父类型。"""
    while ttype:
        if ttype in _TOKEN_COLORS:
            return _TOKEN_COLORS[ttype]
        ttype = ttype.parent
    return "#abb2bf"


def _get_lexer(lang):
    """根据语言名获取 lexer，失败则返回 TextLexer。"""
    if lang:
        try:
            return get_lexer_by_name(lang)
        except Exception:
            pass
    return TextLexer()


def parse_inline_segments(text):
    """将段落文本解析为 [(text, style), ...] 片段列表。
    style: 'normal', 'bold', 'code'
    """
    segments = []
    parts = re.split(r'(`[^`]+`|\*\*[^*]+\*\*)', text)
    for part in parts:
        if not part:
            continue
        if part.startswith('`') and part.endswith('`'):
            segments.append((part[1:-1], 'code'))
        elif part.startswith('**') and part.endswith('**'):
            segments.append((part[2:-2], 'bold'))
        else:
            clean = re.sub(r'\*([^*]+)\*', r'\1', part)
            if clean:
                segments.append((clean, 'normal'))
    return segments


def wrap_rich_text(segments, fonts, max_width, draw):
    """将带格式的片段按像素宽度换行，返回行列表。
    每行是 [(text, style), ...] 的列表。"""
    lines = []
    current_line = []
    current_width = 0

    for text, style in segments:
        font = fonts["bold"] if style == 'bold' else fonts["body"]
        # 按token遍历（英文单词不拆分）
        i = 0
        while i < len(text):
            if _is_latin(text[i]):
                word = ""
                while i < len(text) and _is_latin(text[i]):
                    word += text[i]
                    i += 1
            else:
                word = text[i]
                i += 1

            bbox = draw.textbbox((0, 0), word, font=font)
            word_w = bbox[2] - bbox[0]
            if current_width + word_w > max_width and current_line:
                lines.append(current_line)
                current_line = []
                current_width = 0
            # 追加到当前行
            if current_line and current_line[-1][1] == style:
                current_line[-1] = (current_line[-1][0] + word, style)
            else:
                current_line.append((word, style))
            current_width += word_w

    if current_line:
        lines.append(current_line)
    return lines


def draw_rich_line(line_segments, fonts, draw, x, y):
    """绘制一行带格式的文本。"""
    cx = x
    for text, style in line_segments:
        font = fonts["bold"] if style == 'bold' else fonts["body"]
        if style == 'bold':
            color = BOLD_COLOR
        elif style == 'code':
            color = CODE_COLOR
        else:
            color = TEXT_COLOR
        draw.text((cx, y), text, font=font, fill=color)
        bbox = draw.textbbox((0, 0), text, font=font)
        cx += bbox[2] - bbox[0]


def estimate_block_height(block, fonts, draw, md_dir=None):
    """估算一个块的渲染高度。"""
    if block["type"] == "spacer":
        return block["height"]
    if block["type"] == "separator":
        return int(FONT_SIZE_BODY * 2)
    if block["type"] == "h2":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        lines = wrap_text(text, fonts["h2"], CONTENT_WIDTH, draw)
        return len(lines) * int(FONT_SIZE_H2 * LINE_SPACING) + 20
    if block["type"] == "h3":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        lines = wrap_text(text, fonts["bold"], CONTENT_WIDTH - 20, draw)
        return len(lines) * int(FONT_SIZE_BODY * LINE_SPACING) + 16
    if block["type"] == "paragraph":
        segments = parse_inline_segments(block["text"])
        lines = wrap_rich_text(segments, fonts, CONTENT_WIDTH, draw)
        return len(lines) * int(FONT_SIZE_BODY * LINE_SPACING)
    if block["type"] == "list_item":
        bullet_indent = 40
        segments = parse_inline_segments(block["text"])
        lines = wrap_rich_text(segments, fonts, CONTENT_WIDTH - bullet_indent, draw)
        return len(lines) * int(FONT_SIZE_BODY * LINE_SPACING)
    if block["type"] == "image":
        # 图片缩放到内容宽度，计算高度
        img_path = _resolve_img_path(block["path"], md_dir)
        if img_path and img_path.exists():
            img = Image.open(img_path)
            scale = CONTENT_WIDTH / img.width
            return int(img.height * scale) + 30
        return 0
    if block["type"] == "table":
        row_h = int(FONT_SIZE_BODY * LINE_SPACING) + 10
        # 预计算每行实际需要的行数（考虑换行）
        rows = block["rows"]
        if not rows:
            return 0
        num_cols = max(len(r) for r in rows)
        col_w = CONTENT_WIDTH // max(num_cols, 1)
        total_h = 20
        for row in rows:
            max_lines = 1
            for cell in row[:num_cols]:
                cell_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell)
                lines = wrap_text(cell_text, fonts["body"], col_w - 16, draw)
                max_lines = max(max_lines, len(lines))
            total_h += max_lines * row_h
        return total_h
    if block["type"] == "code_block":
        code_text = block["text"]
        lang = block.get("lang", "")
        line_h = int(FONT_SIZE_BODY * 1.6)
        code_max_w = CONTENT_WIDTH - 40
        font = fonts["body"]
        lexer = _get_lexer(lang)
        # 按行分组 tokens
        code_lines_tokens = [[]]
        for ttype, value in lex(code_text, lexer):
            parts = value.split('\n')
            for pi, part in enumerate(parts):
                if pi > 0:
                    code_lines_tokens.append([])
                if part:
                    code_lines_tokens[-1].append(part)
        # 对每行做 wrap 计算总渲染行数
        total_render_lines = 0
        for line_parts in code_lines_tokens:
            line_text = ''.join(line_parts)
            wrapped = wrap_text(line_text, font, code_max_w, draw) or [""]
            total_render_lines += len(wrapped)
        return total_render_lines * line_h + 40
    if block["type"] == "quote_line":
        # 去掉链接语法
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', block["text"])
        lines = wrap_text(text, fonts["body"], CONTENT_WIDTH, draw)
        return len(lines) * int(FONT_SIZE_BODY * 1.6)
    return 0


def _resolve_img_path(path_str, md_dir):
    """解析图片路径（相对于 md 文件目录）。"""
    if md_dir is None:
        return None
    p = Path(path_str)
    if not p.is_absolute():
        p = md_dir / p
    return p


def draw_block(block, fonts, draw, x, y, img_canvas=None, md_dir=None):
    """在指定位置绘制块，返回消耗的高度。"""
    if block["type"] == "spacer":
        return block["height"]

    if block["type"] == "separator":
        sep_y = y + FONT_SIZE_BODY
        draw.line([(x, sep_y), (x + CONTENT_WIDTH, sep_y)], fill=SEPARATOR_COLOR, width=2)
        return int(FONT_SIZE_BODY * 2)

    if block["type"] == "h2":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        lines = wrap_text(text, fonts["h2"], CONTENT_WIDTH, draw)
        line_h = int(FONT_SIZE_H2 * LINE_SPACING)
        for i, line in enumerate(lines):
            draw.text((x, y + i * line_h), line, font=fonts["h2"], fill=HEADING_COLOR)
        return len(lines) * line_h + 20

    if block["type"] == "h3":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        lines = wrap_text(text, fonts["bold"], CONTENT_WIDTH - 20, draw)
        line_h = int(FONT_SIZE_BODY * LINE_SPACING)
        total_h = len(lines) * line_h
        # 左侧竖线
        draw.rectangle([(x, y + 2), (x + 4, y + total_h - 2)], fill="#a0220d")
        for i, line in enumerate(lines):
            draw.text((x + 16, y + i * line_h), line, font=fonts["bold"], fill=HEADING_COLOR)
        return total_h + 16

    if block["type"] == "paragraph":
        segments = parse_inline_segments(block["text"])
        lines = wrap_rich_text(segments, fonts, CONTENT_WIDTH, draw)
        line_h = int(FONT_SIZE_BODY * LINE_SPACING)
        for i, line_segs in enumerate(lines):
            draw_rich_line(line_segs, fonts, draw, x, y + i * line_h)
        return len(lines) * line_h

    if block["type"] == "list_item":
        bullet_indent = 40
        bullet_y = y + int(FONT_SIZE_BODY * 0.45)
        draw.ellipse([(x + 8, bullet_y), (x + 20, bullet_y + 12)], fill=TEXT_COLOR)
        segments = parse_inline_segments(block["text"])
        lines = wrap_rich_text(segments, fonts, CONTENT_WIDTH - bullet_indent, draw)
        line_h = int(FONT_SIZE_BODY * LINE_SPACING)
        for i, line_segs in enumerate(lines):
            draw_rich_line(line_segs, fonts, draw, x + bullet_indent, y + i * line_h)
        return len(lines) * line_h

    if block["type"] == "image" and img_canvas is not None:
        img_path = _resolve_img_path(block["path"], md_dir)
        if img_path and img_path.exists():
            img = Image.open(img_path).convert("RGB")
            scale = CONTENT_WIDTH / img.width
            new_h = int(img.height * scale)
            img_resized = img.resize((CONTENT_WIDTH, new_h), Image.LANCZOS)
            img_canvas.paste(img_resized, (x, y + 15))
            return new_h + 30
        return 0

    if block["type"] == "table":
        rows = block["rows"]
        if not rows:
            return 0
        num_cols = max(len(r) for r in rows)
        col_w = CONTENT_WIDTH // max(num_cols, 1)
        row_h = int(FONT_SIZE_BODY * LINE_SPACING) + 10
        cy = y + 10
        for ri, row in enumerate(rows):
            # 计算本行最大行数
            max_lines = 1
            row_wrapped = []
            for ci, cell in enumerate(row[:num_cols]):
                cell_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell)
                font = fonts["bold"] if ri == 0 else fonts["body"]
                lines = wrap_text(cell_text, font, col_w - 16, draw)
                row_wrapped.append(lines)
                max_lines = max(max_lines, len(lines))
            # 绘制每个单元格的多行文本
            for ci, lines in enumerate(row_wrapped):
                cell_x = x + ci * col_w + 8
                font = fonts["bold"] if ri == 0 else fonts["body"]
                color = HEADING_COLOR if ri == 0 else TEXT_COLOR
                for li, line in enumerate(lines):
                    draw.text((cell_x, cy + li * row_h), line, font=font, fill=color)
            cell_h = max_lines * row_h
            # 行底线
            draw.line([(x, cy + cell_h - 5), (x + CONTENT_WIDTH, cy + cell_h - 5)], fill=SEPARATOR_COLOR, width=1)
            cy += cell_h
        return cy - y + 10

    if block["type"] == "code_block":
        code_text = block["text"]
        lang = block.get("lang", "")
        line_h = int(FONT_SIZE_BODY * 1.6)
        code_max_w = CONTENT_WIDTH - 40
        font = fonts["body"]
        lexer = _get_lexer(lang)

        # 将 tokens 按行分组，每行是 [(text, color), ...] 的列表
        code_lines_tokens = [[]]
        for ttype, value in lex(code_text, lexer):
            color = _token_color(ttype)
            parts = value.split('\n')
            for pi, part in enumerate(parts):
                if pi > 0:
                    code_lines_tokens.append([])
                if part:
                    code_lines_tokens[-1].append((part, color))

        # 对每行做 word-wrap，得到渲染行列表 [(text, color), ...]
        render_lines = []
        for line_tokens in code_lines_tokens:
            if not line_tokens:
                render_lines.append([])
                continue
            current_line = []
            current_width = 0
            for text, color in line_tokens:
                i = 0
                while i < len(text):
                    if _is_latin(text[i]):
                        word = ""
                        while i < len(text) and _is_latin(text[i]):
                            word += text[i]
                            i += 1
                    else:
                        word = text[i]
                        i += 1
                    bbox = draw.textbbox((0, 0), word, font=font)
                    word_w = bbox[2] - bbox[0]
                    if current_width + word_w > code_max_w and current_line:
                        render_lines.append(current_line)
                        current_line = []
                        current_width = 0
                    if current_line and current_line[-1][1] == color:
                        current_line[-1] = (current_line[-1][0] + word, color)
                    else:
                        current_line.append((word, color))
                    current_width += word_w
            render_lines.append(current_line)

        total_h = len(render_lines) * line_h + 40
        # 背景
        draw.rectangle([(x, y), (x + CONTENT_WIDTH, y + total_h)], fill="#282c34")
        cy = y + 20
        for line_segs in render_lines:
            cx = x + 20
            for seg_text, seg_color in line_segs:
                draw.text((cx, cy), seg_text, font=font, fill=seg_color)
                bbox = draw.textbbox((0, 0), seg_text, font=font)
                cx += bbox[2] - bbox[0]
            cy += line_h
        return total_h

    if block["type"] == "quote_line":
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', block["text"])
        lines = wrap_text(text, fonts["body"], CONTENT_WIDTH, draw)
        line_h = int(FONT_SIZE_BODY * 1.6)
        for i, line in enumerate(lines):
            draw.text((x, y + i * line_h), line, font=fonts["body"], fill="#888")
        return len(lines) * line_h

    return 0


def paginate_blocks(blocks, fonts, md_dir=None):
    """将块分配到页面，确保不超出页面高度。标题尽量和后续内容同页。"""
    tmp_img = Image.new("RGB", (WIDTH, HEIGHT))
    tmp_draw = ImageDraw.Draw(tmp_img)

    max_content_height = HEIGHT - 2 * PADDING_Y
    pages = []
    current_page = []
    current_height = 0

    i = 0
    while i < len(blocks):
        block = blocks[i]
        h = estimate_block_height(block, fonts, tmp_draw, md_dir)

        # 如果是标题，尝试和下一个非spacer块绑定
        if block["type"] == "h2" and i + 1 < len(blocks):
            # 找到标题后的第一个内容块
            next_idx = i + 1
            while next_idx < len(blocks) and blocks[next_idx]["type"] == "spacer":
                next_idx += 1
            if next_idx < len(blocks):
                # 计算标题+中间spacer+下一块的总高度
                group_h = h
                for j in range(i + 1, next_idx + 1):
                    group_h += estimate_block_height(blocks[j], fonts, tmp_draw, md_dir)
                # 如果当前页放不下这个组合，但新页能放下，就翻页
                if current_height + group_h > max_content_height and group_h <= max_content_height and current_page:
                    pages.append(current_page)
                    current_page = []
                    current_height = 0

        if current_height + h > max_content_height and current_page:
            pages.append(current_page)
            current_page = []
            current_height = 0
        current_page.append(block)
        current_height += h
        i += 1

    if current_page:
        pages.append(current_page)

    return pages


def render_page(blocks, fonts, page_num, total_pages, md_dir=None):
    """渲染单页为 PIL Image。"""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    y = PADDING_Y
    for block in blocks:
        h = draw_block(block, fonts, draw, PADDING_X, y, img_canvas=img, md_dir=md_dir)
        y += h

    # 页码
    page_text = f"{page_num}/{total_pages}"
    bbox = draw.textbbox((0, 0), page_text, font=fonts["body"])
    pw = bbox[2] - bbox[0]
    draw.text((WIDTH - PADDING_X - pw, HEIGHT - PADDING_Y + 20), page_text,
              font=fonts["body"], fill="#999")

    return img


def render_md_to_images(md_path, output_dir):
    """主入口：读取Markdown，渲染为图片序列。"""
    md_path = Path(md_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    md_dir = md_path.parent
    md_text = md_path.read_text(encoding="utf-8")
    blocks = parse_md_to_blocks(md_text)
    fonts = get_fonts()
    pages = paginate_blocks(blocks, fonts, md_dir)

    for i, page_blocks in enumerate(pages, 1):
        img = render_page(page_blocks, fonts, i, len(pages), md_dir)
        img.save(output_dir / f"{i:02d}.png", "PNG")
        print(f"已生成: {output_dir / f'{i:02d}.png'}")

    print(f"共 {len(pages)} 张图片")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <input.md> <output_dir/>")
        sys.exit(1)
    render_md_to_images(sys.argv[1], sys.argv[2])
