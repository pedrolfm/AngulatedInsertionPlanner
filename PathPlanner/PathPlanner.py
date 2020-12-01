import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
#
# PathPlanner
#

class PathPlanner(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PathPlanner" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# PathPlannerWidget
#

class PathPlannerWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the prostate image to select the target." )
    parametersFormLayout.addRow("Prostate Volume: ", self.inputSelector)

    #
    # segmented volume selector
    #
    self.anatomySelector = slicer.qMRMLNodeComboBox()
    self.anatomySelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.anatomySelector.selectNodeUponCreation = True
    self.anatomySelector.addEnabled = False
    self.anatomySelector.removeEnabled = False
    self.anatomySelector.noneEnabled = False
    self.anatomySelector.showHidden = False
    self.anatomySelector.showChildNodeTypes = False
    self.anatomySelector.setMRMLScene( slicer.mrmlScene )
    self.anatomySelector.setToolTip( "Pick the anatomy segmentation." )
    parametersFormLayout.addRow("Anatomy segmentation: ", self.anatomySelector)

    #
    # target selector
    #
    self.targetSelector = slicer.qMRMLNodeComboBox()
    self.targetSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    self.targetSelector.selectNodeUponCreation = True
    self.targetSelector.addEnabled = False
    self.targetSelector.removeEnabled = False
    self.targetSelector.noneEnabled = False
    self.targetSelector.showHidden = False
    self.targetSelector.showChildNodeTypes = False
    self.targetSelector.setMRMLScene( slicer.mrmlScene )
    self.targetSelector.setToolTip( "Pick the target list." )
    parametersFormLayout.addRow("Target: ", self.targetSelector)

    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

    #
    # Target Button
    #
    self.selectTarget = qt.QPushButton("Select Target")
    self.selectTarget.toolTip = "Select Target"
    self.selectTarget.enabled = True
    parametersFormLayout.addRow(self.selectTarget)


    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton,self.selectTarget)

    #
    # Angulation Area
    #
    angulationCollapsibleButton = ctk.ctkCollapsibleButton()
    angulationCollapsibleButton.text = "Smart Template angles"
    self.layout.addWidget(angulationCollapsibleButton)

    angulationFormLayout = qt.QFormLayout(angulationCollapsibleButton)

    self.angleXWidget = ctk.ctkSliderWidget()
    self.angleXWidget.singleStep = 1
    self.angleXWidget.minimum = -20
    self.angleXWidget.maximum = 20
    self.angleXWidget.value = 0.0
    self.angleXWidget.setToolTip("needle guide angulation")
    angulationFormLayout.addRow("Angle 1", self.angleXWidget)

    self.angleYWidget = ctk.ctkSliderWidget()
    self.angleYWidget.singleStep = 1
    self.angleYWidget.minimum = -20
    self.angleYWidget.maximum = 20
    self.angleYWidget.value = 0.0
    self.angleYWidget.setToolTip("needle guide angulation")
    angulationFormLayout.addRow("Angle 2", self.angleYWidget)


    # connections
    self.angleXWidget.connect('valueChanged(double)', self.onSliderChange)
    self.angleYWidget.connect('valueChanged(double)', self.onSliderChange)
    self.selectTarget.connect('clicked(bool)', self.onSelectTarget)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.anatomySelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect) #TODO: REMOVE

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

    slicer.util.selectModule('CurveMaker')
    self.cmlogic = slicer.modules.CurveMakerWidget.logic

  def cleanup(self):
    pass

  def onSliderChange(self):

    try:
      path_points = slicer.util.getNode('path')
      self.updatePoints(path_points, 100.0)

    except:
      print('No path selected yet')



    self.cmlogic.updateCurve()


  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.anatomySelector.currentNode()

  def onApplyButton(self):
    logic = PathPlannerLogic()
    imageThreshold = 0
    logic.run(self.inputSelector.currentNode(), self.anatomySelector.currentNode(), self.angleXWidget, self.angleYWidget, self.cmlogic)

  def onSelectTarget(self):

    try:
      target_list = slicer.util.getNode('target')
    except slicer.util.MRMLNodeNotFoundException:
      target_list = slicer.vtkMRMLMarkupsFiducialNode()
      target_list.SetName('target')
      slicer.mrmlScene.AddNode(target_list)

    slicer.modules.markups.logic().StartPlaceMode(0)

  def updatePoints(self,path_points,distance_to_zFrame):
    _point1 = [0.0, 0.0, 0.0]
    _point2 = [0.0, 0.0, 0.0]
    _point3 = [0.0, 0.0, 0.0]
    path_points.GetNthFiducialPosition(0, _point1)
    path_points.GetNthFiducialPosition(1, _point2)
    path_points.GetNthFiducialPosition(2, _point3)
    _angleX = (self.angleXWidget.value)*3.14/180
    _angleY = (self.angleYWidget.value)*3.14/180

    _point3[0] = _point1[0] + distance_to_zFrame * np.sin(_angleX)
    _point3[1] = _point1[1] + distance_to_zFrame * np.sin(_angleY)
    _point3[2] = _point1[2] - distance_to_zFrame

    _point2[0] = _point1[0] +distance_to_zFrame/2.0 * np.sin(_angleX)
    _point2[1] = _point1[1] +distance_to_zFrame/2.0 * np.sin(_angleY)
    _point2[2] = _point1[2] - distance_to_zFrame/2.0

    path_points.SetNthFiducialPosition(1, _point2[0], _point2[1], _point2[2])
    path_points.SetNthFiducialPosition(2, _point3[0], _point3[1], _point3[2])





#
# PathPlannerLogic
#

class PathPlannerLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def createModels(self,labelMapNode, modelHierarchyNode):

    modelMakerCLI = slicer.modules.modelmaker
    # tf = tempfile.NamedTemporaryFile(prefix='Slicer/Models-', suffix='.mrml')

    modelMakerParameters = {}
    # modelMakerParameters['ColorTable'] = 'vtkMRMLColorTableNodeFileGenericAnatomyColors.txt'
    modelMakerParameters['ModelSceneFile'] = modelHierarchyNode.GetID()
    modelMakerParameters['Name'] = 'Model'
    modelMakerParameters['GenerateAll'] = True
    modelMakerParameters['StartLabel'] = -1
    modelMakerParameters['EndLabel'] = -1
    modelMakerParameters['KkipUnNamed'] = True
    modelMakerParameters['JointSmooth'] = True
    modelMakerParameters['Smooth'] = 15
    modelMakerParameters['FilterType'] = 'Sinc'
    modelMakerParameters['Decimate'] = 0.25
    modelMakerParameters['SplitNormals'] = True
    modelMakerParameters['PointNormals'] = True
    modelMakerParameters['InputVolume'] = labelMapNode.GetID()

    slicer.cli.run(modelMakerCLI, None, modelMakerParameters, True)

  def run(self, inputVolume, anatomySelector,angleXWidget, angleYWidget, cmlogic):

    # Create 3D models
    print "Creating 3D surface models for %s " % anatomySelector
    modelHierarchyNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelHierarchyNode")

    slicer.mrmlScene.AddNode(modelHierarchyNode)
    self.createModels(anatomySelector, modelHierarchyNode)

    chnode = modelHierarchyNode.GetNthChildNode(3)
    mnode = chnode.GetAssociatedNode()
    objectPoly = mnode.GetPolyData()

    centerOfmass = vtk.vtkCenterOfMass()
    centerOfmass.SetInputData(objectPoly)
    centerOfmass.SetUseScalarsAsWeights(False)
    centerOfmass.Update()
    center = centerOfmass.GetCenter()
    print(center)


    target_list = slicer.util.getNode("target")


    try:
      path_points = slicer.util.getNode('path')
    except slicer.util.MRMLNodeNotFoundException:
      path_points = slicer.vtkMRMLMarkupsFiducialNode()
      path_points.SetName('path')
      slicer.mrmlScene.AddNode(path_points)
      target_fiducial = slicer.modules.markups.logic().AddFiducial(0, 0, 0)
      anatomy_fiducial = slicer.modules.markups.logic().AddFiducial(0,0,0)
      template_fiducial = slicer.modules.markups.logic().AddFiducial(0,0,0)
      path_points.SetNthFiducialLabel(1, "target")
      path_points.SetNthFiducialLabel(1, "anatomy")
      path_points.SetNthFiducialLabel(2, "insertion")

    ras_target = [0.0,0.0,0.0]
    target_list.GetNthFiducialPosition(0, ras_target)

    path_points.SetNthFiducialPosition(0, ras_target[0], ras_target[1], ras_target[2])
    path_points.SetNthFiducialPosition(1, center[0],center[1],center[2])

    template_position = [0,0,0]
    delta = [center[0]-ras_target[0],center[1]-ras_target[1],center[2]-ras_target[2]]
    template_position[0] = ras_target[0] + delta[0] * 2
    template_position[1] = ras_target[1] + delta[1] * 2
    template_position[2] = ras_target[2] + delta[2] * 2
    path_points.SetNthFiducialPosition(2, template_position[0], template_position[1], template_position[2])

    angle1 = (np.arctan(delta[0]/delta[2]))*180/3.14
    angle2 = (np.arctan(delta[1] / delta[2])) * 180 / 3.14
    angleXWidget.value = angle1
    angleYWidget.value = angle2

    cmlogic.setInterpolationMethod(1)
    cmlogic.setRing(0)
    cmlogic.setTubeRadius(1.0)

    #PArei aqui, instalar o curve maker

    destNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelNode')
    slicer.mrmlScene.AddNode(destNode)
    cmlogic.SourceNode = path_points
    cmlogic.DestinationNode = destNode
    cmlogic.enableAutomaticUpdate(True)
    cmlogic.updateCurve()


    return True


class PathPlannerTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_PathPlanner1()

  def test_PathPlanner1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import SampleData
    SampleData.downloadFromURL(
      nodeNames='FA',
      fileNames='FA.nrrd',
      uris='http://slicer.kitware.com/midas3/download?items=5767')
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = PathPlannerLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
