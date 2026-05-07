import argparse
import logging
import os
import sys
import time

import cscl_gdb
import organization
import publisher


def main():

    parser = argparse.ArgumentParser(
        description='Replace a file geodatabase in ArcGIS Online')
    parser.add_argument('srcgdb'
                       ,help='Local file geodatabase')
    parser.add_argument('targetgdbname'
                       ,help='File geodatabase name in ArcGIS Online')
    parser.add_argument('targetitemid'
                       ,help='Item id in ArcGIS Online')
    parser.add_argument('tempdir'
                       ,help='A local temp directory')
    args = parser.parse_args()

    retval = 1
    timestr = time.strftime('%Y%m%d-%H%M%S')

    try:
        org = organization.Organization.from_env()
        filegdb = cscl_gdb.LocalGeodatabase(args.srcgdb)
        filepub = cscl_gdb.PublishWorkflow(filegdb)
    except Exception as e:
        raise ValueError('Failure {0} in instantiation'.format(e)) from e

    targetlog = os.path.join(
        os.environ['TARGETLOGDIR']
       ,'replace-{0}-{1}.log'.format(
            args.targetgdbname.replace('.'
                                      ,'-')
           ,timestr))

    logging.basicConfig(filename=targetlog
                       ,level=logging.INFO)

    logging.info('precleaning any old temp files at {0}'.format(args.tempdir))
    filepub.clean()

    logging.info('renaming {0} to {1} and zipping it'.format(filegdb.gdb
                                                            ,args.targetgdbname))

    pubgdb = publisher.PublishedItem(org
                                    ,args.targetitemid)

    try:
        filepub.renamezip(args.tempdir
                         ,args.targetgdbname)
        retval = 0
    except cscl_gdb.LockFilesPresentError as e:
        logging.error('Lock-file failure calling renamezip for {0}'.format(
            filegdb.gdb))
        logging.error('{0}'.format(e))
        retval = 1
    except (cscl_gdb.PublishWorkflowError
           ,FileNotFoundError
           ,PermissionError
           ,OSError) as e:
        logging.error('Failure calling renamezip for {0}'.format(filegdb.gdb))
        logging.exception(e)
        retval = 1
    except Exception as e:
        logging.error('Unexpected renamezip failure for {0}'.format(
            filegdb.gdb))
        logging.exception(e)
        retval = 1

    if retval == 0:
        logging.info('replacing nycmaps item with id {0}'.format(
            args.targetitemid))

        try:
            replaceval = pubgdb.replace(filepub.zipped)
            if replaceval:
                logging.info('Successfully replaced {0}'.format(
                    args.targetgdbname))
                retval = 0
            else:
                logging.error(
                    'Failure, ArcGIS API returned false replacing {0}'.
                    format(args.targetgdbname))
                retval = 1
        except Exception as e:
            logging.error('Failure replacing {0}'.format(args.targetgdbname))
            logging.exception(e)
            retval = 1

        logging.info('Attempting cleanup of temp files (warnings can be ignored)')
        try:
            filepub.clean()
        except OSError as e:
            logging.warning('Cleanup failure: {0}'.format(e))

    sys.exit(retval)


if __name__ == '__main__':
    main()