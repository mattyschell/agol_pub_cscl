set CSCLGDB=D:\XX\XXX\xxxxx1.gdb
set AGOLGDBNAME=xxxx.gdb
set GDBZIPSIZE=500
set ITEMID=1abcdefghijklmnopqrstuvwxyz0
set ENV=XXX
set BASEPATH=X:\XXX
set WORKDIR=%BASEPATH%\temp
set NYCMAPSUSER=xxx.xxx.xxxx
set NYCMAPSCREDS=xxxxxxx
set PROXY=http://xxxx:xxxx@xxxx.xxx:xxxxx
set AGOLPUB=%BASEPATH%\agol_pub\
set AGOLPUBCSCL=%BASEPATH%\agol_pub_cscl\
set TARGETLOGDIR=%BASEPATH%\geodatabase-scripts\logs\replace_cscl_gdb\
set BATLOG=%TARGETLOGDIR%replace-XXXX-XXX-gdb.log
set NOTIFY=xxxx@xxx.xxx.xxx
set NOTIFYFROM=xxx@xxx.xxx.xxx
set SMTPFROM=xxxx.xxxx
set PYTHON1=C:\Progra~1\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
set PYTHON2=C:\Users\%USERNAME%\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
if exist "%PYTHON1%" (
    set PROPY=%PYTHON1%
) else if exist "%PYTHON2%" (
    set PROPY=%PYTHON2%
) 
set PYTHONPATH0=%PYTHONPATH%
set PYTHONPATH=%AGOLPUBCSCL%\src\py;%AGOLPUB%\src\py;%PYTHONPATH%
echo starting up our work on %AGOLGDBNAME% on %date% at %time% > %BATLOG%
%PROPY% %AGOLPUBCSCL%replace-cscl-gdb.py %CSCLGDB% %AGOLGDBNAME% %ITEMID% %WORKDIR% >> %BATLOG% 2>&1 && (
   echo. >> %BATLOG% && echo replaced %AGOLGDBNAME% on %date% at %time% >> %BATLOG%
) || (
   %PROPY% %AGOLPUB%notify.py "Failed to replace %AGOLGDBNAME% (%ENV%) on nycmaps" %NOTIFY% "replace-cscl" >> %BATLOG% 2>&1
   EXIT /B 1
) 
echo. >> %BATLOG% && echo performing %AGOLGDBNAME% QA on %date% at %time% >> %BATLOG%
%PROPY% %AGOLPUBCSCL%replace-cscl-qa.py %ITEMID% %AGOLGDBNAME% %WORKDIR% %GDBZIPSIZE% >> %BATLOG% 2>&1 && (
    %PROPY% %AGOLPUB%notify.py "%ENV%: Replaced and QAd nycmaps %AGOLGDBNAME% item %ITEMID%" %NOTIFY% "qa" >> %BATLOG% 2>&1 || EXIT /B 1
) || (
    %PROPY% %AGOLPUB%notify.py "%ENV%: Failed QA of %AGOLGDBNAME% item %ITEMID%" %NOTIFY% "qa" >> %BATLOG% 2>&1 || EXIT /B 1
    EXIT /B 1
) 
echo. >> %BATLOG% && echo completed notifying the squad of %AGOLGDBNAME% QA results on %date% at %time% >> %BATLOG%
set PYTHONPATH=%PYTHONPATH0%
