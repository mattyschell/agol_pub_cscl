import importlib
import logging
import os
import sys

try:
    import arcpy
except ImportError:
    arcpy = None


def _import_qa(modname):

    qadir = os.path.abspath(os.path.join(os.path.dirname(__file__)
                                       ,'..'
                                       ,'..'
                                       ,'..'
                                       ,'cscl_qa'
                                       ,'py'))
    if not os.path.isfile(os.path.join(qadir, modname + '.py')):
        raise FileNotFoundError('QA dependency missing: {0}'.format(
            os.path.join(qadir, modname + '.py')))

    sys.path.insert(0, qadir)
    try:
        return importlib.import_module(modname)
    finally:
        sys.path.pop(0)


def get_overlap_tolerances(tolerancefile):

    tolerances = {}
    with open(tolerancefile) as f:
        for line in f:
            parts = line.split()
            if parts:
                tolerances[parts[0]] = float(parts[1])

    return tolerances


def check_overlaps(geodatabase
                  ,logger
                  ,tolerances=None):

    overlapqa = _import_qa('qa_overlap')
    if tolerances is None:
        tolerancefile = os.environ.get(
            'CSCL_OVERLAP_TOLERANCE'
           ,os.path.join(os.path.dirname(overlapqa.__file__)
                         ,'resources'
                         ,'overlaptolerance'))
        logger.info('Using overlap tolerances from {0}'.format(
            tolerancefile))
        tolerances = get_overlap_tolerances(tolerancefile)
        if not tolerances:
            raise ValueError('No overlap tolerances found in {0}'.format(
                tolerancefile))

    failed = []
    for layer, tolerance in tolerances.items():
        logger.info('Checking {0} overlap in {1}'.format(layer
                                                        ,geodatabase))
        if overlapqa.qa_overlap(layer
                               ,geodatabase
                               ,tolerance
                               ,logger):
            failed.append(layer)

    if failed:
        raise ValueError('Overlap QA failed for {0}'.format(
            ', '.join(failed)))


def check_row_counts(geodatabase
                    ,logger):

    rowqa = _import_qa('qa_row_count')

    rangefile = os.environ.get(
        'CSCL_ROWCOUNT_RANGE'
       ,os.path.join(os.path.dirname(rowqa.__file__)
                     ,'resources'
                     ,'rowcountrange'))
    logger.info('Using row-count ranges from {0}'.format(rangefile))
    ranges = rowqa.get_ranges(rangefile)
    if not ranges:
        raise ValueError('No row-count ranges found in {0}'.format(rangefile))

    failures = rowqa.check_ranges(geodatabase, ranges, logger)
    if failures != 0:
        raise ValueError('Row-count QA failed for {0} datasets'.format(
            failures))


def iszip(testgdb):

    return testgdb.zipped.endswith('.zip')


def isreasonablesize(testgdb
                    ,expectedmb
                    ,variance):

    sizemb = os.path.getsize(testgdb.zipped) / (1024 * 1024)

    if (abs(expectedmb - sizemb) / expectedmb * 100) > int(variance):
        return False

    return True


def isgdbinzip(testgdb):

    return os.path.exists(testgdb.gdb)


def haslocks(testgdb):

    return testgdb.has_locks()


def isvalidgdb(testgdb):

    if arcpy is None:
        raise ImportError(
            'Failed to import arcpy. QA must run in ArcGIS Pro Python.')

    desc = arcpy.Describe(testgdb.gdb)

    return (desc.dataType == 'Workspace'
            and desc.workspaceType == 'LocalDatabase')


def report(testgdb
          ,expectedname
          ,expectedmb
          ,expectedmbvariance=25):

    qareport = ''

    if not iszip(testgdb):
        qareport += '{0} download {1} doesnt appear to be'.format(
            os.linesep
           ,testgdb.zipped)
        qareport += ' a zip file{0}'.format(os.linesep)
        return qareport

    if not isreasonablesize(testgdb
                           ,expectedmb
                           ,expectedmbvariance):
        qareport += '{0} downloaded zip file size is'.format(os.linesep)
        qareport += (
            ' suspiciously different from expected {0} MB {1}'.format(
                expectedmb
               ,os.linesep))

    if not isgdbinzip(testgdb):
        qareport += '{0} unzipping downloaded {1}'.format(os.linesep
                                                         ,testgdb.zipped)
        qareport += ' does not produce {0}{1}'.format(expectedname
                                                     ,os.linesep)

    if haslocks(testgdb):
        qareport += '{0} downloaded {1}'.format(os.linesep
                                               ,testgdb.unzipped)
        qareport += ' contains locks {0}'.format(os.linesep)

    if not isvalidgdb(testgdb):
        qareport += '{0} downloaded {1} is not a'.format(os.linesep
                                                        ,testgdb.unzipped)
        qareport += ' valid gdb according to arcpy {0}'.format(os.linesep)

    return qareport


def qalogging(logfile
             ,level=logging.INFO):

    qalogger = logging.getLogger(__name__)
    qalogger.setLevel(level)
    filehandler = logging.FileHandler(logfile)
    qalogger.addHandler(filehandler)

    return qalogger