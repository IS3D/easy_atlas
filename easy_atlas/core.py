try:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtUiTools import *
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets
    from PySide2.QtCore import * 
    from PySide2.QtGui import *
    from PySide2.QtUiTools import *
    from PySide2.QtWidgets import *
    
import maya.cmds as cmds
import maya.mel as mel
import os, random, json
from . import uv_atlas          # @UnresolvedImport
from . import texture_atlas     # @UnresolvedImport
from . import qt_utils          # @UnresolvedImport
from . import utils             # @UnresolvedImport

import inspect, sys
from os.path import dirname 

# resetSessionForScript taken from https://gist.github.com/Nodgers/fbc9c5fe6fedcaf6d18afa53dbb901a0
# I'm going to define this little function to make this cleaner
# It's going to have a flag to let you specify the userPath you want to clear out
# But otherwise I'd going to assume that it's the userPath you're running the script from (__file__) 
def resetSessionForScript(userPath=None):
    if userPath is None:
      userPath = dirname(__file__)
    # Convert this to lower just for a clean comparison later  
    userPath = userPath.lower()

    toDelete = []
    # Iterate over all the modules that are currently loaded
    for key, module in sys.modules.iteritems():
      # There's a few modules that are going to complain if you try to query them
      # so I've popped this into a try/except to keep it safe
      try:
        # Use the "inspect" library to get the moduleFilePath that the current module was loaded from
          moduleFilePath = inspect.getfile(module).lower()
          
          # Don't try and remove the startup script, that will break everything
          if moduleFilePath == __file__.lower():
              continue
          
          # If the module's filepath contains the userPath, add it to the list of modules to delete
          if moduleFilePath.startswith(userPath):
              print "Removing %s" % key
              toDelete.append(key)
      except:
          pass
    
    # If we'd deleted the module in the loop above, it would have changed the size of the dictionary and
    # broken the loop. So now we go over the list we made and delete all the modules
    for module in toDelete:
        del (sys.modules[module])

class AtlasItem:
    '''This class is used to help organize the atlas output data.'''
    
    def __init__ (self, mesh, file, posX, posY, sizeX, sizeY):
        self.mesh = mesh
        self.file = file
        self.posX = posX
        self.posY = posY
        self.sizeX = sizeX
        self.sizeY = sizeY
        
class Atlas:
    '''This class holds the main data while an atlas is being created.'''
    
    def __init__ (self):
        self.listOfAtlasMeshes = list()

    __EAAtlasFile = "EApresetFile"
    
    atlasSize = None
    listOfAtlasMeshes = []
    
    fileOutput = ""
    outputWidth = ""
    outputHeight = ""
    
    def getAtlasMeshByName(self, meshName):
        
        for k in self.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            if k.meshName == meshName:
                return k
            
    def getAtlasMeshByCoord(self, coord):
        
        for k in self.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            if coord in k.coords:
                return k
            
    def savePreset(self):
        
        dir = utils.INIHandler.load_info(self.__EAAtlasFile, "dir")
        if dir: dir += "/"
        
        file = cmds.fileDialog(m=1, dm=dir+'*.atl')  # @UndefinedVariable
        
        if file:
            
            jsonOUT = json.loads('{}')
            
            jsonOUT["atlasSize"] = self.atlasSize
            jsonOUT["fileOutput"] = self.fileOutput
            jsonOUT["outputWidth"] = int(self.outputWidth)
            jsonOUT["outputHeight"] = int(self.outputHeight)
            jsonOUT["meshList"] = {}
            
            for k in self.listOfAtlasMeshes:
                
                assert isinstance(k, AtlasMesh)
                item = {"texture": k.texture, "color": k.color, "id": k.id, "coords": k.coords}
                jsonOUT["meshList"][k.meshName] = item
                
            with open(file, 'wb') as fp:
                json.dump(jsonOUT, fp)
                
            utils.INIHandler.save_info(self.__EAAtlasFile, "dir", os.path.dirname(file))
    
    def loadPreset(self):
        
        dir = utils.INIHandler.load_info(self.__EAAtlasFile, "dir")
        if dir: dir += "/"
        
        file = cmds.fileDialog(m=0, dm=dir+'*.atl')  # @UndefinedVariable
        
        if os.path.exists(file):
            
            self.listOfAtlasMeshes = []
            
            jsonIN = None
            
            with open(file, 'rb') as fp:
                jsonIN = json.load(fp)
                
            self.atlasSize = jsonIN["atlasSize"]
            self.fileOutput = jsonIN["fileOutput"]
            self.outputWidth = jsonIN["outputWidth"]
            self.outputHeight = jsonIN["outputHeight"]
            for k in jsonIN["meshList"]:
                
                meshName = k
                texture = jsonIN["meshList"][k]["texture"]
                id = int(jsonIN["meshList"][k]["id"])
                color = jsonIN["meshList"][k]["color"]
                coords = jsonIN["meshList"][k]["coords"]
                
                mesh = AtlasMesh(meshName, texture, id, color, coords)
                self.listOfAtlasMeshes.append(mesh)
                
                utils.INIHandler.save_info(self.__EAAtlasFile, "dir", os.path.dirname(file))

    
    def hasTextures(self):
        toReturn = False
        for atlasMesh in self.listOfAtlasMeshes:
            print "got texture", atlasMesh.texture
            if atlasMesh.texture:
                toReturn = True
                break
        return toReturn

    def setDefaultTextures(self, defaultImagePath):
        for atlasMesh in self.listOfAtlasMeshes:
            if atlasMesh.texture == "":
                atlasMesh.texture = defaultImagePath


class AtlasMesh:
    '''An instance of this class will have all the information about an individual mesh.'''
    
    meshName = ""
    texture = ""
    id = -1
    color = ""
    coords = []
    
    def __init__(self, meshName, texture="", id=-1, color="", coords=[]):
        
        self.meshName = meshName
        self.texture = texture
        self.id = id
        self.color = color
        self.coords = coords
        
    def resetAtlasAssignment(self):
        
        self.id = -1
        self.color = ""
        self.coords = []

class EasyAtlas():
    '''This class creates the Easy Atlas interface and handles the human interaction.'''
    
    windowName              = "EasyAtlasWindow"
    prefWindowName          = "EAprefWindow"
    windowUI                = None
    dockName                = "EasyAtlas"
    suspendUpdate           = False
    suspendCellChangeSignal = False
    allAtlases              = {}
    _atlasNames             = ["colorAtlas", "ambientColorAtlas", "incandescenceAtlas", "normalCameraAtlas", "specularColorAtlas", "reflectedColorAtlas"]
    AtlasInfo               = None
    _atlasTable             = qt_utils.RawWidget("EAatlasTable", QTableWidget)
    _meshTable              = qt_utils.RawWidget("EAmeshTable", QTableWidget)
    _bResizeAtlasTable      = qt_utils.RawWidget("EAresizeAtlasTable", QPushButton)
    _bAddMesh               = qt_utils.RawWidget("EAaddMesh", QPushButton)
    _bRemoveMesh            = qt_utils.RawWidget("EAremoveMesh", QPushButton)
    _bClearMeshTable        = qt_utils.RawWidget("EAclearMeshTable", QPushButton)
    _bPickFile              = qt_utils.RawWidget("EApickFile", QPushButton)
    _bMakeAtlas             = qt_utils.RawWidget("EAmakeAtlas", QPushButton)
    _tRowCount              = qt_utils.RawWidget("EArowCount", QLineEdit)
    _tColCount              = qt_utils.RawWidget("EAcolCount", QLineEdit)
    _tFileOutput            = qt_utils.RawWidget("EAfileOutput", QLineEdit)
    _tOutputWidth           = qt_utils.RawWidget("EAoutputWidth", QLineEdit)
    _tOutputHeight          = qt_utils.RawWidget("EAoutputHeight", QLineEdit)
    _lEasyAtlasImage        = qt_utils.RawWidget("EAeasyAtlasImage", QLabel)
    _aSavePreset            = qt_utils.RawWidget("EAsavePreset", QAction)
    _aLoadPreset            = qt_utils.RawWidget("EAloadPreset", QAction)
    _aPrefs                 = qt_utils.RawWidget("EApreferences", QAction)
    _aAddEAtoShelf          = qt_utils.RawWidget("EAaddEAtoShelf", QAction)
    _aAbout                 = qt_utils.RawWidget("EAAbout", QAction)
    _configFile             = "UVnTextureAtlasMaker.cfg"
    _uiFile                 = ("%s/ui/easy_atlas.ui" % os.path.dirname(__file__))
    _uiPrefsFile            = ("%s/ui/prefs.ui" % os.path.dirname(__file__))
    _easyAtlasImage         = ("%s/img/easy_atlas.png" % os.path.dirname(__file__))
    _easyAtlasIcon          = ("%s/img/easy_atlas_icon.png" % os.path.dirname(__file__))
    _colorList              = QColor.colorNames()
    _color                  = _colorList[random.randint(0, len(_colorList)-1)]

    def __init__(self):
        
        # Shuffle colors
        random.shuffle(self._colorList)
        
        self.windowUI = qt_utils.loadQtWindow(self._uiFile, self.windowName)  # @UndefinedVariable
        
        # create dock
        if (cmds.dockControl(self.dockName, exists=True)):  # @UndefinedVariable
            cmds.deleteUI(self.dockName)  # @UndefinedVariable
        cmds.dockControl(self.dockName, allowedArea=["right", "left"], area="right", content=self.windowName, visible=True)  # @UndefinedVariable

        #eventually remove
        self.AtlasInfo = Atlas()
        self.AtlasInfo.listOfAtlasMeshes = []

        #multiple atlas support, initialize allAtlases dict
        for s in self._atlasNames:
            self.allAtlases[s] = Atlas()
            self.allAtlases[s].listOfAtlasMeshes = []
        print "total atlas spots:", len(self.allAtlases)
        
        pixmap = QPixmap(self._easyAtlasImage);
        if pixmap:
            lEasyAtlasImage = qt_utils.getControl(self._lEasyAtlasImage)
            lEasyAtlasImage.setPixmap(pixmap);
            
        # Connect stuff
        bAddMesh = qt_utils.getControl(self._bAddMesh)
        bRemoveMesh = qt_utils.getControl(self._bRemoveMesh)
        bUpdateGrid = qt_utils.getControl(self._bResizeAtlasTable)
        bClear = qt_utils.getControl(self._bClearMeshTable)
        bPickFileOutput = qt_utils.getControl(self._bPickFile)
        bMakeAtlas = qt_utils.getControl(self._bMakeAtlas)
        aSavePreset = qt_utils.getControl(self._aSavePreset)
        aLoadPreset = qt_utils.getControl(self._aLoadPreset)
        aAbout = qt_utils.getControl(self._aAbout)
        aPrefs = qt_utils.getControl(self._aPrefs)
        aAddEAtoShelf = qt_utils.getControl(self._aAddEAtoShelf)
        tOutputFile = qt_utils.getControl(self._tFileOutput)
        toutputWidth = qt_utils.getControl(self._tOutputWidth)
        tOutputHeight = qt_utils.getControl(self._tOutputHeight)
        
        bAddMesh.clicked.connect(lambda: self.addMesh())
        bRemoveMesh.clicked.connect(lambda: self.removeMesh())
        bUpdateGrid.clicked.connect(lambda: self.resizeAtlasTable())
        bClear.clicked.connect(lambda: self.clearMeshes())
        bPickFileOutput.clicked.connect(lambda: self.pickOutputTexture())
        bMakeAtlas.clicked.connect(lambda: self.makeAtlas())
        aSavePreset.triggered.connect(lambda: self.savePreset())
        aLoadPreset.triggered.connect(lambda: self.loadPreset())
        aAbout.triggered.connect(lambda: self.about())
        aAddEAtoShelf.triggered.connect(lambda: self.addEAtoShelf())
        aPrefs.triggered.connect(lambda: self.preferences())
        tOutputFile.textChanged.connect(lambda: self.updateMeshList())
        toutputWidth.textChanged.connect(lambda: self.updateMeshList())
        tOutputHeight.textChanged.connect(lambda: self.updateMeshList())
        
        tableMeshes = qt_utils.getControl(self._meshTable)
        assert isinstance(tableMeshes, QTableWidget)
        tableMeshes.setContextMenuPolicy(Qt.CustomContextMenu)
        tableMeshes.customContextMenuRequested.connect(self.contextMenu_meshTable)
        tableMeshes.scrollToItem(tableMeshes.item(0,0))
        tableMeshes.itemChanged.connect(lambda: self.updateAtlasInfoFromMeshTableChange())

        # Attach context menu to atlas table
        table = qt_utils.getControl(self._atlasTable)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.contextMenu_atlasTable)
        
        # Show window and reset tables
        self.resizeAtlasTable()
        self.updateAtlasTable()
        
    def about(self):
        cmds.confirmDialog(t="About", message="Easy Atlas was made by Seigi Sato.\nMore info at www.seigisato.com.", button=["Ok"])  # @UndefinedVariable
        
    def addEAtoShelf(self):
        shelf = mel.eval("string $gShelfTopLevel; string $currentShelf = `tabLayout -q -st $gShelfTopLevel`;")  # @UndefinedVariable
        cmds.shelfButton(rpt=True, i1=self._easyAtlasIcon, ann="Easy Atlas", command="import easy_atlas\neasy_atlas.launch()", p=shelf)  # @UndefinedVariable
    
    def preferences(self):
        prefWindow = qt_utils.loadQtWindow(self._uiPrefsFile, self.prefWindowName)
        
        photoshopLineEdit = qt_utils.getControl(qt_utils.RawWidget("EAprefPhotoshopPath", QLineEdit))
        pickButton = qt_utils.getControl(qt_utils.RawWidget("EApickPhotoshopPath", QPushButton))
        saveButton = qt_utils.getControl(qt_utils.RawWidget("EAsavePref", QPushButton))
        cancelButton = qt_utils.getControl(qt_utils.RawWidget("EAcancelPref", QPushButton))
        
        cancelButton.clicked.connect(lambda: prefWindow.close())
        pickButton.clicked.connect(lambda: self.pickPhotoshopPath())
        saveButton.clicked.connect(lambda: self.savePreferences(prefWindow))
        
        photoshopPath = utils.INIHandler.load_info(self._configFile, "photoshop")
        photoshopLineEdit.setText(photoshopPath)
        
        prefWindow.show()
        
    def pickPhotoshopPath(self):
        
        photoshopLineEdit = qt_utils.getControl(qt_utils.RawWidget("EAprefPhotoshopPath", QLineEdit))
        folder = os.path.dirname(photoshopLineEdit.text())
        
        photoshopPath = cmds.fileDialog(m=0, dm='%s/*.exe' % folder)  # @UndefinedVariable
        if os.path.exists(photoshopPath):
            photoshopLineEdit.setText(photoshopPath)
    
    def savePreferences(self, window):
        
        photoshopLineEdit = qt_utils.getControl(qt_utils.RawWidget("EAprefPhotoshopPath", QLineEdit))
        utils.INIHandler.save_info(self._configFile, "photoshop", photoshopLineEdit.text())
        window.close()
     
    def updateAtlasInfoFromMeshTableChange(self):
        
        if self.suspendCellChangeSignal:
            return
        
        row = 0
        for k in self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes:
        # for k in self.AtlasInfo.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            tableMeshes = qt_utils.getControl(self._meshTable)
            k.meshName = tableMeshes.item(row, 1).text()
            k.texture = tableMeshes.item(row, 2).text()
            row += 1
        
        self.updateMeshList()
        
    def savePreset(self):
        self.allAtlases[self._atlasNames[0]].savePreset()
        # self.AtlasInfo.savePreset()
        
    def loadPreset(self):
        firstAtlas = self.allAtlases[self._atlasNames[0]]
        firstAtlas.loadPreset()
        # self.AtlasInfo.loadPreset()
        
        self.suspendUpdate = True
        qt_utils.getControl(self._tFileOutput).setText(firstAtlas.fileOutput)
        qt_utils.getControl(self._tOutputWidth).setText(str(firstAtlas.outputWidth))
        qt_utils.getControl(self._tOutputHeight).setText(str(firstAtlas.outputHeight))
        qt_utils.getControl(self._tRowCount).setText(str(firstAtlas.atlasSize[0]))
        qt_utils.getControl(self._tColCount).setText(str(firstAtlas.atlasSize[1]))
        self.suspendUpdate = False
        
        self.resizeAtlasTable(False)
        self.updateAtlasTable()
        
    def contextMenu_meshTable(self):
        menu = QMenu()
        menu.addAction('Assign Texture to Mesh', self.assignTextureToMesh)
        menu.exec_(QCursor.pos())
        menu.show()
        
    def contextMenu_atlasTable(self):
                
        menu = QMenu()
        if self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes:
        # if self.AtlasInfo.listOfAtlasMeshes:
        
            menu.addSeparator()
            for k in self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes:
            # for k in self.AtlasInfo.listOfAtlasMeshes:
                assert isinstance(k, AtlasMesh)
                if k.id == -1:
                    menu.addAction("Assign to %s" %k.meshName, lambda mesh=k: self.setAtlasIdToMesh(mesh))
            
        menu.addSeparator()
        menu.addAction("Add mesh from viewport selection", self.addMeshFromViewportSelection)
        menu.addAction('Unassign Mesh', self.celeteAtlasRegion)
            
        menu.exec_(QCursor.pos())
        menu.show()
        
    def setAtlasIdToMesh(self, mesh):
        
        table = qt_utils.getControl(self._atlasTable)
        
        # Make sure the new region doesn't overlap another region
        allTakenCoords = []
        for k in self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes:
        # for k in self.AtlasInfo.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            allTakenCoords.extend(k.coords)
        
        selectedCoords = []
        for k in table.selectedItems():
            selectedCoord = [k.row(), k.column()]
            selectedCoords.append(selectedCoord)
            if selectedCoord in allTakenCoords:
                cmds.confirmDialog(t="Warning", message="Cannot overlap Atlas region.", button=["ok"])  # @UndefinedVariable
                return
        
        # Find unique atlas id
        idList = []
        for k in self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes:
        # for k in self.AtlasInfo.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            idList.append(k.id)
            
        nextIdAtlas = -1
        index = 0
        while nextIdAtlas == -1:
            if not index in idList:
                nextIdAtlas = index
                break
            index += 1
        
        # Assign new region
        colorName = self.getNextColor()

        assert isinstance(mesh, AtlasMesh)
        mesh.color = colorName
        mesh.id = nextIdAtlas
        mesh.coords = selectedCoords
        self.updateAtlasTable()
        
    def assignTextureToMesh(self):
        
        dir = utils.INIHandler.load_info(self._configFile, "loadTextureDir")
        file = cmds.fileDialog(m=0, dm=dir+'/*.*')  # @UndefinedVariable
            
        if file:
            
            tableMeshes = qt_utils.getControl(self._meshTable)
            sel = tableMeshes.selectedItems()
            if sel:
                sel = sel[0]
                row = tableMeshes.row(sel)
                itemText = tableMeshes.item(row, 1).text()
                mesh = self.allAtlases[self._atlasNames[0]].getAtlasMeshByName(itemText)
                # mesh = self.AtlasInfo.getAtlasMeshByName(itemText)
                assert isinstance(mesh, AtlasMesh)
                mesh.texture = file
            self.updateMeshList()
            
            dir = os.path.dirname(file)
            utils.INIHandler.save_info(self._configFile, "loadTextureDir", dir)
    
    def resizeAtlasTable(self, resetItems=True):
        '''Rezises the table.
        
        Clear id, color and coords info from meshes.
        '''
        
        table = qt_utils.getControl(self._atlasTable)
        tRowcount = qt_utils.getControl(self._tRowCount)
        tColCount = qt_utils.getControl(self._tColCount)
        
        rowCount = int(tRowcount.text())
        colCount = int(tColCount.text())
        
        self.allAtlases[self._atlasNames[0]].atlasSize = [rowCount, colCount]
        # self.AtlasInfo.atlasSize = [rowCount, colCount]
        
        if resetItems:
            for k in self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes:
            # for k in self.AtlasInfo.listOfAtlasMeshes:
                assert isinstance(k, AtlasMesh)
                k.resetAtlasAssignment()
            
        table.setRowCount(rowCount)
        table.setColumnCount(colCount)
        
        tableSize = table.size()
            
        for k in range(rowCount):
            table.setRowHeight(k, (tableSize.height()*1.0)/rowCount)
            
        for k in range(colCount):
            table.setColumnWidth(k, (tableSize.width()*1.0)/colCount)
            
        self.updateAtlasTable()
        
    def resetAtlasTable(self):
        """
            Reset all the table colors to initial state.
        """
        
        table = qt_utils.getControl(self._atlasTable)
        
        for m in range(table.rowCount()):
            for n in range(table.columnCount()):
                table.setItem(m, n, QTableWidgetItem(""))
                brush = QBrush(QColor().fromRgb(128, 128, 128))
                table.item(m,n).setBackground(brush)
                
        table.scrollToItem(table.item(0, 0))
    
    def updateAtlasTable(self):
        """
            Assign colors and id to table item.
        """
        
        self.resetAtlasTable()
        table = qt_utils.getControl(self._atlasTable)
        for k in self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes:
        # for k in self.AtlasInfo.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            if k.id != -1:
                coordList = k.coords
                for m in coordList:
                    brush = QBrush(QColor(k.color))
                    brushFont = QBrush(QColor().black())
                    table.item(m[0], m[1]).setBackground(brush)
                    table.item(m[0], m[1]).setForeground(brushFont)
                    table.item(m[0], m[1]).setText(str(k.id))
                    table.item(m[0], m[1]).setTextAlignment(Qt.AlignCenter)
        
        table.scrollToItem(table.item(0, 0))
            
        self.updateMeshList()
    
    def getNextColor(self):
        
        index = self._colorList.index(self._color)
        index += 1
        if index > len(self._colorList)-1:
            index = 0
        self._color = self._colorList[index]
        
        return self._color
    
    def addMesh(self):
        
        meshes = cmds.ls(sl=True, l=True)  # @UndefinedVariable
        if not meshes:
            cmds.confirmDialog(t="Warning", message="At least one mesh must be selected for adding.", button=["ok"])  # @UndefinedVariable
            return
        
        for k in meshes:
            #to remove AtlasInfo later
            if not self.AtlasInfo.getAtlasMeshByName(k):
                texture = ""
                try:
                    rel = cmds.listRelatives(k)                                 # @UndefinedVariable
                    sg = cmds.listConnections(rel, type="shadingEngine")        # @UndefinedVariable
                    materials = cmds.listConnections(sg[0]+".surfaceShader")    # @UndefinedVariable
                    files = cmds.listConnections(materials[0], type="file")     # @UndefinedVariable
                    texture = cmds.getAttr(files[0]+".fileTextureName")         # @UndefinedVariable
                except:
                    pass
                #to remove AtlasInfo later
                item = AtlasMesh(k, texture)
                self.AtlasInfo.listOfAtlasMeshes.append(item)
            #end to remove
            self.buildAtlasDictionary(k) #will need to make sure meshes aren't added twice
        print self._atlasNames[0], " length: ", len(self.allAtlases[(self._atlasNames[0])].listOfAtlasMeshes)
        print self._atlasNames[1], " length: ", len(self.allAtlases[(self._atlasNames[1])].listOfAtlasMeshes)
        print self._atlasNames[2], " length: ", len(self.allAtlases[(self._atlasNames[2])].listOfAtlasMeshes)
        print self._atlasNames[3], " length: ", len(self.allAtlases[(self._atlasNames[3])].listOfAtlasMeshes)
        print self._atlasNames[4], " length: ", len(self.allAtlases[(self._atlasNames[4])].listOfAtlasMeshes)
        print self._atlasNames[5], " length: ", len(self.allAtlases[(self._atlasNames[5])].listOfAtlasMeshes)
        self.updateMeshList()
        
    def buildAtlasDictionary(self, mesh):
        #find connected texures
        rel = cmds.listRelatives(mesh)                                 
        sg = cmds.listConnections(rel, type="shadingEngine")        
        materials = cmds.listConnections(sg[0]+".surfaceShader")    
        print "Textures connected to", materials[0], ":"

        attrs = [
        (materials[0]+ ".color"), 
        (materials[0]+ ".ambientColor"), 
        (materials[0]+ ".incandescence"), 
        (materials[0]+ ".normalCamera"), 
        (materials[0]+ ".specularColor"), 
        (materials[0]+ ".reflectedColor")
        ]    

        #get file pathnames and put them in dictionary "atlasTextures"
        for attrInd, i in enumerate(attrs):
            print i
            # dictKey = ("tex_" + str(attrInd) + "_mesh_" + str(meshIndex))
            if attrInd == 3:            
                bumpNode = cmds.listConnections(i)            
                if bumpNode:
                    bumpTexture = cmds.listConnections(bumpNode, type="file")
                    if bumpTexture:
                        bumpFilePath = cmds.getAttr(bumpTexture[0] + ".fileTextureName")
                        dictVal = bumpFilePath
                        print bumpFilePath                    
                    else:
                        dictVal = ""
                        print "No bump file Node"
                else:
                    dictVal = ""
                    print "No bump connection"           
            else:
                connections = cmds.listConnections(i)
                if connections:
                    filePath = cmds.getAttr(connections[0] + ".fileTextureName")
                    dictVal = filePath
                    print filePath
                else:
                    dictVal = ""
                    print "no file connected"
            # atlasTextures[dictKey] = dictVal
            item = AtlasMesh(mesh, dictVal)
            self.allAtlases[(self._atlasNames[attrInd])].listOfAtlasMeshes.append(item) #can probably just access dictionary with attrInd?
            # print self._atlasNames[attrInd], "listOfAtlasMeshes length: ", len(self.allAtlases[(self._atlasNames[attrInd])].listOfAtlasMeshes)

    def addMeshFromViewportSelection(self):
        
        meshes = cmds.ls(sl=True, l=True)  # @UndefinedVariable
        if not meshes:
            cmds.confirmDialog(t="Warning", message="A mesh must be selected for adding.", button=["ok"])  # @UndefinedVariable
            return
        
        if len(meshes) > 1:
            cmds.confirmDialog(t="Warning", message="Please select only one mesh at a time.", button=["ok"])  # @UndefinedVariable
            return
        
        self.addMesh()
        self.setAtlasIdToMesh(self.allAtlases[self._atlasNames[0]].getAtlasMeshByName(meshes[0]))
        # self.setAtlasIdToMesh(self.AtlasInfo.getAtlasMeshByName(meshes[0]))
    
    def removeMesh(self):
        
        tableMeshes = qt_utils.getControl(self._meshTable)
        selectedItems = tableMeshes.selectedItems()
        
        if selectedItems:
            
            sel = selectedItems[0]
            row = tableMeshes.row(sel)
            itemText = tableMeshes.item(row, 1).text()
            
            mesh = self.allAtlases[self._atlasNames[0]].getAtlasMeshByName(itemText)
            # mesh = self.AtlasInfo.getAtlasMeshByName(itemText)
            self.allAtlases[self._atlasNames[0]].remove(mesh)
            # self.AtlasInfo.listOfAtlasMeshes.remove(mesh)
            #TODO sync across all atlases
                
            self.updateAtlasTable()
        
    def clearMeshes(self):
        self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes = [] #TODO sync across all atlases
        # self.AtlasInfo.listOfAtlasMeshes = []
        self.updateAtlasTable()
    
    def updateMeshList(self):
        
        if self.suspendUpdate:
            return
        
        # Must suspend Cell Change Signal
        self.suspendCellChangeSignal = True
        
        tableMeshes = qt_utils.getControl(self._meshTable)
        
        itemSelectedName = None
        if tableMeshes.selectedItems():
            itemSelectedName = tableMeshes.selectedItems()[1].text()
        
        tableMeshes.clear()
        firstAtlas = self.allAtlases[self._atlasNames[0]]
        # rowCount = len(firstAtlas.listofAtlasMeshes)
        rowCount = len(self.AtlasInfo.listOfAtlasMeshes) #.AtlasInfo isn't right, but the other line throws a "Atlas instance has no attribute 'listofAtlasMeshes;" error" but I'm going to leave it for now? 
        colCount = 3
        tableMeshes.setRowCount(rowCount)
        tableMeshes.setColumnCount(colCount)
        
        index = 0
        for k in self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes:
        # for k in self.AtlasInfo.listOfAtlasMeshes:
            
            assert isinstance(k, AtlasMesh)
            
            if k.id == -1:
                tableMeshes.setItem(index, 0, QTableWidgetItem(""))
            else:
                tableMeshes.setItem(index, 0, QTableWidgetItem(str(k.id)))
                
            tableMeshes.item(index, 0).setTextAlignment(Qt.AlignHCenter)
            tableMeshes.setItem(index, 1, QTableWidgetItem(k.meshName))
            tableMeshes.setItem(index, 2, QTableWidgetItem(k.texture))
            
            
            color = QColor().fromRgb(150, 150, 150)
            brush = QBrush(color)
            brushFont = QBrush(QColor("white"))
            if k.color:
                color = QColor(k.color)
                brush = QBrush(color)
                brushFont = QBrush(QColor().black())
                
            for i in range(3):
                tableMeshes.item(index, i).setBackground(brush)
                tableMeshes.item(index, i).setForeground(brushFont)
            
            if itemSelectedName == k:
                tableMeshes.setCurrentCell(index, 0)
            
            index += 1
        
        #tableMeshes.horizontalHeader().setStretchLastSection(True)
        tableMeshes.setHorizontalHeaderLabels(["Atlas", "Mesh", "Texture"])
        tableMeshes.horizontalHeaderItem(0).setTextAlignment(Qt.AlignHCenter)
        tableMeshes.horizontalHeaderItem(1).setTextAlignment(Qt.AlignLeft)
        tableMeshes.horizontalHeaderItem(2).setTextAlignment(Qt.AlignLeft)
        tableMeshes.setColumnWidth(0, 40)
        tableMeshes.setColumnWidth(1, 150)
        tableMeshes.resizeColumnToContents(2)

        self.allAtlases[self._atlasNames[0]].fileOutput = qt_utils.getControl(self._tFileOutput).text()
        # self.AtlasInfo.fileOutput = qt_utils.getControl(self._tFileOutput).text()
        self.allAtlases[self._atlasNames[0]].outputWidth = qt_utils.getControl(self._tOutputWidth).text()
        # self.AtlasInfo.outputWidth = qt_utils.getControl(self._tOutputWidth).text()
        self.allAtlases[self._atlasNames[0]].outputHeight = qt_utils.getControl(self._tOutputHeight).text()
        # self.AtlasInfo.outputHeight = qt_utils.getControl(self._tOutputHeight).text()
        
        tRowcount = qt_utils.getControl(self._tRowCount)
        tColCount = qt_utils.getControl(self._tColCount)
        
        rowCount = int(tRowcount.text())
        colCount = int(tColCount.text())
        
        self.allAtlases[self._atlasNames[0]].atlasSize = [rowCount, colCount]
        # self.AtlasInfo.atlasSize = [rowCount, colCount]
        
        # Must revert Cell Change Signal to false
        self.suspendCellChangeSignal = False
            
        #=======================================================================
        # with open(self._jsonFile, 'wb') as fp:
        #     json.dump(__REPLACE_JSON__, fp)
        #=======================================================================
    
    def celeteAtlasRegion(self):
        
        table = qt_utils.getControl(self._atlasTable)
        
        for k in table.selectedItems():
            coord = [k.row(), k.column()]
            mesh = self.allAtlases[self._atlasNames[0]].getAtlasMeshByCoord(coord)
            # mesh = self.AtlasInfo.getAtlasMeshByCoord(coord)
            if mesh:
                mesh.resetAtlasAssignment()
        
        self.updateAtlasTable()
    
    def pickOutputTexture(self):
        
        outputFilename = qt_utils.getControl(self._tFileOutput)
        dir = ""
        
        if outputFilename.text() != "":
            dir = os.path.dirname(outputFilename.text())
            
        if not os.path.exists(dir):
            dir = utils.INIHandler.load_info(self._configFile, "loadTextureDir")
        
        file = cmds.fileDialog(m=1, dm=dir+'/*.*')  # @UndefinedVariable
        
        if file:
            
            outputFilename.setText(file)
            
            dir = os.path.dirname(file)
            utils.INIHandler.save_info(self._configFile, "loadTextureDir", dir)
    
    def getCoordRangeNormalized(self, coordList, totalSize):
        
        
        totalSizeX = totalSize[1]
        totalSizeY = totalSize[0]
        
        xList = []
        yList = []
        for k in coordList:
            xList.append(k[1])
            yList.append(k[0])
            
        posX = min(xList)
        maxPosX = max(xList)
        sizeX = maxPosX+1-posX
        
        posY = min(yList)
        maxPosY = max(yList)
        sizeY = maxPosY+1-posY
        
        posXNormalized = float(posX) / totalSizeX
        posYNormalized = float(posY) / totalSizeY
        sizeXNormalized = float(sizeX) / totalSizeX
        sizeYNormalized = float(sizeY) / totalSizeY
        
        return posXNormalized, posYNormalized, sizeXNormalized, sizeYNormalized
    
    def makeAtlas(self):
        
        # Work around for the editing text PySide issue on the mesh table
        t = qt_utils.getControl(self._meshTable)
        t.focusNextChild()
        t.focusPreviousChild()
        self.updateAtlasInfoFromMeshTableChange()
        
        # Make sure Photoshop path is set up
        photoshopPath = utils.INIHandler.load_info(self._configFile, "photoshop")
        if not photoshopPath:
            setUpPS = cmds.confirmDialog(t="Warning", message="Photoshop path missing. Do you want to pick a Photoshop path now?", button=["Yes", "No"], defaultButton='Yes', cancelButton='No', dismissString='No')  # @UndefinedVariable
            
            if setUpPS == "No":
                return
            
            else:
                photoshopPath = cmds.fileDialog(m=0, dm='c:/*.exe')  # @UndefinedVariable
                if os.path.exists(photoshopPath):
                    utils.INIHandler.save_info(self._configFile, "photoshop", photoshopPath)
                else:
                    return
        
        # Now the script
        txtFinalFilename = qt_utils.getControl(self._tFileOutput).text().lower() #need to differentiate final file name
        atlasItems = self.gatherAtlasData("colorAtlas", txtFinalFilename, photoshopPath)
        splitFileName = txtFinalFilename.split('.')
        fileExtension = splitFileName.pop()
        fileNameWithNoExtension = ".".join(splitFileName)
        #loop through the other atlases but don't care about atlasItems
        for index, atlasName in enumerate(self._atlasNames):
            # print atlasName, "to gatherAtlasData"
            if (index > 0): 
                self.gatherAtlasData(atlasName, (fileNameWithNoExtension+"_"+atlasName+"."+fileExtension), photoshopPath)
        
        uv_atlas.createAtlas(atlasItems)
        
        meshes = [x.mesh for x in atlasItems]
        cmds.select(meshes)  # @UndefinedVariable
        
        shader=cmds.shadingNode("lambert",asShader=True)  # @UndefinedVariable
        file_node=cmds.shadingNode("file",asTexture=True)  # @UndefinedVariable
        shading_group= cmds.sets(renderable=True,noSurfaceShader=True,empty=True)  # @UndefinedVariable
        cmds.connectAttr('%s.outColor' %shader ,'%s.surfaceShader' %shading_group)  # @UndefinedVariable
        cmds.connectAttr('%s.outColor' %file_node, '%s.color' %shader)  # @UndefinedVariable
        cmds.setAttr(file_node+'.fileTextureName', txtFinalFilename, type='string')  # @UndefinedVariable
        cmds.sets(meshes, edit=True, forceElement=shading_group)  # @UndefinedVariable
        
        cmds.select(meshes) # @UndefinedVariable
    
    def gatherAtlasData(self, atlasName, txtFinalFilename, photoshopPath):
        print atlasName, "gatherAtlasData started, filename", txtFinalFilename
        atlasItems = []
        outputSizeX = int(qt_utils.getControl(self._tOutputWidth).text())
        outputSizeY = int(qt_utils.getControl(self._tOutputHeight).text())
        
        # Check that output file extension is valid
        if not os.path.splitext(txtFinalFilename)[1] in [".jpg", ".png", ".tga", ".psd"]:
            cmds.confirmDialog(t="Warning", message="Output file type not supported by Easy Atlas.\n Supported types are jpg, png, tga and psd.", button=["ok"])  # @UndefinedVariable
            return
        
        hasTextures = self.allAtlases[atlasName].hasTextures()
        if not hasTextures:
            print atlasName, "doesn't have any textures to make an atlas, skipping."
            return
        # atleast one of the meshes has a texture on the channel, set the default image
        # hold on this for now, there are uv implications if a texture is missing... self.allAtlases[atlasName].setDefaultTextures(self._easyAtlasIcon)

        for index, mesh in enumerate(self.allAtlases[self._atlasNames[0]].listOfAtlasMeshes): 
        # for mesh in self.allAtlases[atlasName].listOfAtlasMeshes:
            
            assert isinstance(mesh, AtlasMesh)
            print "mesh.id", mesh.id
            if mesh.id != -1:
                # texture = mesh.texture
                atlasNameMesh = self.allAtlases[atlasName].listOfAtlasMeshes[index]
                texture = atlasNameMesh.texture
                rawCoords = mesh.coords
                posX, posY, sizeX, sizeY = self.getCoordRangeNormalized(rawCoords, self.allAtlases[self._atlasNames[0]].atlasSize)
                # posX, posY, sizeX, sizeY = self.getCoordRangeNormalized(rawCoords, self.AtlasInfo.atlasSize)
                aItem = AtlasItem(mesh.meshName, texture, posX, posY, sizeX, sizeY)
                atlasItems.append(aItem)
                
                if not os.path.exists(mesh.texture):
                    cmds.confirmDialog(t="Warning", message="Input texture doesn't exist: \n%s." % mesh.texture, button=["ok"])  # @UndefinedVariable
                    return
                
                # Make sure the mesh has a valid maya name (names that use non-standard characters break maya)
                try:
                    cmds.ls(mesh.meshName)  # @UndefinedVariable
                except:
                    cmds.confirmDialog(t="Warning", message="Invalid mesh name: \n%s." % (mesh.meshName), button=["ok"])  # @UndefinedVariable
                    return
                
                if not cmds.ls(mesh.meshName):  # @UndefinedVariable
                    cmds.confirmDialog(t="Warning", message="Mesh doesn't exist: \n%s." % mesh.meshName, button=["ok"])  # @UndefinedVariable
                    return
        
        if not atlasItems:
            cmds.confirmDialog(t="Warning", message="No item has been assigned to the Atlas: " + atlasName, button=["ok"])  # @UndefinedVariable
            return
            
        texture_atlas.createAtlas(atlasItems, txtFinalFilename, int(outputSizeX), int(outputSizeY), photoshopPath)
        return atlasItems

def launch():
    '''Method for launching the Easy Atlas interface.'''
    
    EA = EasyAtlas()
        
# Quick launch script if debug mode is on
if bool(mel.eval('getenv "EASY_DEBUG_MODE"')):  # @UndefinedVariable
    launch()