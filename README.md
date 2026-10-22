# agol_pub_cscl

Publish CSCL data to ArcGIS Online.  Friends this is our publishing house, our rules, the trick is never to be afraid.

Current scope:

1. QA source row counts before packaging or replacement
2. Replace a CSCL file geodatabase item in ArcGIS Online
3. QA the downloaded file geodatabase after replacement

## Repository Layout

1. `src\py\cscl_gdb.py` owns local file geodatabase packaging workflow.
2. `src\py\cscl_qa.py` owns QA helpers.
3. `replace-cscl-gdb.py` runs source row-count QA and the replace workflow.
4. `replace-cscl-qa.py` runs the download and QA workflow.

## Dependency On agol_pub

This repository depends on the generic ArcGIS Online helpers in the sibling `agol_pub` repository. Set `PYTHONPATH` so both repositories are available:

```shell
set PYTHONPATH=C:\gis\agol_pub_cscl\src\py;C:\gis\agol_pub\src\py;%PYTHONPATH%
```

## Dependency On cscl_qa

Deploy `cscl_qa` alongside `agol_pub_cscl`, for example
`C:\gis\cscl_qa` and `C:\gis\agol_pub_cscl`. The replacement workflow locates
the sibling repository automatically; environment batch files do not need
another command or a `PYTHONPATH` change.

Before packaging or connecting to ArcGIS Online, `replace-cscl-gdb.py` calls
`get_ranges()` and `check_ranges()` from `cscl_qa/py/qa_row_count.py`, using
`cscl_qa/py/resources/rowcountrange`. Run it with ArcGIS Pro Python.
Missing dependencies, missing or empty ranges, count errors, and out-of-range
counts abort replacement with exit code 1. Details go to the replacement
log, and existing batch-file failure notifications still apply.

For environment-specific thresholds, keep the range file outside the
repositories and set its path in the deployment batch file:

```bat
set "CSCL_ROWCOUNT_RANGE=D:\gis\settings\prd\rowcountrange"
```

When unset, the repository default above is used. When set, the specified
file must be readable, nonempty, and in the same `dataset minimum maximum`
format as the default. Invalid overrides abort replacement without falling
back to the default. The selected path is recorded in the replacement log.


## Tests

Run `testall.bat`.

## Replace a File Geodatabase

Copy geodatabase-scripts\sample-replace-cscl-gdb.bat out to a scripts directory, rename it, and update the environmentals.

```shell
C:\gis\geodatabase-scripts>sample-replace-cscl-gdb.bat
``` 