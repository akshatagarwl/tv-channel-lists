import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import combine
from export_curated import public_records

A = 'UC' + 'a' * 22
B = 'UC' + 'b' * 22


class PublicationTests(unittest.TestCase):
    def test_public_records_are_minimal_approved_facts(self):
        record = {'id': A, 'name': ' Example \n', 'category': 'example', 'approved': True,
                  'source_url': 'https://www.youtube.com/@Example/about', 'checked_at': '2026-11-15',
                  'description': 'Publisher biography and contact details', 'session': 'must-not-export'}
        exported = public_records([record, {**record, 'id': B, 'approved': False}])
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported[0]['name'], 'Example')
        self.assertEqual(set(exported[0]), {'id', 'name', 'category', 'approved', 'source_url', 'checked_at'})

    def test_export_rejects_invalid_identity_duplicates_or_external_urls(self):
        record = {'id': A, 'name': 'Example', 'category': 'example', 'approved': True,
                  'source_url': 'https://www.youtube.com/@Example/about', 'checked_at': '2026-11-15'}
        for entries in [[record, record], [{**record, 'id': 'invalid'}],
                        [{**record, 'source_url': 'https://example.com/'}],
                        [{**record, 'source_url': 'https://www.youtube.com/@Example?session=secret'}],
                        [{**record, 'approved': 'true'}]]:
            with self.assertRaises(ValueError):
                public_records(entries)

    def test_public_list_contains_only_reviewed_facts(self):
        entries = json.loads((ROOT / 'lists/religion-spirituality.json').read_text())
        self.assertEqual(len(entries), 49)
        self.assertEqual(public_records(entries), entries)
        for entry in entries:
            self.assertNotIn('description', entry)

    def fixture(self, root):
        (root / 'lists').mkdir()
        (root / 'sources.json').write_text(json.dumps({'religion': {
            'kind': 'local-curated', 'file': 'lists/test.json', 'license': 'CC0-1.0'}}))
        (root / 'lists/test.json').write_text(json.dumps([
            {'id': A, 'name': 'Allowed channel', 'approved': True, 'source_url': 'https://www.youtube.com/channel/' + A},
            {'id': B, 'name': 'Blocked channel', 'approved': True, 'source_url': 'https://www.youtube.com/channel/' + B}]))
        (root / 'allowlist.txt').write_text(A + '\n')

    def test_private_exceptions_do_not_erase_explicit_personal_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            personal = root / 'personal-input'
            personal.write_text(f'{A}&vi;Personal choice%OB%null')
            out = root / 'data/subset'
            with patch.object(combine, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                combine.build(personal=personal, selected_sources=['religion'], output=out)
            payload = json.loads((out / 'community.json').read_text())
            self.assertEqual(payload['channels'], [[B, 'Blocked channel', 8]])
            self.assertIn('id:' + A, json.loads((out / 'personal.json').read_text()))
            self.assertEqual(json.loads((out / 'summary.json').read_text())['community_allowlisted'], 1)

    def test_unknown_source_and_shrink_fail_without_replacing_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            out = root / 'data'
            out.mkdir()
            (out / 'summary.json').write_text(json.dumps({'community_channels': 100}))
            (out / 'community.json').write_text('last-good')
            with patch.object(combine, 'ROOT', root):
                with self.assertRaises(ValueError):
                    combine.build(selected_sources=['unknown'])
                with self.assertRaises(ValueError):
                    combine.build(selected_sources=['religion'])
            self.assertEqual((out / 'community.json').read_text(), 'last-good')


if __name__ == '__main__':
    unittest.main()
