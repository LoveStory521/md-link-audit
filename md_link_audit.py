"""Offline audit of local Markdown file links. Python 3.10+, no dependencies."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__'}
LINK = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+["\'][^\n]*?["\'])?\s*\)')
REFERENCE = re.compile(r'^ {0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)', re.M)


def mask_code(text):
    """Mask code and comments in source order, preserving offsets and lines."""
    masked = list(text)
    position = 0
    while position < len(text):
        end = None
        if position == 0 or text[position - 1] == '\n':
            opener = re.match(r' {0,3}(`{3,}|~{3,})[^\n]*(?:\n|$)', text[position:])
            if opener:
                fence = opener[1]
                closer = re.compile(
                    r'^ {0,3}' + re.escape(fence[0]) + '{' + str(len(fence))
                    + r',}[ \t]*\r?$', re.M)
                closing = closer.search(text, position + opener.end())
                end = closing.end() if closing else len(text)
        if end is None and text.startswith('<!--', position):
            closing = text.find('-->', position + 4)
            end = closing + 3 if closing >= 0 else len(text)
        if end is None and text[position] == '`':
            run = re.match(r'`+', text[position:])[0]
            closing = re.search(r'(?<!`)' + re.escape(run) + r'(?!`)',
                                text[position + len(run):])
            if closing:
                end = position + len(run) + closing.end()
            else:
                position += len(run)
                continue
        if end is None:
            position += 1
            continue
        for index in range(position, end):
            if text[index] not in '\r\n':
                masked[index] = ' '
        position = end
    return ''.join(masked)


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
            reason = None
            try:
                destination = (source.parent / unquote(parsed.path)).resolve()
                if not destination.is_relative_to(root):
                    reason = 'target escapes scan root'
                elif not destination.exists():
                    reason = 'target does not exist'
            except (OSError, RuntimeError, ValueError) as exc:
                reason = f'cannot resolve target: {exc}'
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
