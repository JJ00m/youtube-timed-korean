import copy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'captions.py'
spec = importlib.util.spec_from_file_location('captions', SCRIPT)
c = importlib.util.module_from_spec(spec) if SCRIPT.exists() else None
if c:
    spec.loader.exec_module(c)


class CaptionsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(c, 'caption helper must be implemented')
        self.raw = {'video_id': 'abcdefghijk', 'language_code': 'en', 'kind': 'asr',
                    'has_transcript': True, 'segment_count': 3, 'segments': [
                        {'start_ms': 0, 'duration_ms': 4000, 'text': 'Set tempo to 140.'},
                        {'start_ms': 2000, 'duration_ms': 3500, 'text': 'Add a short snare.'},
                        {'start_ms': 6000, 'duration_ms': 2000, 'text': '[music]'}]}

    def test_url_forms(self):
        for value in ['abcdefghijk', 'https://youtu.be/abcdefghijk?t=2',
                      'https://www.youtube.com/watch?v=abcdefghijk',
                      'https://youtube.com/shorts/abcdefghijk']:
            self.assertEqual(c.video_id(value), 'abcdefghijk')

    def test_reject_foreign_url(self):
        for value in ['https://youtube.com.evil.test/watch?v=abcdefghijk', 'bad',
                      'https://evil.test/abcdefghijk']:
            with self.assertRaises(ValueError): c.video_id(value)

    def test_overlap_preserved(self):
        doc = c.normalize(self.raw, 'test')
        report = c.inspect(doc)
        self.assertEqual(report['overlap_count'], 1)
        self.assertEqual(report['last_end_ms'], 8000)
        self.assertEqual(doc['segments'][1]['start_ms'], 2000)

    def test_invalid_times(self):
        for value in [-1, float('nan'), float('inf'), True, '0']:
            raw = copy.deepcopy(self.raw)
            raw['segments'][0]['start_ms'] = value
            with self.assertRaises(ValueError): c.normalize(raw, 'test')

    def test_unsorted_and_zero_duration(self):
        for key, value in [('start_ms', 7000), ('duration_ms', 0)]:
            raw = copy.deepcopy(self.raw)
            raw['segments'][0][key] = value
            with self.assertRaises(ValueError): c.normalize(raw, 'test')

    def test_empty_and_count_mismatch(self):
        for key, value in [('segments', []), ('has_transcript', False), ('segment_count', 2)]:
            raw = copy.deepcopy(self.raw)
            raw[key] = value
            with self.assertRaises(ValueError): c.normalize(raw, 'test')

    def test_provider_error(self):
        with self.assertRaisesRegex(ValueError, 'upstream_rate_limited'):
            c.normalize({'error': {'code': 'upstream_rate_limited'}}, 'test')

    def test_firecrawl_envelope(self):
        doc = c.normalize({'data': {'alexandria': [{'data': self.raw}]}}, 'test')
        self.assertEqual(len(doc['segments']), 3)

    def test_source_derived_ranges(self):
        doc = c.normalize(self.raw, 'test')
        md = c.render(doc, {'mode': 'summary', 'items': [
            {'source_ids': ['s0001', 's0002'], 'text': '템포와 스네어로 비트를 구성한다.'}]})
        self.assertIn('00:00.000–00:05.500', md)
        self.assertIn('&t=0s', md)
        self.assertIn('한국어 요약', md)

    def test_invalid_references_and_empty_text(self):
        doc = c.normalize(self.raw, 'test')
        for ids, text in [(['missing'], '내용'), ([], '내용'),
                          (['s0001', 's0001'], '내용'), (['s0001'], '  ')]:
            with self.assertRaises(ValueError):
                c.render(doc, {'mode': 'summary', 'items': [{'source_ids': ids, 'text': text}]})

    def test_summary_mode_only(self):
        with self.assertRaises(ValueError):
            c.render(c.normalize(self.raw, 'test'), {'mode': 'translation', 'items': []})

    def test_duplicate_ids(self):
        doc = c.normalize(self.raw, 'test')
        doc['segments'][1]['id'] = doc['segments'][0]['id']
        with self.assertRaises(ValueError): c.inspect(doc)

    def test_long_timestamp(self):
        self.assertEqual(c.timestamp(3661001), '01:01:01.001')

    def test_provider_text_cannot_create_markdown_images(self):
        doc = c.normalize(self.raw, 'test')
        doc['title'] = '![tracking](https://example.invalid/pixel.png)'
        md = c.render(doc, {'mode': 'summary', 'items': [
            {'source_ids': ['s0001'], 'text': '[click](https://example.invalid)'}]})
        self.assertNotIn('![tracking](', md)
        self.assertNotIn('[click](', md)
        self.assertIn('\\!\\[tracking\\]', md)

    def test_normalized_ids_are_canonical(self):
        doc = c.normalize(self.raw, 'test')
        doc['video_id'] = 'https://youtu.be/abcdefghijk'
        with self.assertRaises(ValueError): c.inspect(doc)
        doc = c.normalize(self.raw, 'test')
        doc['segments'][0]['id'] = '![x](https://example.invalid)'
        with self.assertRaises(ValueError): c.inspect(doc)


if __name__ == '__main__':
    unittest.main()
