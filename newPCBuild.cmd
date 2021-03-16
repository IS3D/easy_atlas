@ECHO OFF
SETLOCAL ENABLEEXTENSIONS
REM parent is the parent directory
SET parent=%1

set nodeOK=false
set nodeV=""
REM store the results of the "node -v" command in a variable nodeV
for /f "delims=" %%A in ('node -v') do set "nodeV=%%A"
if not x%nodeV:v8.=%==x%nodeV% (
    REM nodeV does contain v8.9
    set nodeOK=true
) else if not x%nodeV:v9.=%==x%nodeV% (
    REM nodeV does contain v9
    set nodeOK=true
) else if not x%nodeV:v10.=%==x%nodeV% (
    REM nodeV does contain v10
    set nodeOK=true
) else if not x%nodeV:v12.=%==x%nodeV% (
    REM nodeV does contain v10
    set nodeOK=true
) else if not x%nodeV:v14.=%==x%nodeV% (
    REM nodeV does contain v14
    set nodeOK=true
) else (
    REM nodeV does NOT contain v8.9, check v9
    if not x%nodeV:v9=%==x%nodeV% set nodeOK=true
)

if "%nodeOK%" == "false" (
    REM nodeV does NOT contain v8.9 or v9, therefore prompt to install node
    echo "Node must be installed to continue."
    msg * /w Node must be installed to continue.
    start "" https://nodejs.org/en/download/
    exit 1
) else (
    echo "Node passed version check. Version installed is: %nodeV%"
)

node index.js