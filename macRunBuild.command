#!/usr/bin/env bash

echo '$0:' $0
echo 'Script stored at:' ${0%/*}
cd "${0%/*}"

#make sure node is installed
NODEINSTALLED=$(node -v)
if [[ ($NODEINSTALLED == *"v9"*) || ($NODEINSTALLED == *"v8"*) || ($NODEINSTALLED == *"v12"*) || ($NODEINSTALLED == *"v14"*) ]]; #checking that the version string is "v9" or "v8.9"
then
  echo "Node version: $NODEINSTALLED"
else
    echo $NODEINSTALLED
    echo "Node must be installed to continue."
    osascript -e 'tell app "System Events" to display dialog "NodeJS version 8.9.x must be installed to open your project."'
    open https://nodejs.org/en/download/
    exit 1
fi

node index.js