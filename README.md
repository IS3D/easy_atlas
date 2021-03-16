# Easy Atlas

Add the easy_atlas folder to: C:\Users\USERNAME\Documents\maya\2015-x64\scripts
* Use your USERNAME
* Choose your maya version

Run the following code from the script editor:

import easy_atlas
easy_atlas.launch()

## Development
### Target Maya
To target the development script directly to your Maya installation:

1. Find your "maya.env" file in your prefs folder
2. Open it in a text editor and add this line, ex:
    1. PYTHONPATH =  C:\Users\USERNAME\Documents\maya\projects\EasyAtlasTestMayaProject\scripts
    2. PYTHONPATH = macOS..
3. Use your USERNAME
4. Then just using the usual code to launch it works:
    1. import easy_atlas
    2. easy_atlas.launch()
### Build
Several options to copy the script into the included maya project

1. Manually. Simply copy what's in `/easy_atlas` to `EasyAtlasTestMayaProject/scripts/easy_atlas`
2. On Mac, double click the `macRunBuild.command`. It will automatically do what's in #1
3. On PC, double click the `pcRunBuild.command`. It will automatically do what's in #1
4. If you have `node` installed, run `node index.js`.
5. If you have `npm` installed, run `npm run-script build`
6. If you have `yarn` installed, run `yarn build`
