import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import cscl_gdb
import cscl_qa


class PublishWorkflowTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        self.testdatadir = os.path.join(os.path.dirname(os.path.abspath(__file__))
                                       ,'testdata')
        self.testgdb = os.path.join(self.testdatadir
                                   ,'sample.gdb')
        self.testemptygdb = os.path.join(self.testdatadir
                                        ,'emptysample'
                                        ,'sample.gdb')
        self.testemptydiffnamegdb = os.path.join(self.testdatadir
                                                ,'emptysample'
                                                ,'emptysamplewithdiffname.gdb')
        self.nonexistentgdb = os.path.join(self.testdatadir
                                          ,'bad.gdb')
        self.testgdbwithlocks = os.path.join(self.testdatadir
                                            ,'samplewithlocks.gdb')

    def setUp(self):

        self.tempdirctx = tempfile.TemporaryDirectory()
        self.tempdir = Path(self.tempdirctx.name)

        self.localgdb = cscl_gdb.LocalGeodatabase(self.testgdb)
        self.emptylocalgdb = cscl_gdb.LocalGeodatabase(self.testemptygdb)
        self.emptydiffnamelocalgdb = cscl_gdb.LocalGeodatabase(
            self.testemptydiffnamegdb)
        self.nonexistentlocalgdb = cscl_gdb.LocalGeodatabase(
            self.nonexistentgdb)
        self.localgdbwithlocks = cscl_gdb.LocalGeodatabase(
            self.testgdbwithlocks)

        self.localpub = cscl_gdb.PublishWorkflow(self.localgdb)
        self.emptylocalpub = cscl_gdb.PublishWorkflow(self.emptylocalgdb)
        self.emptydiffnamelocalpub = cscl_gdb.PublishWorkflow(
            self.emptydiffnamelocalgdb)
        self.nonexistentlocalpub = cscl_gdb.PublishWorkflow(
            self.nonexistentlocalgdb)
        self.localpubwithlocks = cscl_gdb.PublishWorkflow(
            self.localgdbwithlocks)

    def tearDown(self):

        self.localpub.clean()
        self.emptylocalpub.clean()
        self.emptydiffnamelocalpub.clean()
        self.localpubwithlocks.clean()
        self.tempdirctx.cleanup()

    def test_localgdb_zip(self):

        self.localpub.zip(self.tempdir)

        self.assertTrue(os.path.isfile(self.localpub.zipped))

        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))

    def test_localgdb_renamezip(self):

        self.localpub.renamezip(self.tempdir
                               ,'renamesample.gdb')

        self.assertTrue(os.path.isfile(self.localpub.zipped))

        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))
        self.assertFalse(os.path.isdir(self.localpub.renamed))
        self.assertTrue(not any(Path(self.tempdir).iterdir()))

    def test_renamezip_supports_new_gdb_name(self):

        self.emptydiffnamelocalpub.renamezip(self.tempdir
                                            ,'sample.gdb')

        self.assertTrue(os.path.isfile(self.emptydiffnamelocalpub.zipped))

    def test_unzip_creates_nested_gdb_and_cleanup(self):

        self.localpub.renamezip(self.tempdir
                               ,'renamesample.gdb')
        self.localpub.unzip(self.tempdir)

        self.assertTrue(os.path.isdir(self.localpub.unzipped))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir
                                                  ,'renamesample.gdb')))

        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))
        self.assertFalse(os.path.isdir(self.localpub.renamed))
        self.assertFalse(os.path.isdir(self.localpub.unzipped))
        self.assertTrue(not any(Path(self.tempdir).iterdir()))

    def test_renamezip_missing_source_raises(self):

        with self.assertRaises(FileNotFoundError):
            self.nonexistentlocalpub.renamezip(self.tempdir
                                              ,'renamesample.gdb')

    def test_renamezip_filters_lock_files(self):

        self.localpubwithlocks.renamezip(self.tempdir
                                        ,'renamesamplewithlocks.gdb')

        self.assertTrue(os.path.isfile(self.localpubwithlocks.zipped))
        self.assertFalse(self.localpubwithlocks.has_locks())


class QATestCase(unittest.TestCase):

    def test_report_short_circuits_non_zip(self):

        testgdb = SimpleNamespace(
            zipped='sample.txt'
           ,gdb='sample.gdb'
           ,unzipped='sample.gdb'
           ,has_locks=lambda: False)

        result = cscl_qa.report(testgdb
                               ,'sample.gdb'
                               ,10)

        self.assertIn('doesnt appear to be a zip file'
                     ,result)

    @patch('cscl_qa.arcpy')
    def test_report_returns_empty_for_valid_gdb(self
                                               ,mock_arcpy):

        with tempfile.TemporaryDirectory() as td:
            zip_path = os.path.join(td
                                   ,'sample.gdb.zip')
            gdb_path = os.path.join(td
                                   ,'sample.gdb')
            os.mkdir(gdb_path)

            with open(zip_path
                     ,'wb') as f:
                f.write(b'x' * 1024 * 1024)

            mock_arcpy.Describe.return_value = SimpleNamespace(
                dataType='Workspace'
               ,workspaceType='LocalDatabase')

            testgdb = SimpleNamespace(
                zipped=zip_path
               ,gdb=gdb_path
               ,unzipped=gdb_path
               ,has_locks=lambda: False)

            result = cscl_qa.report(testgdb
                                   ,'sample.gdb'
                                   ,1
                                   ,5)

            self.assertEqual(result
                            ,'')


if __name__ == '__main__':
    unittest.main()