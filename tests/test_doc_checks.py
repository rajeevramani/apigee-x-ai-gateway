"""Isolated negative fixtures; never mutate repository documents/assets."""
import tempfile
import unittest
from pathlib import Path

from doc_checks import check_examples


class ExampleRegressions(unittest.TestCase):
    def test_removed_example_fails_after_relocation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'references/nested').mkdir(parents=True)
            (root / 'assets/examples').mkdir(parents=True)
            (root / 'assets/examples/a.xml').write_text('<Policy/>\n')
            doc = root / 'references/nested/moved.md'
            doc.write_text('Example source: `../../assets/examples/a.xml`\n\n```xml\n<Policy/>\n```\n')
            expected = {'assets/examples/a.xml'}
            self.assertEqual(set(check_examples(root, expected)), expected)
            doc.unlink()
            with self.assertRaisesRegex(AssertionError, 'missing'):
                check_examples(root, expected)

    def test_bad_markers_and_mismatch_fail(self):
        block = 'Example source: `../assets/examples/a.xml`\n\n```xml\n<Policy/>\n```\n'
        for bad, message in [
            (block + block, 'duplicate'),
            (block + 'Example source: broken\n', 'malformed'),
            (block.replace('```xml', '```text'), 'malformed'),
            (block.replace('<Policy/>', '<Wrong/>'), 'mismatched'),
            (block.replace('a.xml', 'missing.xml'), 'missing asset'),
        ]:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'references').mkdir()
                (root / 'assets/examples').mkdir(parents=True)
                (root / 'assets/examples/a.xml').write_text('<Policy/>')
                (root / 'references/example.md').write_text(bad)
                with self.assertRaisesRegex(AssertionError, message):
                    check_examples(root, {'assets/examples/a.xml'})


class LinkRegressions(unittest.TestCase):
    def test_reference_definition_paragraph_boundary(self):
        from doc_checks import markdown_links
        definitions = '[ref]: https://example.com/source\n[other]: https://example.com/other\n'
        links = ['https://example.com/source', 'https://example.com/other']
        for prefix in ['', '[source][ref]\n\n', 'Report the result.\n\n']:
            with self.subTest(valid_prefix=prefix):
                self.assertEqual(markdown_links(prefix + definitions), links)
        for paragraph in ['Report the result.', '`Report`', '[source][ref]']:
            with self.subTest(paragraph=paragraph):
                with self.assertRaisesRegex(AssertionError, 'reference definition.*blank separator'):
                    markdown_links(paragraph + '\n' + definitions)
        self.assertEqual(markdown_links('```md\nReport.\n' + definitions + '```\n'), [])

    def test_broken_anchor_fails_inline_and_reference_links(self):
        from doc_checks import check_links
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, source = root / 'target.md', root / 'CHANGELOG.md'
            target.write_text('# Valid heading\n')
            for link in ['[label](target.md#ANCHOR)', '[label][ref]\n\n[ref]: target.md#ANCHOR',
                         '[ref][]\n\n[ref]: target.md#ANCHOR', '[ref]\n\n[ref]: target.md#ANCHOR']:
                with self.subTest(link=link):
                    source.write_text(link.replace('ANCHOR', 'valid-heading'))
                    check_links(root, [source, target])
                    source.write_text(link.replace('ANCHOR', 'missing'))
                    with self.assertRaisesRegex(AssertionError, 'anchor'):
                        check_links(root, [source, target])

    def test_heading_convention_and_fenced_code(self):
        from doc_checks import heading_anchors
        text = ('# **Hello** `code` [link](target.md) _word_ a_b Café!\n'
                '# Same\n# Same\n# Same-1\n# Same\n'
                '```bash\n# Not a heading\n```\n'
                '~~~~\n# Also not a heading\n~~~\n~~~~\n'
                '<a id="custom"></a>\n')
        self.assertEqual(heading_anchors(text), {
            'hello-code-link-word-a_b-café', 'same', 'same-1', 'same-1-1', 'same-2', 'custom'})
        self.assertEqual(heading_anchors('# `__TOKEN__` and **bold**'), {'__token__-and-bold'})
        with self.assertRaisesRegex(AssertionError, 'duplicate explicit'):
            heading_anchors('<a id="x"></a>\n<span id="x"></span>')
        with self.assertRaisesRegex(AssertionError, 'unclosed'):
            heading_anchors('```bash\n# hidden')

    def test_links_relative_paths_fragments_and_code_exclusion(self):
        from doc_checks import check_links, markdown_documents
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'references/nested').mkdir(parents=True)
            for name in ['SKILL.md', 'README.md', 'CHANGELOG.md']:
                (root / name).write_text('# Root\n')
            target = root / 'references/target file.md'
            target.write_text('# Café\n<a id="explicit"></a>\n')
            source = root / 'references/nested/source.md'
            source.write_text('# Here\n[same](#here)\n[utf](../target%20file.md#caf%C3%A9)\n'
                              '[explicit](<../target file.md#explicit> "title")\n'
                              '`[ignored](missing.md)`\n```md\n[ignored](missing.md)\n```\n')
            check_links(root, markdown_documents(root))
            self.assertIn(root / 'CHANGELOG.md', markdown_documents(root))
            for bad in ['[missing](gone.md)', '[bad][undefined]', '[private](../../.env)',
                        '[escaped](../../../outside.md)']:
                source.write_text(bad)
                with self.assertRaises(AssertionError):
                    check_links(root, markdown_documents(root))
            source.write_text('# Here\n')
            (root / 'CHANGELOG.md').write_text('[bad](#gone)')
            with self.assertRaisesRegex(AssertionError, 'anchor'):
                check_links(root, markdown_documents(root))


class MetadataRegressions(unittest.TestCase):
    SOURCE = ('---\nname: example\ndescription: Example description\nversion: 9.8.7\n'
              'license: Apache-2.0\n---\n')

    def test_required_fields_and_values(self):
        from doc_checks import frontmatter, validate_metadata
        fields = frontmatter(self.SOURCE)
        validate_metadata(fields)
        self.assertEqual(fields['version'], '9.8.7')
        for field in ['name', 'description', 'version']:
            with self.subTest(missing=field):
                incomplete = dict(fields)
                del incomplete[field]
                with self.assertRaisesRegex(AssertionError, 'shape'):
                    validate_metadata(incomplete)
        for field, value in [('name', 'Not Valid'), ('description', ''), ('version', 'not-version'),
                             ('platforms', 'linux'), ('platforms', []), ('platforms', ['linux', 'linux'])]:
            with self.subTest(field=field, value=value), self.assertRaises(AssertionError):
                validate_metadata(dict(fields, **{field: value}))

    def test_allowed_flat_extras(self):
        from doc_checks import frontmatter, validate_metadata
        extras = ('extra-key: Plain text\nextra_key: "Quoted text"\n'
                  "notes: 'Single quoted text'\nplatforms: [linux, 'macos', \"windows\"]\n")
        fields = frontmatter(self.SOURCE.replace('license:', extras + 'license:'))
        validate_metadata(fields)
        self.assertEqual(fields['extra-key'], 'Plain text')
        self.assertEqual(fields['extra_key'], 'Quoted text')
        self.assertEqual(fields['notes'], 'Single quoted text')
        self.assertEqual(fields['platforms'], ['linux', 'macos', 'windows'])

    def test_unsupported_shapes(self):
        from doc_checks import frontmatter
        for value in ['nested:\n  child: value', '|\n  text', '>\n  text',
                      '|-', '>+', '|2', '!str text', '&anchor text', '*alias',
                      '%directive', '@value', '`value', '- text', '? text',
                      '{child: value}', '[alpha, 123]', 'true', '12',
                      'null', '1e3', '0xFF', '.inf', '.nan', '2026-09-15',
                      '12:30', 'text # comment', 'key: value',
                      'text\t# comment', 'key:\tvalue',
                      "'it''s'", '"escaped\\ntext"', '"unfinished',
                      'value\n  - item', 'value\n<<: *alias']:
            with self.subTest(value=value), self.assertRaises(AssertionError):
                frontmatter(self.SOURCE.replace('Example description', value))
        for bad in [self.SOURCE.replace('license:', ' license:'),
                    self.SOURCE.replace('license:', 'name: duplicate\nlicense:'),
                    self.SOURCE.replace('---\n', '', 1)]:
            with self.subTest(bad=bad), self.assertRaises(AssertionError):
                frontmatter(bad)


if __name__ == '__main__':
    unittest.main()
