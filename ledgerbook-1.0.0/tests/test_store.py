import tempfile,unittest
from pathlib import Path
from ledgerbook.store import Store
class StorageCompatibility(unittest.TestCase):
 def test_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'db.sqlite3');b=s.add_book('Car');s.save_entry(b,{'entry_date':'2026-10-28','title':'Oil change','notes':'Test'});self.assertEqual(s.values(s.entries(b)[0])['title'],'Oil change');self.assertEqual(s.integrity_check(),'ok');s.close()
 def test_export_import(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'db.sqlite3');b=s.add_book('Printer');s.save_entry(b,{'title':'Test print'});path=Path(d)/'book.ledgerbook';s.export_logbook(b,path);new,count=s.import_logbook(path);self.assertEqual(count,1);self.assertEqual(len(s.entries(new)),1);s.close()
if __name__=='__main__':unittest.main()
