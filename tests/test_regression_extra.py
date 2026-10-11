import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from tools.safe_document_core import analyze_document, analyze_json

class Extra(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def test_binary_input(self):
        p=self.root/'binary.txt';p.write_bytes(b'\xff')
        self.assertEqual(analyze_document(str(p),'risk',str(self.root))['status'],'NOT_VERIFIED')
    def test_oversize(self):
        p=self.root/'large.txt';p.write_bytes(b'a' * 5000001)
        self.assertEqual(analyze_document(str(p),'risk',str(self.root))['reason'],'DOCUMENT_TOO_LARGE')
    def test_blank_text(self):
        p=self.root/'blank.md';p.write_text('  \n')
        self.assertEqual(analyze_document(str(p),'risk',str(self.root))['reason'],'NO_EXTRACTABLE_TEXT')
    def test_missing_root(self):
        p=self.root/'x.txt';p.write_text('PASS')
        self.assertEqual(analyze_document(str(p),'risk',str(self.root/'missing'))['status'],'NOT_VERIFIED')
    def test_invalid_docx(self):
        p=self.root/'x.docx';p.write_bytes(b'not docx')
        self.assertEqual(analyze_document(str(p),'risk',str(self.root))['status'],'NOT_VERIFIED')
    def test_redline_docx(self):
        p=self.root/'redline.docx'
        with ZipFile(p,'w',ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            z.writestr('word/document.xml','<x:document xmlns:x="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><x:body><x:p><x:del><x:r><x:delText>PASS</x:delText></x:r></x:del></x:p></x:body></x:document>')
        self.assertEqual(analyze_document(str(p),'compliance',str(self.root))['reason'],'DOCX_REVISIONS_NEED_DEDICATED_REVIEW')
    def test_no_invented_compliance(self):
        p=self.root/'fail.md';p.write_text('Failure noted')
        r=json.loads(analyze_json(str(p),'compliance',str(self.root)))
        self.assertEqual(r['gxp_compliance'],'NOT_VERIFIED')
        self.assertEqual(r['gxp_release'],'NOT_GRANTED')
    def test_symlink_escape(self):
        outside=Path(self.temp.name).parent/'dwvsc_external_synthetic.txt'
        # Use a separate sandbox subdirectory instead of altering any shared external file.
        outer=self.root/'scope';outer.mkdir()
        target=self.root/'outside.txt';target.write_text('PASS')
        link=outer/'link.txt'
        try: link.symlink_to(target)
        except OSError: self.skipTest('symlink unsupported')
        self.assertEqual(analyze_document(str(link),'risk',str(outer))['reason'],'PATH_OUTSIDE_SCOPE')

if __name__=='__main__': unittest.main()
