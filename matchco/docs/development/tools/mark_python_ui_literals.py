#!/usr/bin/env python3
"""Mark literal Django form labels, help text, choice labels and UI errors.

This conservative AST-based migration only wraps static string literals in
known user-facing Python contexts. It does not touch migrations, tests, seeds,
dynamic content or arbitrary strings.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4] / 'matchco'
EXCLUDED = {'.git', '.venv', 'archive', 'archives', 'migrations', 'node_modules', 'static', 'staticfiles', 'tests', 'vendor'}
FIELD_TEXT = {'label', 'help_text', 'verbose_name', 'verbose_name_plural'}
MESSAGE_CALLS = {'ValidationError', 'success', 'error', 'warning', 'info', 'add_error', 'add_message'}


class LiteralCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.nodes: set[ast.Constant] = set()

    def add_string(self, node: ast.AST) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
            self.nodes.add(node)

    def add_choice_labels(self, node: ast.AST) -> None:
        if not isinstance(node, (ast.List, ast.Tuple)):
            return
        for item in node.elts:
            if isinstance(item, (ast.List, ast.Tuple)) and len(item.elts) == 2:
                self.add_string(item.elts[1])
            elif isinstance(item, (ast.List, ast.Tuple)):
                self.add_choice_labels(item)

    def visit_Call(self, node: ast.Call) -> None:
        name = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else ''
        )
        for keyword in node.keywords:
            if keyword.arg in FIELD_TEXT and (keyword.arg != 'label' or name.endswith('Field')):
                self.add_string(keyword.value)
            elif keyword.arg == 'choices':
                self.add_choice_labels(keyword.value)
        if name in MESSAGE_CALLS:
            message_index = 1 if name in {'success', 'error', 'warning', 'info', 'add_error'} else (
                2 if name == 'add_message' else 0
            )
            if len(node.args) > message_index:
                self.add_string(node.args[message_index])
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            name = target.id if isinstance(target, ast.Name) else (
                target.attr if isinstance(target, ast.Attribute) else ''
            )
            if name in FIELD_TEXT:
                self.add_string(node.value)
            if isinstance(target, ast.Name) and name.endswith('_CHOICES'):
                self.add_choice_labels(node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target = node.target
        name = target.id if isinstance(target, ast.Name) else ''
        if node.value is not None and name in FIELD_TEXT:
            self.add_string(node.value)
        if node.value is not None and name.endswith('_CHOICES'):
            self.add_choice_labels(node.value)
        self.generic_visit(node)


def translation_alias(tree: ast.Module) -> str | None:
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'django.utils.translation':
            for alias in node.names:
                if alias.name == 'gettext_lazy':
                    return alias.asname or alias.name
    return None


def import_insertion(tree: ast.Module, source: str) -> int:
    lines = source.splitlines(keepends=True)
    insert_after = 0
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and insert_after == 0:
            insert_after = node.end_lineno or node.lineno
        elif isinstance(node, ast.ImportFrom) and node.module == '__future__':
            insert_after = node.end_lineno or node.lineno
        else:
            break
    return sum(len(line) for line in lines[:insert_after])


def transform(path: Path, source: str) -> tuple[str, int]:
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return source, 0
    normalized_alias = False
    occupied = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    if 'gettext_lazy' not in occupied:
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == 'django.utils.translation':
                if any(alias.name == 'gettext_lazy' and alias.asname == '_l10n' for alias in node.names):
                    source = source.replace('gettext_lazy as _l10n', 'gettext_lazy as gettext_lazy')
                    source = source.replace('_l10n(', 'gettext_lazy(')
                    tree = ast.parse(source, filename=str(path))
                    normalized_alias = True
                    break
    collector = LiteralCollector()
    collector.visit(tree)
    if not collector.nodes:
        return source, int(normalized_alias)
    alias = translation_alias(tree)
    add_import = alias is None
    if add_import:
        occupied = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        alias = '_' if '_' not in occupied else 'gettext_lazy'
        if alias == 'gettext_lazy' and alias in occupied:
            alias = '_l10n'
    assert alias
    encoded = source.encode('utf-8')
    edits: list[tuple[int, int, bytes]] = []
    for node in collector.nodes:
        start = sum(len(line.encode('utf-8')) for line in source.splitlines(keepends=True)[:node.lineno - 1]) + node.col_offset
        end = sum(len(line.encode('utf-8')) for line in source.splitlines(keepends=True)[:node.end_lineno - 1]) + node.end_col_offset
        original = encoded[start:end]
        edits.append((start, end, alias.encode() + b'(' + original + b')'))
    for start, end, replacement in sorted(edits, reverse=True):
        encoded = encoded[:start] + replacement + encoded[end:]
    updated = encoded.decode('utf-8')
    if add_import:
        position = import_insertion(tree, source)
        separator = '' if position == 0 else '\n'
        updated = updated[:position] + f'{separator}from django.utils.translation import gettext_lazy as {alias}\n' + updated[position:]
    return updated, len(edits) + int(normalized_alias)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', help='limita a caminhos relativos à raiz Django')
    parser.add_argument('--check', action='store_true', help='não grava; apenas conta o que seria marcado')
    args = parser.parse_args()
    prefix = args.path.strip('/') if args.path else None
    files = sorted(path for path in ROOT.rglob('*.py')
                   if path.name != Path(__file__).name
                   and not any(part in EXCLUDED for part in path.parts)
                   and (prefix is None or prefix in path.relative_to(ROOT).as_posix()))
    changed = count = 0
    for path in files:
        source = path.read_text(encoding='utf-8', errors='replace')
        updated, added = transform(path, source)
        if added:
            changed += 1
            count += added
            if not args.check:
                path.write_text(updated, encoding='utf-8')
    print(f'{changed} arquivos Python; {count} literais de interface ' + ('seriam marcados.' if args.check else 'marcados.'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
