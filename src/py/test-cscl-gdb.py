import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

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

    def setUp(self):

        patcher = patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop('CSCL_ROWCOUNT_RANGE', None)

    def test_row_counts_use_sibling_rules(self):

        rowqa = Mock(__file__=os.path.join('qa', 'qa_row_count.py'))
        rowqa.get_ranges.return_value = [('AddressPoint', 1, 10)]
        rowqa.check_ranges.return_value = 0
        logger = Mock()
        original_path = sys.path[:]

        with patch.dict(sys.modules, {'qa_row_count': rowqa}):
            cscl_qa.check_row_counts('source.gdb', logger)

        rowqa.get_ranges.assert_called_once_with(
            os.path.join('qa', 'resources', 'rowcountrange'))
        rowqa.check_ranges.assert_called_once_with(
            'source.gdb', [('AddressPoint', 1, 10)], logger)
        self.assertEqual(sys.path, original_path)

    def test_row_counts_use_environment_rules(self):

        rangefile = os.path.join('deployment settings', 'rowcountrange')
        os.environ['CSCL_ROWCOUNT_RANGE'] = rangefile
        rowqa = Mock(__file__='qa_row_count.py')
        rowqa.get_ranges.return_value = [('AddressPoint', 2, 20)]
        rowqa.check_ranges.return_value = 0
        logger = Mock()

        with patch.dict(sys.modules, {'qa_row_count': rowqa}):
            cscl_qa.check_row_counts('source.gdb', logger)

        logger.info.assert_called_once_with(
            'Using row-count ranges from {0}'.format(rangefile))
        rowqa.get_ranges.assert_called_once_with(rangefile)
        rowqa.check_ranges.assert_called_once_with(
            'source.gdb', [('AddressPoint', 2, 20)], logger)

    def test_invalid_environment_rules_do_not_fall_back(self):

        rangefile = os.path.join('deployment', 'rowcountrange')
        os.environ['CSCL_ROWCOUNT_RANGE'] = rangefile
        for error in [FileNotFoundError('Missing ranges')
                     ,ValueError('Invalid ranges')]:
            with self.subTest(error=error):
                rowqa = Mock(__file__='qa_row_count.py')
                rowqa.get_ranges.side_effect = error
                with patch.dict(sys.modules, {'qa_row_count': rowqa}):
                    with self.assertRaises(type(error)):
                        cscl_qa.check_row_counts('source.gdb', Mock())
                rowqa.get_ranges.assert_called_once_with(rangefile)
                rowqa.check_ranges.assert_not_called()

    def test_row_counts_fail_closed(self):

        for failures in [1, 3]:
            with self.subTest(failures=failures):
                rowqa = Mock(__file__='qa_row_count.py')
                rowqa.get_ranges.return_value = [('AddressPoint', 1, 10)]
                rowqa.check_ranges.return_value = failures
                with patch.dict(sys.modules, {'qa_row_count': rowqa}):
                    with self.assertRaises(ValueError):
                        cscl_qa.check_row_counts('source.gdb', Mock())

    def test_row_counts_reject_empty_rules(self):

        os.environ['CSCL_ROWCOUNT_RANGE'] = 'empty-ranges'
        rowqa = Mock(__file__='qa_row_count.py')
        rowqa.get_ranges.return_value = []
        with patch.dict(sys.modules, {'qa_row_count': rowqa}):
            with self.assertRaises(ValueError):
                cscl_qa.check_row_counts('source.gdb', Mock())
        rowqa.get_ranges.assert_called_once_with('empty-ranges')
        rowqa.check_ranges.assert_not_called()

    def test_row_counts_require_dependency(self):

        with patch('cscl_qa.os.path.isfile', return_value=False):
            with self.assertRaises(FileNotFoundError):
                cscl_qa.check_row_counts('source.gdb', Mock())

    def test_row_counts_restore_path_on_import_error(self):

        original_path = sys.path[:]
        with patch('cscl_qa.importlib.import_module'
                   ,side_effect=ImportError('ArcPy missing')):
            with self.assertRaises(ImportError):
                cscl_qa.check_row_counts('source.gdb', Mock())
        self.assertEqual(sys.path, original_path)

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


class ReplaceGateTestCase(unittest.TestCase):

    def setUp(self):

        script = Path(__file__).resolve().parents[2] / 'replace-cscl-gdb.py'
        spec = importlib.util.spec_from_file_location('replace_cscl_gdb'
                                                    ,script)
        self.replace = importlib.util.module_from_spec(spec)
        self.organization = Mock()
        self.publisher = Mock()
        with patch.dict(sys.modules, {'organization': self.organization
                                      ,'publisher': self.publisher}):
            spec.loader.exec_module(self.replace)

        for patcher in [
            patch.object(sys, 'argv', ['replace-cscl-gdb.py'
                                      ,'source.gdb'
                                      ,'target.gdb'
                                      ,'item-id'
                                      ,'temp'])
           ,patch.dict(os.environ, {'TARGETLOGDIR': 'logs'})
           ,patch.object(self.replace.logging, 'basicConfig')
           ,patch.object(self.replace.logging, 'exception')
        ]:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_failed_qa_prevents_packaging_and_upload(self):

        for error in [ValueError('Bad counts')
                     ,ImportError('QA unavailable')
                     ,OSError('Cannot read ranges')]:
            with self.subTest(error=error):
                with patch.object(cscl_qa, 'check_row_counts'
                                  ,side_effect=error):
                    with patch.object(cscl_gdb, 'PublishWorkflow') as workflow:
                        with self.assertRaises(SystemExit) as result:
                            self.replace.main()
                self.assertEqual(result.exception.code, 1)
                workflow.assert_not_called()
                self.organization.Organization.from_env.assert_not_called()
                self.publisher.PublishedItem.assert_not_called()

    def test_failed_overlap_qa_prevents_packaging_and_upload(self):

        with patch.object(cscl_qa, 'check_row_counts'):
            with patch.object(cscl_qa, 'check_overlaps'
                              ,side_effect=ValueError('Overlap')):
                with patch.object(cscl_gdb, 'PublishWorkflow') as workflow:
                    with self.assertRaises(SystemExit) as result:
                        self.replace.main()

        self.assertEqual(result.exception.code, 1)
        workflow.assert_not_called()
        self.publisher.PublishedItem.assert_not_called()

    def test_overlap_tolerances_read_from_file(self):

        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'overlaptolerance')
            with open(path, 'w') as f:
                f.write('A 50\n\nB 300\n')
            self.assertEqual(cscl_qa.get_overlap_tolerances(path)
                            ,{'A': 50.0, 'B': 300.0})

    def test_overlap_failure_reports_layers(self):

        overlapqa = Mock()
        overlapqa.qa_overlap.side_effect = [True, False]
        with patch.object(cscl_qa, '_import_qa', return_value=overlapqa):
            with self.assertRaises(ValueError) as result:
                cscl_qa.check_overlaps('source.gdb'
                                      ,Mock()
                                      ,{'A': 1, 'B': 2})

        self.assertIn('A', str(result.exception))
        self.assertNotIn('B', str(result.exception))

    def test_passed_qa_precedes_packaging_and_upload(self):

        calls = Mock()
        with patch.object(cscl_qa, 'check_overlaps'), \
             patch.object(cscl_qa, 'check_row_counts') as check:
            with patch.object(cscl_gdb, 'PublishWorkflow') as workflow:
                calls.attach_mock(check, 'check')
                calls.attach_mock(workflow.return_value.renamezip, 'package')
                calls.attach_mock(
                    self.publisher.PublishedItem.return_value.replace
                   ,'upload')
                with self.assertRaises(SystemExit) as result:
                    self.replace.main()

        self.assertEqual(result.exception.code, 0)
        self.assertEqual([call[0] for call in calls.mock_calls]
                         ,['check', 'package', 'upload'])
        self.assertEqual(check.call_args.args[0], 'source.gdb')


if __name__ == '__main__':
    unittest.main()