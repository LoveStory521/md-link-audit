"""Offline audit of local Markdown file links. Python 3.10+, no dependencies."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__'}
LINK = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+["\'][^\n]*?["\'])?\s*\)')
REFERENCE = re.compile(r'^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)', re.M)


def mask_code(text):
    """Keep offsets stable while ignoring fenced and inline code and comments."""
    text = re.sub(r'<!--[\s\S]*?-->', lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text)
    lines = text.splitlines(keepends=True)
    fence = None
    for i, line in enumerate(lines):
        match = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if fence:
            close = re.match(r'^\s{0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$', line.rstrip('\n'))
            lines[i] = '\n' if line.endswith('\n') else ''
            if close:
                fence = None
        elif match:
            fence = match[1]
            lines[i] = '\n' if line.endswith('\n') else ''
    return re.sub(r'(`+).*?\1', lambda m: ' ' * len(m[0]), ''.join(lines))


def audit(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('Scan root must be an existing directory')
    issues, checked, skipped = [], 0, 0
    for source in sorted(root.rglob('*')):
        if any(p in SKIP_DIRS for p in source.relative_to(root).parts) or source.suffix.lower() not in {'.md', '.markdown'}:
            continue
        if source.is_symlink() or not source.is_file():
            continue
        try:
            text = mask_code(source.read_text(encoding='utf-8'))
        except (OSError, UnicodeError) as exc:
            issues.append({'file': source.relative_to(root).as_posix(), 'line': 1, 'target': '', 'reason': str(exc)})
            continue
        matches = sorted([*LINK.finditer(text), *REFERENCE.finditer(text)], key=lambda m: m.start())
        for match in matches:
            target = match[1].strip('<>')
            try:
                parsed = urlsplit(target)
            except ValueError:
                skipped += 1
                continue
            if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith('/'):
                skipped += 1
                continue
            checked += 1
            destination = (source.parent / unquote(parsed.path)).resolve()
            reason = None
            if not destination.is_relative_to(root):
                reason = 'target escapes scan root'
            elif not destination.exists():
                reason = 'target does not exist'
            if reason:
                issues.append({'file': source.relative_to(root).as_posix(), 'line': text.count('\n', 0, match.start()) + 1, 'target': target, 'reason': reason})
    return {'checked': checked, 'skipped': skipped, 'issues': issues}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', default='.')
    parser.add_argument('--json', action='store_true', help='Print a machine-readable report')
    args = parser.parse_args(argv)
    try:
        report = audit(args.root)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for issue in report['issues']:
            print(f"{issue['file']}:{issue['line']}: {issue['reason']}: {issue['target']}")
        print(f"Checked {report['checked']} local links; skipped {report['skipped']}; issues {len(report['issues'])}.")
    return 1 if report['issues'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
