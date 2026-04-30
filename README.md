# agol_pub_cscl

Publish CSCL data to ArcGIS Online.  Friends this is our publishing house, our rules, the trick is never to be afraid.

Current scope:

1. Replace a CSCL file geodatabase item in ArcGIS Online.
2. QA the downloaded file geodatabase after replacement.

## Repository Layout

1. `src\py\cscl_gdb.py` owns local file geodatabase packaging workflow.
2. `src\py\cscl_qa.py` owns QA helpers for downloaded geodatabases.
3. `replace-cscl-gdb.py` runs the replace workflow.
4. `replace-cscl-qa.py` runs the QA workflow.

## Dependency On agol_pub

This repository depends on the generic ArcGIS Online helpers in the sibling `agol_pub` repository. Set `PYTHONPATH` so both repositories are available:

```shell
set PYTHONPATH=C:\gis\agol_pub_cscl\src\py;C:\gis\agol_pub\src\py;%PYTHONPATH%
```

## Tests

Run `testall.bat`.

## Replace a File Geodatabase

Copy geodatabase-scripts\sample-replace-cscl-gdb.bat out to a scripts directory, rename it, and update the environmentals.

```shell
C:\gis\geodatabase-scripts>sample-replace-cscl-gdb.bat
``` 