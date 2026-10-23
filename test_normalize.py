import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from normalize_exceptions import process

class NormalizationTests(unittest.TestCase):
    def test_sample(self):
        with TemporaryDirectory() as d:
            records, counts = process(Path(__file__).with_name('exceptions_raw.csv'), Path(d) / 'out.csv')
            self.assertEqual(len(records), 5)
            self.assertEqual(dict(counts), {'missed_pickup': 2, 'doc_mismatch': 2, 'carrier_substitution': 1})
            self.assertEqual(records[2]['terminal'], 'Terminal 3')
            self.assertEqual(records[2]['carrier_code'], 'SWFT')
            self.assertEqual(records[2]['event_ts'], '2026-08-14T10:03:00Z')
            self.assertEqual(records[3]['needs_review'], 'yes')
            self.assertEqual(records[3]['carrier_code'], '')
            self.assertEqual(sum(r['needs_review'] == 'yes' for r in records), 1)
            self.assertTrue(all(r['event_ts'].startswith('2026-08-') for r in records))

if __name__ == '__main__':
    unittest.main()
