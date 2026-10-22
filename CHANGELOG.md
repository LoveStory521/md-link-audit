# Changelog

## 0.1.1 — 2026-10-22

- Handle code fences, inline code, and HTML comments in source order so comment markers inside code cannot hide real links.
- Report cyclic or unresolvable target paths as issues and continue scanning, including valid JSON output.
- Correct reference-definition line numbers after blank lines.
- Add five regression tests (12 total).

## 0.1.0 — 2026-10-21

Initial implementation of offline Markdown local-file link auditing, text/JSON reports, basic code exclusion, and regression tests.
