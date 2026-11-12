import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'captions.py'


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')

    def test_end_to_end_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            doc = Path(directory) / 'captions.json'
            md = Path(directory) / 'summary.md'
            result = self.run_cli('import', ROOT / 'examples/captions.json', '--provider', 'test', '--out', doc)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = self.run_cli('inspect', doc)
            self.assertEqual(json.loads(report.stdout)['segment_count'], 3)
            result = self.run_cli('render', doc, ROOT / 'examples/summary.json', '--out', md)
            self.assertEqual(result.returncode, 0, result.stderr)
            original = md.read_bytes()
            self.assertIn('140 BPM', original.decode('utf-8'))
            repeated = self.run_cli('render', doc, ROOT / 'examples/summary.json', '--out', md)
            self.assertEqual(repeated.returncode, 2)
            self.assertEqual(md.read_bytes(), original)

    def test_failed_import_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'error.json', Path(directory) / 'out.json'
            source.write_text('{"error":{"code":"upstream_rate_limited"}}', encoding='utf-8')
            result = self.run_cli('import', source, '--provider', 'test', '--out', output)
            self.assertEqual(result.returncode, 2)
            self.assertIn('upstream_rate_limited', result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
