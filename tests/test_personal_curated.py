import unittest

from combine import merge_curated_personal

A = 'UC' + 'a' * 22
B = 'UC' + 'b' * 22


def reviewed(channel=A, name='Example'):
    return {'id': channel, 'name': name, 'approved': True,
            'source_url': 'https://www.youtube.com/channel/' + channel + '/about'}


class CuratedPersonalTests(unittest.TestCase):
    def test_adds_exact_ids_without_dropping_existing_ids_or_aliases(self):
        old = {'id:' + B: 'Existing label', 'name:alias': 'Alias'}
        new = merge_curated_personal(old, [reviewed()])
        self.assertEqual(new, {**old, 'id:' + A: 'Example'})
        self.assertNotIn('id:' + A, old)  # no mutation of the saved preference set

    def test_existing_user_labels_win_and_duplicates_are_idempotent(self):
        old = {'id:' + A: 'My label'}
        self.assertEqual(merge_curated_personal(old, [reviewed(), reviewed()]), old)

    def test_unreviewed_candidates_are_not_automatically_blocked(self):
        item = reviewed()
        item['approved'] = False
        self.assertEqual(merge_curated_personal({}, [item]), {})

    def test_requires_exact_id_name_and_youtube_identity_evidence(self):
        for changes in ({'id': 'some words'}, {'name': ''}, {'name': 'Bad\nname'},
                        {'source_url': 'https://example.com/channel/' + A},
                        {'source_url': 'https://www.youtube.com/@example?token=private'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                merge_curated_personal({}, [{**reviewed(), **changes}])


if __name__ == '__main__':
    unittest.main()
