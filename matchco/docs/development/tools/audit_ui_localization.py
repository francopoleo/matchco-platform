#!/usr/bin/env python3
"""Deterministic, no-LLM audit of Django UI translation readiness.

Checks HTML templates for visible literals outside Django translation tags,
collects gettext calls from Python source, and compares marked strings against
the project's pt_BR catalogs. It reports findings only; it never edits files.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
DJANGO_ROOT = REPO_ROOT / 'matchco'
EXCLUDED_PARTS = {
    '.git', '.venv', 'archive', 'archives', 'migrations', 'node_modules',
    'static', 'staticfiles', 'tests', 'vendor', 'docs',
}
DJANGO_TOKEN_RE = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.DOTALL)
BLOCKTRANS_RE = re.compile(r'\{%\s*blocktrans\b.*?%\}.*?\{%\s*endblocktrans\s*%\}', re.DOTALL)
TRANS_RE = re.compile(r"\{%\s*trans\s+(['\"])(.*?)\1(?:\s+noop)?\s*%\}", re.DOTALL)
GETTEXT_NAMES = {'_', 'gettext', 'gettext_lazy', 'gettext_noop', 'pgettext', 'ngettext', 'npgettext'}
VISIBLE_ATTRIBUTES = {'alt', 'aria-description', 'aria-label', 'placeholder', 'title'}
IGNORED_ELEMENTS = {'code', 'pre', 'script', 'style', 'svg', 'noscript'}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    text: str


def is_scannable(path: Path) -> bool:
    return not any(part in EXCLUDED_PARTS for part in path.parts)


def normalize_text(value: str) -> str:
    value = DJANGO_TOKEN_RE.sub(' ', value)
    return re.sub(r'\s+', ' ', value).strip()


def is_meaningful_text(value: str) -> bool:
    value = normalize_text(value)
    if re.fullmatch(r'v\s*(?:—|·)?', value, re.IGNORECASE):
        return False  # Standard version prefix, not a translatable word.
    return len(value) >= 2 and any(char.isalpha() for char in value)


class TemplateLiteralScanner(HTMLParser):
    def __init__(self, path: Path, root: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.root = root
        self.ignored_depth = 0
        self.ignored_stack: list[str] = []
        self.findings: list[Finding] = []

    def _add(self, value: str, line: int) -> None:
        text = normalize_text(value)
        if is_meaningful_text(text):
            self.findings.append(Finding(self.path.relative_to(self.root).as_posix(), line, text))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_values = dict(attrs)
        if tag in IGNORED_ELEMENTS or attr_values.get('aria-hidden', '').lower() == 'true':
            self.ignored_depth += 1
            self.ignored_stack.append(tag)
        if not self.ignored_depth:
            line = self.getpos()[0]
            visible_attributes = set(VISIBLE_ATTRIBUTES)
            if tag == 'input' and attr_values.get('type') in {'submit', 'button', 'reset'}:
                visible_attributes.add('value')
            for name, value in attrs:
                if name in visible_attributes and value:
                    self._add(value, line)

    def handle_endtag(self, tag: str) -> None:
        if self.ignored_stack and tag == self.ignored_stack[-1]:
            self.ignored_stack.pop()
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self._add(data, self.getpos()[0])


def template_findings(path: Path, root: Path) -> list[Finding]:
    source = path.read_text(encoding='utf-8', errors='replace')
    # Content inside blocktrans is already marked. Remove it before parsing;
    # remaining Django tokens are removed so a trans tag inside a quoted HTML
    # attribute cannot confuse HTMLParser's markup structure.
    source = BLOCKTRANS_RE.sub(' ', source)
    source = DJANGO_TOKEN_RE.sub(lambda match: '\n' * match.group(0).count('\n'), source)
    scanner = TemplateLiteralScanner(path, root)
    try:
        scanner.feed(source)
        scanner.close()
    except Exception as exc:  # malformed HTML still yields useful partial results
        scanner.findings.append(Finding(path.relative_to(root).as_posix(), 1, f'[erro de leitura HTML: {exc}]'))
    return scanner.findings


class GettextCallScanner(ast.NodeVisitor):
    def __init__(self, path: Path, root: Path):
        self.path = path
        self.root = root
        self.messages: list[tuple[str, Finding]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else ''
        )
        if func_name in GETTEXT_NAMES and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                message = arg.value
                self.messages.append((message, Finding(
                    self.path.relative_to(self.root).as_posix(), node.lineno, message,
                )))
        self.generic_visit(node)


def python_gettext_messages(path: Path, root: Path) -> list[tuple[str, Finding]]:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []
    scanner = GettextCallScanner(path, root)
    scanner.visit(tree)
    return scanner.messages


def _po_unquote(raw: str) -> str:
    try:
        value = ast.literal_eval(raw)
        return value if isinstance(value, str) else ''
    except (SyntaxError, ValueError):
        return ''


def parse_po(path: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    entry: dict[str, object] = {'msgid': '', 'msgstr': {}, 'fuzzy': False}
    active_field: str | None = None

    def finish() -> None:
        nonlocal entry, active_field
        if entry.get('msgid'):
            entries.append(entry)
        entry = {'msgid': '', 'msgstr': {}, 'fuzzy': False}
        active_field = None

    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        stripped = line.strip()
        if not stripped:
            finish()
            continue
        if stripped.startswith('#'):
            if stripped.startswith('#,') and 'fuzzy' in stripped:
                entry['fuzzy'] = True
            continue
        if stripped.startswith('msgid_plural '):
            active_field = None
            continue
        match = re.match(r'^(msgid|msgstr)(?:\[(\d+)\])?\s+(".*")$', stripped)
        if match:
            field, plural_index, raw = match.groups()
            value = _po_unquote(raw)
            key = f'msgstr[{plural_index}]' if field == 'msgstr' and plural_index else field
            if field == 'msgstr':
                msgstr = entry['msgstr']
                assert isinstance(msgstr, dict)
                msgstr[key] = value
            else:
                entry[field] = value
            active_field = key
            continue
        if stripped.startswith('"') and active_field:
            value = _po_unquote(stripped)
            if active_field == 'msgid':
                entry['msgid'] = str(entry['msgid']) + value
            else:
                msgstr = entry['msgstr']
                assert isinstance(msgstr, dict)
                msgstr[active_field] = str(msgstr.get(active_field, '')) + value
    finish()
    return entries


def load_catalogs(root: Path) -> tuple[dict[str, bool], list[dict[str, object]], int]:
    """Return msgid -> translated, raw untranslated entries, catalog count."""
    catalog_files = [p for p in root.rglob('*.po') if 'pt_BR' in p.parts and is_scannable(p)]
    coverage: dict[str, bool] = {}
    untranslated: list[dict[str, object]] = []
    for path in sorted(catalog_files):
        for entry in parse_po(path):
            msgid = str(entry['msgid'])
            translations = entry['msgstr']
            assert isinstance(translations, dict)
            translated = bool(translations) and all(bool(v.strip()) for v in translations.values()) and not entry['fuzzy']
            coverage[msgid] = coverage.get(msgid, False) or translated
            if not translated:
                untranslated.append({
                    'path': path.relative_to(root).as_posix(),
                    'msgid': msgid,
                    'fuzzy': bool(entry['fuzzy']),
                })
    return coverage, untranslated, len(catalog_files)


def discover_files(root: Path) -> tuple[list[Path], list[Path]]:
    html_files = sorted(
        path for path in root.rglob('templates/**/*.html')
        if is_scannable(path)
    )
    python_files = sorted(
        path for path in root.rglob('*.py')
        if is_scannable(path)
        and not any(part in {'management', 'commands'} for part in path.parts)
    )
    return html_files, python_files


def build_report(root: Path) -> dict[str, object]:
    html_files, python_files = discover_files(root)
    unmarked: list[Finding] = []
    marked_template_messages: dict[str, Finding] = {}
    for path in html_files:
        unmarked.extend(template_findings(path, root))
        source = path.read_text(encoding='utf-8', errors='replace')
        for match in TRANS_RE.finditer(source):
            message = match.group(2)
            marked_template_messages.setdefault(message, Finding(
                path.relative_to(root).as_posix(), source.count('\n', 0, match.start()) + 1, message,
            ))

    python_messages: dict[str, Finding] = {}
    for path in python_files:
        for message, finding in python_gettext_messages(path, root):
            python_messages.setdefault(message, finding)

    catalog_coverage, untranslated_entries, catalog_count = load_catalogs(root)
    marked_messages = {**python_messages, **marked_template_messages}
    missing_catalog_messages = [
        finding for message, finding in marked_messages.items()
        if not catalog_coverage.get(message, False)
    ]
    by_template = Counter(finding.path for finding in unmarked)
    return {
        'root': str(root),
        'templates_scanned': len(html_files),
        'python_files_scanned': len(python_files),
        'pt_br_catalogs_scanned': catalog_count,
        'gettext_messages_found': len(marked_messages),
        'unmarked_visible_literals': len(unmarked),
        'marked_messages_missing_pt_br_catalog_entry_or_translation': len(missing_catalog_messages),
        'untranslated_pt_br_catalog_entries': len(untranslated_entries),
        'top_templates_with_unmarked_literals': by_template.most_common(20),
        'unmarked_examples': [asdict(finding) for finding in unmarked],
        'missing_catalog_examples': [asdict(finding) for finding in missing_catalog_messages],
        'untranslated_catalog_examples': untranslated_entries,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DJANGO_ROOT, help='raiz do projeto Django')
    parser.add_argument('--json', action='store_true', help='imprime o relatório completo em JSON')
    parser.add_argument('--path', help='limita a auditoria a um caminho relativo à raiz Django')
    parser.add_argument('--output', type=Path, help='grava o JSON completo neste arquivo, sem despejá-lo no terminal')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report = build_report(root)
    if args.path:
        prefix = args.path.strip('/')
        scoped_templates = [p for p in root.rglob('templates/**/*.html') if is_scannable(p) and prefix in p.relative_to(root).as_posix()]
        scoped_python = [p for p in root.rglob('*.py') if is_scannable(p) and prefix in p.relative_to(root).as_posix()]
        for key in ('unmarked_examples', 'missing_catalog_examples', 'untranslated_catalog_examples'):
            report[key] = [item for item in report[key] if item['path'].startswith(prefix)]
        report['scope'] = prefix
        report['templates_scanned'] = len(scoped_templates)
        report['python_files_scanned'] = len(scoped_python)
        report['unmarked_visible_literals'] = len(report['unmarked_examples'])
        report['marked_messages_missing_pt_br_catalog_entry_or_translation'] = len(report['missing_catalog_examples'])
        report['untranslated_pt_br_catalog_entries'] = len(report['untranslated_catalog_examples'])
        counts = Counter(item['path'] for item in report['unmarked_examples'])
        report['top_templates_with_unmarked_literals'] = counts.most_common(20)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.json:
        if not args.output:
            print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.output:
        print(f"Auditoria salva em {args.output}")
        print(f"Textos sem marcação: {report['unmarked_visible_literals']}; mensagens sem cobertura pt_BR: {report['marked_messages_missing_pt_br_catalog_entry_or_translation']}; entradas vazias/fuzzy: {report['untranslated_pt_br_catalog_entries']}")
    else:
        print('Auditoria determinística de idioma MatchCo (sem LLM)')
        print(f"Templates HTML: {report['templates_scanned']}")
        print(f"Arquivos Python: {report['python_files_scanned']}")
        print(f"Catálogos pt_BR: {report['pt_br_catalogs_scanned']}")
        print(f"Mensagens gettext: {report['gettext_messages_found']}")
        print(f"Textos visíveis sem marcação: {report['unmarked_visible_literals']}")
        print(f"Mensagens marcadas sem tradução/catálogo pt_BR: {report['marked_messages_missing_pt_br_catalog_entry_or_translation']}")
        print(f"Entradas pt_BR vazias ou fuzzy: {report['untranslated_pt_br_catalog_entries']}")
        print('\nTemplates com mais textos sem marcação:')
        for path, count in report['top_templates_with_unmarked_literals']:
            print(f'  {count:4}  {path}')
        print('\nExemplos de textos visíveis sem marcação (até 30):')
        for finding in report['unmarked_examples'][:30]:
            print(f"  {finding['path']}:{finding['line']}: {finding['text']}")
        print('\nExemplos de mensagens marcadas sem cobertura pt_BR:')
        for finding in report['missing_catalog_examples'][:30]:
            print(f"  {finding['path']}:{finding['line']}: {finding['text']}")
    return 1 if report['unmarked_visible_literals'] or report['marked_messages_missing_pt_br_catalog_entry_or_translation'] else 0


if __name__ == '__main__':
    sys.exit(main())
