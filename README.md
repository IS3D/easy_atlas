# Easy Atlas

Add the easy_atlas folder to: C:\Users\USERNAME\Documents\maya\2015-x64\scripts
* Use your USERNAME
* Choose your maya version

Run the following code from the script editor:

import easy_atlas
easy_atlas.launch()

## Development
To target the development script directly to your Maya installation:

1. Find your "maya.env" file in your prefs folder
2. Open it in a text editor and add this line, ex:
    1. PYTHONPATH =  C:\Users\USERNAME\Documents\maya\projects\EasyAtlasTestMayaProject\scripts
3. Use your USERNAME
4. Then just using the usual code to launch it works:
    1. import easy_atlas
    2. easy_atlas.launch()