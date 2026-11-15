import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from combine import blocktube_channels, smarttube_entries, text_ids

A = 'UC' + 'a' * 22
B = 'UC' + 'b' * 22


class ParserTests(unittest.TestCase):
    def test_exact_ids_only(self):
        self.assertEqual(text_ids(f'// {A}\n{A}\n{A}\n! comment\n/{B}/\nUCbad\n'), {A})

    def test_blocktube_never_imports_keywords_regex_or_script(self):
        content = json.dumps({'filterData': {'channelId': [
            '// Blocked by context menu (Example)', A, '/.*/', '// other', B],
            'videoTitle': ['news'], 'javascript': 'throw Error()'}})
        self.assertEqual(blocktube_channels(content), {A: 'Example', B: ''})

    def test_smarttube_preserves_ids_and_name_aliases(self):
        self.assertEqual(smarttube_entries(f'{A}&vi;Example%AR%null&vi;Name Alias%OB%null'),
                         {'id:' + A: 'Example', 'name:name alias': 'Name Alias'})

    def test_smarttube_rejects_malformed_data(self):
        with self.assertRaises(ValueError):
            smarttube_entries('not a SmartTube export')


if __name__ == '__main__':
    unittest.main()
