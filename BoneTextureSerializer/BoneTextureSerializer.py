import os
import re
import qt
import slicer
from slicer.ScriptedLoadableModule import *
import csv

class case(object):
    def __init__(self, ID):
        self.caseID = ID
        self.scanFilePath = None
        self.segmentationFilePath = None
        self.outputFilePath = None
        self.GLCMFeatures = None
        self.GLRLMFeatures = None

################################################################################
######################  Bone Texture Serializer ################################
################################################################################


class BoneTextureSerializer(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Bone Texture Serializer"
        self.parent.categories = ["Quantification"]
        self.parent.dependencies = []
        self.parent.contributors = ["Jean-Baptiste VIMORT (Kitware Inc.)"]
        self.parent.helpText = """
        This module to serialyse the BoneTexture's algorythms on several cases contained in the same folder.
        The input data should be named in the folowing way: Scan"ID".nrrd (for the input scan) and Segm"ID".nrrd
        (for the segmentation if it exist)
        """
        self.parent.acknowledgementText = """
        This work was supported by the National Institute of Health (NIH) National Institute for
        Dental and Craniofacial Research (NIDCR) R01EB021391 (Textural Biomarkers of Arthritis for
        the Subchondral Bone in the Temporomandibular Joint)
        """

################################################################################
##########################  Bone Texture Widget ################################
################################################################################


class BoneTextureSerializerWidget(ScriptedLoadableModuleWidget):

    # ************************************************************************ #
    # -------------------------- Initialisation ------------------------------ #
    # ************************************************************************ #

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        print("-----  Bone Texture Serializer widget setup -----")
        self.moduleName = 'BoneTextureSerializer'
        scriptedModulesPath = eval('slicer.modules.%s.path' % self.moduleName.lower())
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)

        # - Initialisation of Bone Texture Serializer and its logic - #

        self.logic = BoneTextureSerializerLogic(self)
        self.caseDict = dict()
        self.GLCMFeaturesValueDict = {}
        self.GLCMFeaturesValueDict["insideMask"] = 1
        self.GLCMFeaturesValueDict["binNumber"] = 10
        self.GLCMFeaturesValueDict["pixelIntensityMin"] = 0
        self.GLCMFeaturesValueDict["pixelIntensityMax"] = 4000
        self.GLCMFeaturesValueDict["neighborhoodRadius"] = 6
        self.GLRLMFeaturesValueDict = {}
        self.GLRLMFeaturesValueDict["insideMask"] = 1
        self.GLRLMFeaturesValueDict["binNumber"] = 10
        self.GLRLMFeaturesValueDict["pixelIntensityMin"] = 0
        self.GLRLMFeaturesValueDict["pixelIntensityMax"] = 4000
        self.GLRLMFeaturesValueDict["neighborhoodRadius"] = 4
        self.GLRLMFeaturesValueDict["distanceMin"] = 0.00
        self.GLRLMFeaturesValueDict["distanceMax"] = 1.00

        # -------------------------------------------------------------------- #
        # ----------------- Definition of the UI interface ------------------- #
        # -------------------------------------------------------------------- #

        # -------------------- Loading of the .ui file ----------------------- #

        loader = qt.QUiLoader()
        path = os.path.join(scriptedModulesPath, 'Resources', 'UI', '%s.ui' % self.moduleName)
        qfile = qt.QFile(path)
        qfile.open(qt.QFile.ReadOnly)
        widget = loader.load(qfile, self.parent)
        self.layout = self.parent.layout()
        self.widget = widget
        self.layout.addWidget(widget)

        # ---------------- Input Data Collapsible Button --------------------- #

        self.inputDataCollapsibleButton = self.logic.get("InputDataCollapsibleButton")
        self.singleCaseGroupBox = self.logic.get("SingleCaseGroupBox")
        self.inputFolderDirectoryButton = self.logic.get("InputFolderDirectoryButton")

        # ---------------- Computation Collapsible Button -------------------- #

        self.computationCollapsibleButton = self.logic.get("ComputationCollapsibleButton")
        self.featureChoiceCollapsibleGroupBox = self.logic.get("FeatureChoiceCollapsibleGroupBox")
        self.gLCMFeaturesCheckBox = self.logic.get("GLCMFeaturesCheckBox")
        self.gLRLMFeaturesCheckBox = self.logic.get("GLRLMFeaturesCheckBox")
        self.computeFeaturesPushButton = self.logic.get("ComputeFeaturesPushButton")
        self.computeColormapsPushButton = self.logic.get("ComputeColormapsPushButton")
        self.GLCMparametersCollapsibleGroupBox = self.logic.get("GLCMParametersCollapsibleGroupBox")
        self.GLCMinsideMaskValueSpinBox = self.logic.get("GLCMInsideMaskValueSpinBox")
        self.GLCMnumberOfBinsSpinBox = self.logic.get("GLCMNumberOfBinsSpinBox")
        self.GLCMminVoxelIntensitySpinBox = self.logic.get("GLCMMinVoxelIntensitySpinBox")
        self.GLCMmaxVoxelIntensitySpinBox = self.logic.get("GLCMMaxVoxelIntensitySpinBox")
        self.GLCMneighborhoodRadiusSpinBox = self.logic.get("GLCMNeighborhoodRadiusSpinBox")
        self.GLRLMparametersCollapsibleGroupBox = self.logic.get("GLRLMParametersCollapsibleGroupBox")
        self.GLRLMinsideMaskValueSpinBox = self.logic.get("GLRLMInsideMaskValueSpinBox")
        self.GLRLMnumberOfBinsSpinBox = self.logic.get("GLRLMNumberOfBinsSpinBox")
        self.GLRLMminVoxelIntensitySpinBox = self.logic.get("GLRLMMinVoxelIntensitySpinBox")
        self.GLRLMmaxVoxelIntensitySpinBox = self.logic.get("GLRLMMaxVoxelIntensitySpinBox")
        self.GLRLMminDistanceSpinBox = self.logic.get("GLRLMMinDistanceSpinBox")
        self.GLRLMmaxDistanceSpinBox = self.logic.get("GLRLMMaxDistanceSpinBox")
        self.GLRLMneighborhoodRadiusSpinBox = self.logic.get("GLRLMNeighborhoodRadiusSpinBox")

        # ---------------- Exportation Collapsible Button -------------------- #

        self.exportationCollapsibleButton = self.logic.get("ExportationCollapsibleButton")
        self.outputFolderDirectoryButton = self.logic.get("OutputFolderDirectoryButton")
        self.separateFeaturesCheckBox = self.logic.get("separateFeaturesCheckBox")


        # -------------------------------------------------------------------- #
        # ---------------------------- Connections --------------------------- #
        # -------------------------------------------------------------------- #

        # ---------------- Input Data Collapsible Button --------------------- #

        self.inputFolderDirectoryButton.connect('directoryChanged(const QString &)', self.onDirectoryChanged)
        self.GLCMinsideMaskValueSpinBox.connect('valueChanged(int)',lambda: self.onGLCMFeaturesValueDictModified("insideMask", self.GLCMinsideMaskValueSpinBox.value))
        self.GLCMnumberOfBinsSpinBox.connect('valueChanged(int)', lambda: self.onGLCMFeaturesValueDictModified("binNumber", self.GLCMnumberOfBinsSpinBox.value))
        self.GLCMminVoxelIntensitySpinBox.connect('valueChanged(int)', lambda: self.onGLCMFeaturesValueDictModified("pixelIntensityMin", self.GLCMminVoxelIntensitySpinBox.value))
        self.GLCMmaxVoxelIntensitySpinBox.connect('valueChanged(int)', lambda: self.onGLCMFeaturesValueDictModified("pixelIntensityMax", self.GLCMmaxVoxelIntensitySpinBox.value))
        self.GLCMneighborhoodRadiusSpinBox.connect('valueChanged(int)', lambda: self.onGLCMFeaturesValueDictModified("neighborhoodRadius", self.GLCMneighborhoodRadiusSpinBox.value))
        self.GLRLMinsideMaskValueSpinBox.connect('valueChanged(int)', lambda: self.onGLRLMFeaturesValueDictModified("insideMask", self.GLRLMinsideMaskValueSpinBox.value))
        self.GLRLMnumberOfBinsSpinBox.connect('valueChanged(int)', lambda: self.onGLRLMFeaturesValueDicttModified("binNumber", self.GLRLMnumberOfBinsSpinBox.value))
        self.GLRLMminVoxelIntensitySpinBox.connect('valueChanged(int)', lambda: self.onGLRLMFeaturesValueDictModified("pixelIntensityMin", self.GLRLMminVoxelIntensitySpinBox.value))
        self.GLRLMmaxVoxelIntensitySpinBox.connect('valueChanged(int)', lambda: self.onGLRLMFeaturesValueDictModified("pixelIntensityMax", self.GLRLMmaxVoxelIntensitySpinBox.value))
        self.GLRLMminDistanceSpinBox.connect('valueChanged(double)', lambda: self.onGLRLMFeaturesValueDictModified("distanceMin", self.GLRLMminDistanceSpinBox.value))
        self.GLRLMmaxDistanceSpinBox.connect('valueChanged(double)', lambda: self.onGLRLMFeaturesValueDictModified("distanceMax", self.GLRLMmaxDistanceSpinBox.value))
        self.GLRLMneighborhoodRadiusSpinBox.connect('valueChanged(int)', lambda: self.onGLRLMFeaturesValueDictModified("neighborhoodRadius", self.GLRLMneighborhoodRadiusSpinBox.value))

        # ---------------- Computation Collapsible Button -------------------- #

        self.computeFeaturesPushButton.connect('clicked()', self.onComputeFeatures)
        self.computeColormapsPushButton.connect('clicked()', self.onComputeColormaps)

        # ---------------- Exportation Collapsible Button -------------------- #

        # -------------------------------------------------------------------- #
        # -------------------------- Initialisation -------------------------- #
        # -------------------------------------------------------------------- #

        # ******************************************************************** #
        # ----------------------- Algorithm ---------------------------------- #
        # ******************************************************************** #

        # ---------------- Input Data Collapsible Button --------------------- #

    def onGLCMFeaturesValueDictModified(self, key, value):
        self.GLCMFeaturesValueDict[key] = value

    def onGLRLMFeaturesValueDictModified(self, key, value):
        self.GLRLMFeaturesValueDict[key] = value

    def onDirectoryChanged(self):
        self.logic.updateCaseDictionary(self.caseDict,
                                        self.inputFolderDirectoryButton.directory)

        # ---------------- Computation Collapsible Button -------------------- #

    def onComputeFeatures(self):
        self.logic.computeFeatures(self.caseDict,
                                   self.gLCMFeaturesCheckBox.isChecked(),
                                   self.gLRLMFeaturesCheckBox.isChecked(),
                                   self.GLCMFeaturesValueDict,
                                   self.GLRLMFeaturesValueDict,
                                   self.outputFolderDirectoryButton.directory.encode('utf-8'))

    def onComputeColormaps(self):
        self.logic.computeColormaps(self.caseDict,
                                    self.gLCMFeaturesCheckBox.isChecked(),
                                    self.gLRLMFeaturesCheckBox.isChecked(),
                                    self.GLCMFeaturesValueDict,
                                    self.GLRLMFeaturesValueDict,
                                    self.outputFolderDirectoryButton.directory.encode('utf-8'),
                                    self.separateFeaturesCheckBox.isChecked())

        # ---------------- Exportation Collapsible Button -------------------- #

    def cleanup(self):
        pass


################################################################################
#####################  Bone Texture Serializer Logic ###########################
################################################################################


class BoneTextureSerializerLogic(ScriptedLoadableModuleLogic):

    # ************************************************************************ #
    # ----------------------- Initialisation --------------------------------- #
    # ************************************************************************ #

    def __init__(self, interface):
        print("----- Bone Texture Serializer logic init -----")
        self.interface = interface
        self.CFeatures = ["energy", "entropy",
                          "correlation", "inverseDifferenceMoment",
                          "inertia", "clusterShade",
                          "clusterProminence", "haralickCorrelation"]
        self.RLFeatures = ["shortRunEmphasis", "longRunEmphasis",
                           "greyLevelNonuniformity", "runLengthNonuniformity",
                           "lowGreyLevelRunEmphasis" , "highGreyLevelRunEmphasis" ,
                           "shortRunLowGreyLevelEmphasis", "shortRunHighGreyLevelEmphasis",
                           "longRunLowGreyLevelEmphasis", "longRunHighGreyLevelEmphasis"]

    # ************************************************************************ #
    # ------------------------ Algorithm ------------------------------------- #
    # ************************************************************************ #

    # ----------- Useful functions to access the .ui file elements ----------- #

    def get(self, objectName):
        return self.findWidget(self.interface.widget, objectName)

    def findWidget(self, widget, objectName):
        if widget.objectName == objectName:
            return widget
        else:
            for w in widget.children():
                resulting_widget = self.findWidget(w, objectName)
                if resulting_widget:
                    return resulting_widget
            return None

    # ------- Test to ensure that the input data exist and are conform ------- #

    def inputDataVerification(self, inputScan, inputSegmentation):
        if not(inputScan):
            slicer.util.warningDisplay("Please specify an input scan")
            return False
        if inputScan and inputSegmentation:
            if inputScan.GetImageData().GetDimensions() != inputSegmentation.GetImageData().GetDimensions():
                slicer.util.warningDisplay("The input san and the input segmentation must be the same size")
                return False
            if (inputScan.GetSpacing() != inputSegmentation.GetSpacing()) or \
                    (inputScan.GetOrigin() != inputSegmentation.GetOrigin()):
                slicer.util.warningDisplay("The input san and the input segmentation must overlap: same origin, spacing and orientation")
                return False
        return True

    # ---------------- Fill the case dictionary ------------------------------- #

    def updateCaseDictionary(self,
                             caseDict,
                             inputDirectory):
        caseDict.clear()
        for fileName in os.listdir(inputDirectory):
            if fileName.endswith(".nrrd"):
                print(fileName)
                if fileName.startswith("SegmC"):
                    caseID = re.search("SegmC(.+?).nrrd", fileName).group(1)
                    if caseID in caseDict:
                        caseDict[caseID].segmentationFilePath = os.path.join(inputDirectory , fileName)
                    else:
                        temp = case(caseID)
                        temp.segmentationFilePath = os.path.join(inputDirectory , fileName)
                        caseDict[caseID] = temp
                elif fileName.startswith("Scan"):
                    caseID = re.search("Scan(.+?).nrrd", fileName).group(1)
                    if caseID in caseDict:
                        caseDict[caseID].scanFilePath = os.path.join(inputDirectory , fileName)
                    else:
                        temp = case(caseID)
                        temp.scanFilePath = os.path.join(inputDirectory , fileName )
                        caseDict[caseID] = temp

    # ---------------- Computation of the wanted features---------------------- #

    def computeFeatures(self,
                        caseDict,
                        computeGLCMFeatures,
                        computeGLRLMFeatures,
                        GLCMFeaturesValueDict,
                        GLRLMFeaturesValueDict,
                        outputDirectory):

        if not (computeGLCMFeatures or computeGLRLMFeatures):
            slicer.util.warningDisplay("Please select at least one type of features to compute")
            return

        properties = {}

        file = open( os.path.join(outputDirectory , "TexturalFeatureTable.csv"), 'w+')
        print(file)
        cw = csv.writer(file, delimiter=',')
        for case in caseDict.values():
            properties['labelmap'] = False
            inputScan = slicer.util.loadNodeFromFile(case.scanFilePath, 'VolumeFile', properties, returnNode=True)
            inputScan = inputScan[1]
            properties['labelmap'] = True
            inputSegmentation = slicer.util.loadNodeFromFile(case.segmentationFilePath, 'VolumeFile', properties, returnNode=True)
            inputSegmentation = inputSegmentation[1]
            if not (self.inputDataVerification(inputScan, inputSegmentation)):
                return

            if computeGLCMFeatures:
                case.GLCMFeatures = self.computeSingleFeatureSet(inputScan,
                                                             inputSegmentation,
                                                             slicer.modules.computeglcmfeatures,
                                                             GLCMFeaturesValueDict)

            if computeGLRLMFeatures:
                case.GLRLMFeatures = self.computeSingleFeatureSet(inputScan,
                                                             inputSegmentation,
                                                             slicer.modules.computeglrlmfeatures,
                                                             GLRLMFeaturesValueDict)
            slicer.mrmlScene.RemoveNode(inputScan)
            slicer.mrmlScene.RemoveNode(inputSegmentation)
            toWrite = [case.caseID]
            if (case.GLCMFeatures):
                toWrite += case.GLCMFeatures
            if (case.GLRLMFeatures):
                toWrite += case.GLRLMFeatures
            cw.writerow(toWrite)
        file.close()

    def computeSingleFeatureSet(self,
                               inputScan,
                               inputSegmentation,
                               CLIname,
                               valueDict):
        parameters = dict(valueDict)
        parameters["inputVolume"] = inputScan
        parameters["inputMask"] = inputSegmentation
        CLI = slicer.cli.run(CLIname,
                             None,
                             parameters,
                             wait_for_completion=True)
        return list(map(float, CLI.GetParameterDefault(2, 0).split(",")))

    # --------------- Computation of the wanted colormaps --------------------- #

    def computeColormaps(self,
                         caseDict,
                         computeGLCMFeatures,
                         computeGLRLMFeatures,
                         GLCMFeaturesValueDict,
                         GLRLMFeaturesValueDict,
                         outputDirectory,
                         saparateFeatureMaps):

        if not (computeGLCMFeatures or computeGLRLMFeatures):
            slicer.util.warningDisplay("Please select at least one type of features to compute")
            return

        properties = {}
        for case in caseDict.values():
            inputScan = slicer.util.loadNodeFromFile(case.scanFilePath, 'VolumeFile', properties, returnNode=True)
            inputScan = inputScan[1]
            properties['labelmap'] = True
            inputSegmentation = slicer.util.loadNodeFromFile(case.segmentationFilePath, 'VolumeFile', properties, returnNode=True)
            inputSegmentation = inputSegmentation[1]

            if not (self.inputDataVerification(inputScan, inputSegmentation)):
                return

            print(case.caseID)
            if computeGLCMFeatures:
                volumeNode = self.computeSingleColormap(inputScan,
                                                        inputSegmentation,
                                                        slicer.modules.computeglcmfeaturemaps,
                                                        GLCMFeaturesValueDict,
                                                        "GLCM_ColorMaps")
                if saparateFeatureMaps:
                    param = dict()
                    param["inputVolume"] = volumeNode
                    param["outputFileBaseName"] = os.path.join(outputDirectory , case.caseID  + "_GLCMFeatureMap")
                    slicer.cli.run(slicer.modules.separatevectorimage,
                                   None,
                                   param,
                                   wait_for_completion=True)
                else:
                    slicer.util.saveNode(volumeNode, os.path.join(outputDirectory , case.caseID + "_GLCMFeatureMap.nhdr"))
                slicer.mrmlScene.RemoveNode(volumeNode)

            if computeGLRLMFeatures:
                volumeNode = self.computeSingleColormap(inputScan,
                                                        inputSegmentation,
                                                        slicer.modules.computeglrlmfeaturemaps,
                                                        GLRLMFeaturesValueDict,
                                                        "GLRLM_ColorMaps")
                if saparateFeatureMaps:
                    param = dict()
                    param["inputVolume"] = volumeNode
                    param["outputFileBaseName"] = os.path.join(outputDirectory , case.caseID  + "_GLRLMFeatureMap")
                    slicer.cli.run(slicer.modules.separatevectorimage,
                                   None,
                                   param,
                                   wait_for_completion=True)
                else:
                    slicer.util.saveNode(volumeNode, os.path.join(outputDirectory , case.caseID + "_GLRLMFeatureMap.nhdr"))
                slicer.mrmlScene.RemoveNode(volumeNode)

            slicer.mrmlScene.RemoveNode(inputScan)
            slicer.mrmlScene.RemoveNode(inputSegmentation)

        self.renameSeparatedFeatures(outputDirectory)

    def computeSingleColormap(self,
                              inputScan,
                              inputSegmentation,
                              CLIname,
                              valueDict,
                              outputName):
        parameters = dict(valueDict)
        parameters["inputVolume"] = inputScan
        parameters["inputMask"] = inputSegmentation
        volumeNode = slicer.vtkMRMLDiffusionWeightedVolumeNode()
        slicer.mrmlScene.AddNode(volumeNode)
        displayNode = slicer.vtkMRMLDiffusionWeightedVolumeDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        colorNode = slicer.util.getNode('Rainbow')
        displayNode.SetAndObserveColorNodeID(colorNode.GetID())
        volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
        volumeNode.SetName(outputName)
        parameters["outputVolume"] = volumeNode
        slicer.cli.run(CLIname,
                       None,
                       parameters,
                       wait_for_completion=True)

        return volumeNode

    def renameSeparatedFeatures(self, outputDirectory):
        for fileName in os.listdir(outputDirectory):
            for i in range(8):
                if fileName.endswith("GLCMFeatureMap_" + str(i) + ".nrrd"):
                    os.rename(os.path.join(outputDirectory, fileName),
                              os.path.join(outputDirectory, fileName.replace(str(i), self.CFeatures[i])))
            for i in range(10):
                if fileName.endswith("GLRLMFeatureMap_" + str(i) + ".nrrd"):
                    os.rename(os.path.join(outputDirectory, fileName),
                              os.path.join(outputDirectory, fileName.replace(str(i), self.RLFeatures[i])))

################################################################################
####################  Bone Texture Serializer Test #############################
################################################################################


class BoneTextureSerializerTest(ScriptedLoadableModuleTest):
    # ************************************************************************ #
    # -------------------------- Initialisation ------------------------------ #
    # ************************************************************************ #

    def setUp(self):
        print("----- Bone Texture test setup -----")
        # reset the state - clear scene
        self.delayDisplay("Clear the scene")
        slicer.mrmlScene.Clear(0)

        # ******************************************************************** #
        # -------------------- Testing of Bone Texture ----------------------- #
        # ******************************************************************** #

    def runTest(self):
        self.setUp()
        self.test_BoneTexture1()

    def test_BoneTexture1(self):
        self.delayDisplay("Starting the test")
