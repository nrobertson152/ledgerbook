"""Beta 2.1 compatibility and data-integrity regression tests (Qt not required)."""
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from ledgerbook.store import Store

class QtMigrationDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.store=Store(self.root/'db.sqlite3')
        self.addCleanup(self.store.close)

    def test_default_columns_generic(self):
        bid=self.store.add_book('Car')
        self.assertEqual([f['label'] for f in self.store.columns(bid)],['Date','Entry','Notes'])

    def test_fields_roundtrip(self):
        bid=self.store.add_book('Printer')
        fields=self.store.columns(bid)+[{'key':'filament','label':'Filament','type':'select','options':['PLA','PETG'],'visible':True}]
        self.store.set_columns(bid,fields)
        eid=self.store.save_entry(bid,{'entry_date':'2026-10-28','title':'Test','notes':'line 1\nline 2','filament':'PLA'})
        row=self.store.db.execute('SELECT * FROM entries WHERE id=?',(eid,)).fetchone()
        self.assertEqual(self.store.values(row)['notes'],'line 1\nline 2')
        self.store.save_entry(bid,{'entry_date':'2026-10-29','title':'Edited','notes':'long text','filament':'PETG'},eid)
        self.assertEqual(self.store.values(self.store.entries(bid)[0])['filament'],'PETG')

    def test_folder_rename_move_delete(self):
        bid=self.store.add_book('Machine');fid=self.store.add_folder('Workshop')
        self.store.configure_book(bid,folder_id=fid)
        self.store.rename_folder(fid,'Equipment')
        self.assertEqual(self.store.folders()[0]['name'],'Equipment')
        self.store.delete_folder(fid)
        self.assertIsNone(self.store.db.execute('SELECT folder_id FROM books WHERE id=?',(bid,)).fetchone()[0])

    def test_duplicate_book_and_archive(self):
        bid=self.store.add_book('Car');self.store.save_entry(bid,{'title':'Oil change'})
        dup=self.store.duplicate_book(bid,True)
        self.assertEqual(len(self.store.entries(dup)),1)
        self.store.configure_book(dup,archived=1)
        self.assertNotIn(dup,[b['id'] for b in self.store.books()])
        self.assertIn(dup,[b['id'] for b in self.store.books(True)])
        self.store.configure_book(dup,archived=0)
        self.assertIn(dup,[b['id'] for b in self.store.books()])

    def test_recycle_entry_restore(self):
        bid=self.store.add_book('Car');eid=self.store.save_entry(bid,{'title':'Repair'})
        self.store.delete_entry(eid)
        self.assertEqual(len(self.store.entries(bid)),0)
        trash=self.store.deleted_items()[0]['id']
        self.store.restore_deleted_entry(trash)
        self.assertEqual(len(self.store.entries(bid)),1)

    def test_recycle_book_restore(self):
        bid=self.store.add_book('Car');self.store.save_entry(bid,{'title':'Repair'})
        self.store.delete_book(bid)
        trash=self.store.db.execute('SELECT id FROM deleted_books').fetchone()[0]
        restored=self.store.restore_deleted_book(trash)
        self.assertEqual(len(self.store.entries(restored)),1)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM deleted_books').fetchone()[0],0)

    def test_empty_recycle_bin_both_kinds(self):
        a=self.store.add_book('A');b=self.store.add_book('B')
        self.store.delete_entry(self.store.save_entry(a,{'title':'x'}));self.store.delete_book(b)
        self.store.empty_all_recycle()
        self.assertEqual(len(self.store.deleted_items()),0)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM deleted_books').fetchone()[0],0)

    def test_search_custom_fields(self):
        bid=self.store.add_book('Printer');fields=self.store.columns(bid)+[{'key':'material','label':'Material','type':'text','visible':True}]
        self.store.set_columns(bid,fields)
        self.store.save_entry(bid,{'title':'Print','material':'PETG'})
        self.assertEqual(len(self.store.entries(bid,'petg')),1)
        self.assertEqual(len(self.store.entries(bid,'abs')),0)

    def test_csv_roundtrip(self):
        bid=self.store.add_book('Printer');self.store.save_entry(bid,{'title':'Job','notes':'multiline\nentry'})
        path=self.root/'data.csv';self.store.export_csv(bid,path)
        bid2=self.store.add_book('Imported');self.assertEqual(self.store.import_csv(bid2,path),1)
        self.assertEqual(self.store.values(self.store.entries(bid2)[0])['notes'],'multiline\nentry')

    def test_logbook_roundtrip(self):
        bid=self.store.add_book('Car');self.store.save_entry(bid,{'title':'Tires'})
        path=self.root/'car.ledgerbook';self.store.export_logbook(bid,path)
        new,count=self.store.import_logbook(path)
        self.assertEqual(count,1);self.assertEqual(self.store.values(self.store.entries(new)[0])['title'],'Tires')

    def test_backup_integrity(self):
        bid=self.store.add_book('Car');self.store.save_entry(bid,{'title':'Inspection'})
        path=self.root/'backup.sqlite3';self.store.backup(path)
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM entries').fetchone()[0],1)
        self.assertEqual(self.store.integrity_check(),'ok')

    def test_invalid_csv_does_not_create_rows(self):
        bid=self.store.add_book('Car');path=self.root/'empty.csv';path.write_text('')
        with self.assertRaises(ValueError):self.store.import_csv(bid,path)

    def test_invalid_logbook_rejected(self):
        path=self.root/'bad.ledgerbook';path.write_text('{"format":"bad"}')
        with self.assertRaises(ValueError):self.store.import_logbook(path)

    def test_legacy_migration(self):
        path=self.root/'legacy.sqlite3'
        db=sqlite3.connect(path)
        db.executescript('''CREATE TABLE books(id INTEGER PRIMARY KEY,name TEXT NOT NULL,kind TEXT NOT NULL DEFAULT 'General',description TEXT NOT NULL DEFAULT '',unit TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE entries(id INTEGER PRIMARY KEY,book_id INTEGER NOT NULL,entry_date TEXT NOT NULL,title TEXT NOT NULL,category TEXT NOT NULL DEFAULT '',reading REAL,cost REAL NOT NULL DEFAULT 0,notes TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
INSERT INTO books(name) VALUES('Old');INSERT INTO entries(book_id,entry_date,title,cost) VALUES(1,'2025-01-01','Repair',123.45);''');db.close()
        s=Store(path)
        try:
            self.assertIn('cost',[f['key'] for f in s.columns(1)])
            self.assertEqual(s.values(s.entries(1)[0])['cost'],123.45)
        finally:s.close()

if __name__=='__main__':unittest.main()
