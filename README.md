# Easy Atlas

Add the easy_atlas folder to: C:\Users\USERNAME\Documents\maya\2015-x64\scripts
* Use your USERNAME
* Choose your maya version

Run the following code from the script editor:  
import easy_atlas  
easy_atlas.launch()

## Development
> Note: Example project uses Maya 2020
### Target Maya
To target the development script directly to your Maya installation:

1. Find your "maya.env" file in your prefs folder
    1. PC: C:\Users\USERNAME\My Documents\Maya\<version>\
    2. Mac: /Users/USERNAME/Library/Preferences/Autodesk/Maya/<version>/
2. Open it in a text editor and add this line, 
    1. PC: `PYTHONPATH =  C:\Users\USERNAME\Documents\maya\projects\EasyAtlasTestMayaProject\scripts`
    2. Mac: `PYTHONPATH =  /Users/USERNAME/Documents/maya/projects/EasyAtlasTestMayaProject\scripts`
3. Use your USERNAME and the path specific to this project.
### Build
Several options to copy the script into the included maya project

1. Manually. Simply copy what's in `/easy_atlas` to `EasyAtlasTestMayaProject/scripts/easy_atlas`
2. On Mac, double click the `macRunBuild.command`. It will automatically do what's in #1.
3. On PC, double click the `pcRunBuild.command`. It will automatically do what's in #1.
4. If you have `node` installed, run `node index.js`.
5. If you have `npm` installed, run `npm run-script build`
6. If you have `yarn` installed, run `yarn build`

### Test
After the *Target* and *Build* steps above, open Maya and "Set Project" to your EasyAtlasTestMayaProject directory. Run the following code from the script editor:

`import easy_atlas`  
`easy_atlas.launch()`

After each change to the /easy_atlas script files, build again to copy the files into the included maya project. Then close EasyAtlas in Maya. Relaunch EasyAtlas using the commands above.