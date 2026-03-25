#!/usr/bin/env python3
"""Scan .py files for Band IV/V style violations (line length > 30 or nesting depth > 2)."""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIR_NAMES = {
    "venv", ".git", "__pycache__", "node_modules", "dist", "build",
    "coverage", "lcov-report", ".cursor", "staticfiles", "migrations",
    "scripts",  # scanner tooling, not app code
}


class DepthVisitor(ast.NodeVisitor):
    def __init__(self):
        self.d = 0
        self.m = 0

    def _e(self, n):
        self.d += 1
        self.m = max(self.m, self.d)
        self.generic_visit(n)
        self.d -= 1

    visit_If = visit_For = visit_While = visit_With = visit_Try = visit_Match = _e
    visit_ExceptHandler = _e


def scan_file(path: Path):
    viol = []
    try:
        t = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return viol
    for node in ast.walk(t):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ln = (getattr(node, "end_lineno", node.lineno) or node.lineno) - node.lineno + 1
            v = DepthVisitor()
            v.visit(node)
            if ln > 30 or v.m > 2:
                viol.append((node.name, ln, v.m))
    return viol


def should_skip(p: Path) -> bool:
    if not p.is_file() or p.suffix != ".py":
        return True
    for part in p.parts:
        if part in EXCLUDE_DIR_NAMES:
            return True
    return False


def main():
    viol_by_file = {}
    for p in ROOT.rglob("*.py"):
        if should_skip(p):
            continue
        v = scan_file(p)
        if v:
            viol_by_file[str(p.relative_to(ROOT))] = v
    for f in sorted(viol_by_file):
        print(f)
    return len(viol_by_file)


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
