import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from md_link_audit import audit, main


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text=''):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def test_valid_and_missing_with_line_numbers(self):
        self.write('guide.md')
        self.write('README.md', '# Test\n[ok](guide.md)\n[bad](gone.md)\n')
        result = audit(self.root)
        self.assertEqual(result['checked'], 2)
        self.assertEqual(result['issues'][0]['line'], 3)

    def test_encoded_images_references_and_fragments(self):
        self.write('图 片.png')
        self.write('guide.md')
        self.write('README.md', '![a](%E5%9B%BE%20%E7%89%87.png)\n[x](guide.md#title)\n[x]: <guide.md>\n')
        self.assertEqual(audit(self.root), {'checked': 3, 'skipped': 0, 'issues': []})

    def test_ignores_fences_inline_comments_and_remote(self):
        self.write('README.md', '```md\n[x](bad.md)\n```\n~~~\n[x](bad.md)\n~~~\n`[x](bad.md)`\n<!-- [x](bad.md) -->\n[x](https://example.com)\n[x](#title)\n[x](mailto:a@example.com)\n')
        result = audit(self.root)
        self.assertEqual(result['checked'], 0)
        self.assertEqual(result['skipped'], 3)

    def test_excludes_dependencies(self):
        self.write('node_modules/a/README.md', '[x](missing.md)')
        self.assertEqual(audit(self.root)['issues'], [])

    def test_traversal_and_symlink(self):
        self.write('README.md', '[x](../outside.md)\n[x](escape.md)')
        (self.root / 'escape.md').symlink_to(self.root.parent / 'outside.md')
        self.assertEqual(len(audit(self.root)['issues']), 2)

    def test_json_and_exit_status(self):
        self.write('README.md', '[x](missing.md)')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main([str(self.root), '--json']), 1)
        self.assertEqual(len(json.loads(output.getvalue())['issues']), 1)

    def test_invalid_root(self):
        with self.assertRaises(ValueError):
            audit(self.root / 'absent')


if __name__ == '__main__':
    unittest.main()
