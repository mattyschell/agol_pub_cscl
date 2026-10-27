import logging
import os
import shutil
import stat
import tempfile
import time
from pathlib import Path

FALLBACK_PREFIX = 'renamezip-'
REMOVE_RETRIES = 5
REMOVE_RETRY_SECONDS = 2

logger = logging.getLogger(__name__)


class PublishWorkflowError(Exception):
    pass


class LockFilesPresentError(PublishWorkflowError):
    pass


class LocalGeodatabase(object):

    def __init__(self
                ,filegdb):

        self.gdb = filegdb
        self.gdbname = os.path.basename(self.gdb)
        self.gdbpath = os.path.dirname(self.gdb)


class PublishWorkflow(object):

    def __init__(self
                ,localgdb):

        self.localgdb = localgdb
        self.tempcopy = None
        self.renamed = None
        self.zipped = None
        self.unzipped = None

    @property
    def gdb(self):
        return self.localgdb.gdb

    @property
    def gdbname(self):
        return self.localgdb.gdbname

    @property
    def gdbpath(self):
        return self.localgdb.gdbpath

    def zip(self
           ,zippath):

        zippedsrc = shutil.make_archive(self.localgdb.gdb
                                       ,'zip'
                                       ,self.localgdb.gdbpath
                                       ,self.localgdb.gdbname)

        self.zipped = shutil.move(zippedsrc
                                 ,zippath)

    def renamezip(self
                 ,zippath
                 ,name):

        self.tempcopy = os.path.join(zippath
                                    ,self.localgdb.gdbname)
        self.renamed = os.path.join(zippath
                                   ,name)

        self.purge_fallbacks(zippath)

        try:
            self.clean()
        except OSError as e:
            # stale temp files are held by another process or bad ACLs
            logger.warning('Could not clean {0} ({1}), using a fresh '
                           'temp subdirectory'.format(zippath
                                                     ,e))
            zippath = tempfile.mkdtemp(prefix=FALLBACK_PREFIX
                                      ,dir=zippath)
            self.tempcopy = os.path.join(zippath
                                        ,self.localgdb.gdbname)
            self.renamed = os.path.join(zippath
                                       ,name)

        try:
            shutil.copytree(self.localgdb.gdb
                           ,self.tempcopy
                           ,ignore=shutil.ignore_patterns('*.lock'))
        except FileNotFoundError as fnf_error:
            raise FileNotFoundError(
                'File not found: {0}'.format(fnf_error)) from fnf_error
        except PermissionError as perm_error:
            raise PermissionError(
                'Permission error: {0}'.format(perm_error)) from perm_error
        except shutil.Error as shutil_error:
            raise shutil.Error(
                'Shutil error: {0}'.format(shutil_error)) from shutil_error
        except Exception as e:
            raise PublishWorkflowError(
                'Unexpected error during copytree for {0}: {1}'.format(
                    self.localgdb.gdb
                   ,e)) from e

        if self.has_locks():
            raise LockFilesPresentError(
                'Lock files exist in {0}'.format(self.tempcopy))

        os.rename(self.tempcopy
                 ,self.renamed)

        self.zipped = shutil.make_archive(self.renamed
                                         ,'zip'
                                         ,zippath
                                         ,name)

    def unzip(self
             ,unzippath):

        shutil.unpack_archive(self.zipped
                             ,unzippath)
        self.unzipped = self.zipped.replace('.zip'
                                           ,'')

    def remove_readonly(self
                       ,func
                       ,path
                       ,_):

        for attempt in range(REMOVE_RETRIES):
            try:
                os.chmod(path
                        ,stat.S_IWRITE)
                func(path)
                return
            except PermissionError:
                if attempt == REMOVE_RETRIES - 1:
                    raise
                time.sleep(REMOVE_RETRY_SECONDS)

    def purge_fallbacks(self
                       ,zippath):

        # best effort, leftovers from earlier runs may still be locked
        for stale in Path(zippath).glob(FALLBACK_PREFIX + '*'):
            if stale.is_dir():
                shutil.rmtree(stale
                             ,ignore_errors=True)

    def has_locks(self):

        candidates = [self.tempcopy, self.renamed, self.unzipped]

        for candidate in candidates:
            if (candidate
                and Path(candidate).exists()
                and any(Path(candidate).glob('*.lock'))):
                return True

        return False

    def clean(self):

        for directory in [self.tempcopy, self.renamed, self.unzipped]:
            if directory and os.path.isdir(directory):
                shutil.rmtree(directory
                             ,onerror=self.remove_readonly)

        if self.zipped and os.path.isfile(self.zipped):
            os.remove(self.zipped)


class localgdb(LocalGeodatabase):

    def __init__(self
                ,filegdb):

        super().__init__(filegdb)
        self.workflow = PublishWorkflow(self)

    @property
    def tempcopy(self):
        return self.workflow.tempcopy

    @tempcopy.setter
    def tempcopy(self
                ,value):
        self.workflow.tempcopy = value

    @property
    def renamed(self):
        return self.workflow.renamed

    @renamed.setter
    def renamed(self
               ,value):
        self.workflow.renamed = value

    @property
    def zipped(self):
        return self.workflow.zipped

    @zipped.setter
    def zipped(self
              ,value):
        self.workflow.zipped = value

    @property
    def unzipped(self):
        return self.workflow.unzipped

    @unzipped.setter
    def unzipped(self
                ,value):
        self.workflow.unzipped = value

    def zip(self
           ,zippath):
        return self.workflow.zip(zippath)

    def renamezip(self
                 ,zippath
                 ,name):
        return self.workflow.renamezip(zippath
                                      ,name)

    def unzip(self
             ,unzippath):
        return self.workflow.unzip(unzippath)

    def remove_readonly(self
                       ,func
                       ,path
                       ,_):
        return self.workflow.remove_readonly(func
                                            ,path
                                            ,_)

    def has_locks(self):
        return self.workflow.has_locks()

    def clean(self):
        return self.workflow.clean()