# md-link-audit

A small, dependency-free Python tool that finds broken **local file links** in Markdown documentation before a release. Runs offline; it never sends documents or URLs to a server.

## Quick start

Requires Python 3.10 or newer. Download or clone this repository, then run:

```sh
python md_link_audit.py /path/to/repository
python md_link_audit.py /path/to/repository --json
python -m unittest discover -s tests -v
```

Example output for a missing file:

```text
README.md:3: target does not exist: docs/missing.md
Checked 2 local links; skipped 0; issues 1.
```

Exit codes: 0 = no issues, 1 = broken/unsafe links or unreadable Markdown, 2 = invalid arguments.

## Supported checks

- Inline file links, image paths, and reference-link definitions.
- Relative paths, UTF-8 filenames, URL-encoded filenames, and paths enclosed in angle brackets.
- Recursively scans `.md` and `.markdown`; skips common dependency directories.
- Ignores fenced code, inline code, and HTML comments.
- Flags links resolving outside the scanned directory, including symlink escapes.
- Prints file and line information or JSON suitable for automation.

## Deliberate limits

This is an initial release with a lightweight parser, not a full CommonMark implementation. Nested parentheses, escaped brackets, multiline links and complex code spans may not be parsed correctly. Reference definitions are checked even if unused. Heading fragments are not validated. HTTP(S), mail links, root-relative website paths and fragment-only links are skipped. Existing directories count as valid targets. Symlinked source Markdown is skipped. The scanner does not fetch external websites.

## 在中文项目中使用

这是一个离线检查 Markdown 本地文件链接的小工具，无需安装第三方依赖。它能定位 README、说明文档中指向不存在文件的链接，支持中文文件名和 JSON 报告。把仓库目录作为参数传入即可。网页链接、标题锚点及复杂 Markdown 语法不在当前检查范围内。

## Development and status

Created on 2026-10-21 with Codex assistance. This is a new project; no adoption, download or maintenance-history claims are made. See [contributing](CONTRIBUTING.md), [release notes](CHANGELOG.md), and the [MIT license](LICENSE).
