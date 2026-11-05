"""Minimal markdown -> HTML for the explorer tabs.

Deliberately dependency-free: the build must not require a pip install into an
environment that may be running the grid. Handles exactly what MODEL.md and
GLOSSARY.md use: headings, tables, blockquotes, fenced/inline code, bold,
italics, links, ordered and unordered lists, horizontal rules, paragraphs.
"""
import re, html as _html


def _inline(s):
    s = _html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def _table(rows):
    def cells(line):
        return [c.strip() for c in line.strip().strip('|').split('|')]
    head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
    out = ['<table><thead><tr>'] + [f'<th>{_inline(c)}</th>' for c in head] + ['</tr></thead><tbody>']
    for r in body:
        out.append('<tr>' + ''.join(f'<td>{_inline(c)}</td>' for c in r) + '</tr>')
    out.append('</tbody></table>')
    return ''.join(out)


def render(src):
    lines = src.split('\n')
    out, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        if ln.startswith('```'):
            j = i + 1
            buf = []
            while j < n and not lines[j].startswith('```'):
                buf.append(lines[j]); j += 1
            out.append('<pre><code>' + _html.escape('\n'.join(buf)) + '</code></pre>')
            i = j + 1; continue
        if re.match(r'^\s*\|.*\|\s*$', ln) and i + 1 < n and re.match(r'^\s*\|[\s:\-|]+\|\s*$', lines[i+1]):
            j = i
            while j < n and re.match(r'^\s*\|.*\|\s*$', lines[j]):
                j += 1
            out.append(_table(lines[i:j])); i = j; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', ln)
        if m:
            lv = len(m.group(1)); out.append(f'<h{lv}>{_inline(m.group(2))}</h{lv}>'); i += 1; continue
        if ln.startswith('> '):
            buf = []
            while i < n and lines[i].startswith('> '):
                buf.append(lines[i][2:]); i += 1
            out.append('<blockquote>' + _inline(' '.join(buf)) + '</blockquote>'); continue
        if re.match(r'^(-{3,}|\*{3,})\s*$', ln):
            out.append('<hr>'); i += 1; continue
        if re.match(r'^\s*\d+\.\s+', ln):
            buf = []
            while i < n and re.match(r'^\s*\d+\.\s+', lines[i]):
                item = re.sub(r'^\s*\d+\.\s+', '', lines[i]); i += 1
                while i < n and lines[i].startswith('   ') and lines[i].strip():
                    item += ' ' + lines[i].strip(); i += 1
                buf.append(f'<li>{_inline(item)}</li>')
            out.append('<ol>' + ''.join(buf) + '</ol>'); continue
        if re.match(r'^\s*[-*]\s+', ln):
            buf = []
            while i < n and re.match(r'^\s*[-*]\s+', lines[i]):
                item = re.sub(r'^\s*[-*]\s+', '', lines[i]); i += 1
                while i < n and lines[i].startswith('  ') and lines[i].strip():
                    item += ' ' + lines[i].strip(); i += 1
                buf.append(f'<li>{_inline(item)}</li>')
            out.append('<ul>' + ''.join(buf) + '</ul>'); continue
        if not ln.strip():
            i += 1; continue
        buf = []
        while i < n and lines[i].strip() and not re.match(r'^(#{1,6}\s|>\s|\s*[-*]\s|\s*\d+\.\s|\|)', lines[i]) \
              and not lines[i].startswith('```'):
            buf.append(lines[i]); i += 1
        out.append('<p>' + _inline(' '.join(buf)) + '</p>')
    return '\n'.join(out)
