#!/usr/bin/env python3
"""Mark static user-facing HTML template text with Django gettext tags.

This bulk migration preserves template markup and dynamic expressions. It is
limited to visible text nodes, accessible presentation attributes and simple
JavaScript UI strings; authored content rendered from context is never changed.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4] / 'matchco'
EXCLUDED = {'.git', '.venv', 'archive', 'archives', 'migrations', 'node_modules', 'static', 'staticfiles', 'tests', 'vendor'}
TEMPLATE_TOKEN = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.DOTALL)
MARKUP_TOKEN = re.compile(r'<!--.*?-->|<![^>]*>|</?[A-Za-z][^>]*>', re.DOTALL)
ATTR_START_RE = re.compile(r'\b(?P<name>alt|aria-description|aria-label|placeholder|title|value)\s*=\s*(?P<quote>["\'])', re.IGNORECASE)
JS_UI_STRING_RE = re.compile(
    r'(?P<prefix>\b(?:confirm|alert|prompt)\s*\(\s*|\.\s*(?:textContent|innerText|placeholder)\s*=\s*|\.\s*setCustomValidity\s*\(\s*)'
    r'(?P<quote>["\'])(?P<message>(?:\\.|(?!\2).)*)(?P=quote)',
    re.DOTALL,
)
IGNORED = {'code', 'pre', 'script', 'style', 'svg', 'noscript'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def quote_for_template(value: str) -> str:
    # Django's template lexer accepts escaped quotes in string literals.
    value = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    return f'{{% trans "{value}" %}}'


def mark_text(value: str) -> tuple[str, int]:
    decoded = html.unescape(value)
    match = re.match(r'^(\s*)(.*?)(\s*)$', decoded, re.DOTALL)
    assert match
    leading, literal, trailing = match.groups()
    if len(literal) < 2 or not any(char.isalpha() for char in literal):
        return value, 0
    return leading + quote_for_template(literal) + trailing, 1


def mark_js_ui_strings(source: str) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        message = match.group('message')
        if not any(char.isalpha() for char in message) or any(token in message for token in ('{%', '{{', '{#')) or '\\' in message:
            return match.group(0)
        count += 1
        trans_tag = quote_for_template(message)
        return f"{match.group('prefix')}{match.group('quote')}{{% filter escapejs %}}{trans_tag}{{% endfilter %}}{match.group('quote')}"

    return JS_UI_STRING_RE.sub(replace, source), count


def mark_mixed_template_value(value: str) -> tuple[str, int]:
    """Mark static fragments in an accessible attribute around dynamic values."""
    parts: list[str] = []
    cursor = 0
    count = 0
    for match in TEMPLATE_TOKEN.finditer(value):
        literal = value[cursor:match.start()]
        marked, added = mark_text(literal)
        parts.append(marked)
        count += added
        parts.append(match.group(0))
        cursor = match.end()
    marked, added = mark_text(value[cursor:])
    parts.append(marked)
    count += added
    return ''.join(parts), count


def next_token(source: str, cursor: int) -> tuple[int, int] | None:
    starts = [(source.find(marker, cursor), marker) for marker in ('<', '{%', '{{', '{#')]
    starts = [(pos, marker) for pos, marker in starts if pos >= 0]
    if not starts:
        return None
    start, marker = min(starts)
    if marker == '{%':
        end = source.find('%}', start + 2)
        return (start, end + 2) if end >= 0 else None
    if marker == '{{':
        end = source.find('}}', start + 2)
        return (start, end + 2) if end >= 0 else None
    if marker == '{#':
        end = source.find('#}', start + 2)
        return (start, end + 2) if end >= 0 else None
    if source.startswith('<!--', start):
        end = source.find('-->', start + 4)
        return (start, end + 3) if end >= 0 else None
    if re.match(r'<![^>]*>', source[start:]):
        end = source.find('>', start + 2)
        return (start, end + 1) if end >= 0 else None
    if not re.match(r'</?[A-Za-z]', source[start:]):
        return next_token(source, start + 1)
    quote = ''
    index = start + 1
    while index < len(source):
        if source.startswith('{%', index):
            end = source.find('%}', index + 2)
            if end < 0:
                break
            index = end + 2
            continue
        if source.startswith('{{', index):
            end = source.find('}}', index + 2)
            if end < 0:
                break
            index = end + 2
            continue
        char = source[index]
        if quote:
            if char == quote:
                quote = ''
        elif char in {'"', "'"}:
            quote = char
        elif char == '>':
            return start, index + 1
        index += 1
    return None


def mark_tag_attributes(token: str, tag_name: str) -> tuple[str, int]:
    parts: list[str] = []
    cursor = 0
    count = 0
    for match in ATTR_START_RE.finditer(token):
        if match.start() < cursor:
            continue
        quote = match.group('quote')
        value_start = match.end()
        index = value_start
        while index < len(token):
            if token.startswith('{%', index):
                end = token.find('%}', index + 2)
                if end >= 0:
                    index = end + 2
                    continue
            if token.startswith('{{', index):
                end = token.find('}}', index + 2)
                if end >= 0:
                    index = end + 2
                    continue
            if token.startswith('{#', index):
                end = token.find('#}', index + 2)
                if end >= 0:
                    index = end + 2
                    continue
            if token[index] == quote:
                break
            index += 1
        if index >= len(token):
            continue
        attr_name = match.group('name').lower()
        is_ui_value = attr_name != 'value' or (
            tag_name == 'input' and re.search(r'\btype\s*=\s*["\']?(?:submit|button|reset)\b', token, re.IGNORECASE)
        )
        value = token[value_start:index]
        replacement = value
        if is_ui_value and any(char.isalpha() for char in html.unescape(value)):
            replacement, added = mark_mixed_template_value(value)
            count += added
        parts.extend((token[cursor:value_start], replacement, quote))
        cursor = index + 1
    parts.append(token[cursor:])
    return ''.join(parts), count


def mark_template(source: str) -> tuple[str, int]:
    source, marked_js = mark_js_ui_strings(source)
    # Repair attributes partially re-wrapped by the first bulk pass, whose
    # lexer treated a Django tag inside a quoted attribute as HTML text.
    source, repaired = re.subn(
        r'\{%\s*trans\s+["\']\{%\s*trans\s*["\']\s*%\}\s+["\']([^"\']*)["\']\s*%\}',
        lambda match: quote_for_template(match.group(1)),
        source,
    )
    parts: list[str] = []
    cursor = 0
    in_blocktrans = False
    ignored_stack: list[str] = []
    count = repaired + marked_js

    while (token_span := next_token(source, cursor)) is not None:
        token_start, token_end = token_span
        text = source[cursor:token_start]
        if text and not in_blocktrans and not ignored_stack:
            marked, added = mark_text(text)
            parts.append(marked)
            count += added
        else:
            parts.append(text)

        token = source[token_start:token_end]
        if token.startswith('{%'):
            tag = token[2:-2].strip().split(None, 1)[0] if token[2:-2].strip() else ''
            if tag == 'blocktrans':
                in_blocktrans = True
            elif tag == 'endblocktrans':
                in_blocktrans = False
        elif token.startswith('<') and not token.startswith('<!--') and not token.startswith('<!'):
            closing = token.startswith('</')
            tag_match = re.match(r'</?\s*([A-Za-z][\w:-]*)', token)
            tag_name = tag_match.group(1).lower() if tag_match else ''
            if not closing and not ignored_stack:
                token, added = mark_tag_attributes(token, tag_name)
                count += added
            if closing:
                for index in range(len(ignored_stack) - 1, -1, -1):
                    if ignored_stack[index] == tag_name:
                        del ignored_stack[index:]
                        break
            elif tag_name in IGNORED and not token.rstrip().endswith('/>'):
                ignored_stack.append(tag_name)

        parts.append(token)
        cursor = token_end

    tail = source[cursor:]
    if tail and not in_blocktrans and not ignored_stack:
        marked, added = mark_text(tail)
        parts.append(marked)
        count += added
    else:
        parts.append(tail)
    result = ''.join(parts)
    if count and not re.search(r'{%\s*load\s+i18n\s*%}', result):
        extends = re.search(r'{%\s*extends\b.*?%}', result)
        insertion = extends.end() if extends else 0
        result = result[:insertion] + '\n{% load i18n %}' + result[insertion:]
    return result, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', help='limita a caminhos relativos à raiz Django')
    parser.add_argument('--check', action='store_true', help='mostra quantos arquivos/textos seriam alterados')
    args = parser.parse_args()
    prefix = args.path.strip('/') if args.path else None
    files = sorted(path for path in ROOT.rglob('templates/**/*.html')
                   if not any(part in EXCLUDED for part in path.parts)
                   and (prefix is None or prefix in path.relative_to(ROOT).as_posix()))
    changed_files = marked_strings = 0
    for path in files:
        original = path.read_text(encoding='utf-8', errors='replace')
        updated, count = mark_template(original)
        if count:
            changed_files += 1
            marked_strings += count
            if not args.check:
                path.write_text(updated, encoding='utf-8')
    verb = 'seriam marcados' if args.check else 'marcados'
    print(f'{changed_files} templates; {marked_strings} literais {verb}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
