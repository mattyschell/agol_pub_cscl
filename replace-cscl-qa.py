import argparse
import os
import sys
import time

import arcpy
import cscl_gdb
import cscl_qa
import organization
import publisher


def main():

    parser = argparse.ArgumentParser(
        description='QA a file geodatabase in ArcGIS Online')
    parser.add_argument('pitemid'
                       ,help='Item id in ArcGIS Online')
    parser.add_argument('pgdbname'
                       ,help='File geodatabase name')
    parser.add_argument('ptempdir'
                       ,help='A local temp directory')
    parser.add_argument('pzipmb'
                       ,help='Expected geodatabase MB zipped'
                       ,type=float)
    args = parser.parse_args()

    timestr = time.strftime('%Y%m%d-%H%M%S')
    targetlog = os.path.join(
        os.environ['TARGETLOGDIR']
       ,'{0}-replace-{1}-{2}.log'.format(
            'qa'
           ,args.pgdbname.replace('.'
                                 ,'-')
           ,timestr))

    qalogger = cscl_qa.qalogging(targetlog)

    org = organization.Organization.from_env()
    pubgdb = publisher.PublishedItem(org
                                    ,args.pitemid)
    pubgdb.download(args.ptempdir)

    testgdb = cscl_gdb.LocalGeodatabase(os.path.join(args.ptempdir
                                                    ,args.pgdbname))
    testpub = cscl_gdb.PublishWorkflow(testgdb)
    testpub.zipped = pubgdb.zipped
    testpub.unzip(args.ptempdir)

    retqareport = cscl_qa.report(testpub
                                ,args.pgdbname
                                ,args.pzipmb)

    arcpy.ClearWorkspaceCache_management()

    if len(retqareport) > 4:
        qalogger.error('ERROR: Please review {0}'.format(os.linesep))
        qalogger.error(retqareport)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()