import logging
import os

try:
    import arcpy
except ImportError:
    arcpy = None


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