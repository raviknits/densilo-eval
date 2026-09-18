import hashlib,json,unittest
from pathlib import Path
from densilo_eval.query import query_records
class Fixtures(unittest.TestCase):
 def test_manifest(self):
  m=json.loads(Path('manifest.json').read_text());self.assertEqual(len(m['tasks']),30);self.assertEqual(len({t['id'] for t in m['tasks']}),30);self.assertEqual(len({t['cluster'] for t in m['tasks']}),10)
  for task in m['tasks']:self.assertEqual(hashlib.sha256(Path(task['path']).read_bytes()).hexdigest(),task['sha256'])
  self.assertFalse(m['independent_sources'])
 def test_exact_duplicates(self):
  result=query_records({'records.json':'[{"x":1},{"x":1},{"x":2}]'},'SELECT count(*) AS n, sum(x) AS total FROM records')
  self.assertIn('3',json.dumps(result));self.assertIn('4',json.dumps(result))
 def test_import(self):
  from densilo_eval import driver
  self.assertTrue(callable(driver.run_one))
if __name__=='__main__':unittest.main()
