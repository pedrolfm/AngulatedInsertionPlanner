import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
import sys
import time
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
    self.logic = PathPlannerLogic()
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
    #self.angleXWidget.connect('valueChanged(double)', self.onSliderChange)
    #self.angleYWidget.connect('valueChanged(double)', self.onSliderChange)
    self.selectTarget.connect('clicked(bool)', self.onSelectTarget)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
   

    #
    # Connection area
    #
    ConnectionCollapsibleButton = ctk.ctkCollapsibleButton()
    ConnectionCollapsibleButton.text = "Connection with Smart Template" 
    ConnectionFormLayout = qt.QGridLayout(ConnectionCollapsibleButton) #QBoxLayout(ConnectionCollapsibleButton)
    
    # Connect Button
    self.openIGTL = qt.QPushButton("Connect")
    self.openIGTL.toolTip = "Start openIGTLink"
    self.openIGTL.enabled = True
    #self.layout.addWidget(self.openIGTL)

    
    # zFrame Button
    self.zFrameButton = qt.QPushButton("zFrame")
    self.zFrameButton.toolTip = "Send zFrame"
    self.zFrameButton.enabled = False
    # Target Button
    self.sendTargetButton = qt.QPushButton("Target")
    self.sendTargetButton.toolTip = "send Target"
    self.sendTargetButton.enabled = False
    # Angles Button
    self.sendAngleButton = qt.QPushButton("Angles")
    self.sendAngleButton.toolTip = "send desired Angulation"
    self.sendAngleButton.enabled = False

    # Move Button
    self.sendMoveButton = qt.QPushButton("Move")
    self.sendMoveButton.toolTip = "start motion"
    self.sendMoveButton.enabled = False

    # Init Button
    self.sendInitButton = qt.QPushButton("Init ST")
    self.sendInitButton.toolTip = "initialization"
    self.sendInitButton.enabled = False

    # Reconnect to galil
    self.sendReconnectButton = qt.QPushButton("Reconnect")
    self.sendReconnectButton.toolTip = "Reconect to Galil serial comunication"
    self.sendReconnectButton.enabled = False


    self.footSwitchStatus = qt.QLabel()
    self.footSwitchStatus.setText("Switch OFF")
    self.footSwitchStatus.setStyleSheet("background-color: pink;border: 1px solid black;")

    self.connectionStatus = qt.QLabel()
    self.connectionStatus.setText("Not connected")
    self.connectionStatus.setStyleSheet("background-color: pink;border: 1px solid black;")

    self.zFrameStatus = qt.QLabel()
    self.zFrameStatus.setText("No connection")
    self.zFrameStatus.setStyleSheet("background-color: pink;border: 1px solid black;")

    self.targetStatus = qt.QLabel()
    self.targetStatus.setText("No connection")
    self.targetStatus.setStyleSheet("background-color: pink;border: 1px solid black;")

    self.angleStatus = qt.QLabel()
    self.angleStatus.setText("No connection")
    self.angleStatus.setStyleSheet("background-color: pink;border: 1px solid black;")

    self.layout.addWidget(ConnectionCollapsibleButton)
    ConnectionFormLayout.addWidget(self.zFrameButton,1,1)
    ConnectionFormLayout.addWidget(self.sendTargetButton,1,2)
    ConnectionFormLayout.addWidget(self.sendAngleButton,1,3)
    ConnectionFormLayout.addWidget(self.openIGTL,0,1)
    ConnectionFormLayout.addWidget(self.sendReconnectButton,0,3)
    ConnectionFormLayout.addWidget(self.connectionStatus,0,2)
    ConnectionFormLayout.addWidget(self.sendMoveButton,3,2)
    ConnectionFormLayout.addWidget(self.zFrameStatus,2,1)
    ConnectionFormLayout.addWidget(self.targetStatus,2,2)
    ConnectionFormLayout.addWidget(self.angleStatus,2,3)
    ConnectionFormLayout.addWidget(self.sendInitButton,3,1)



    # connections
    self.openIGTL.connect('clicked(bool)', self.onOpenIGTL)
    self.zFrameButton.connect('clicked(bool)', self.onzFrameButton)
    self.sendTargetButton.connect('clicked(bool)', self.onSendTargetButton)
    self.sendAngleButton.connect('clicked(bool)', self.onSendAngleButton)
    self.sendInitButton.connect('clicked(bool)', self.onSendInitButton)
    self.sendReconnectButton.connect('clicked(bool)', self.onSendReconnectButton)

    
    #self.timer = qt.QTimer()
    
    #self.timer.connect('timeout(bool)', self.onTimeout)

    #self.timer.timeout.connect(self.onTimeout)
    #self.timer.setSingleShot(True)
    #self.timer.start(10000)
    qt.QTimer.singleShot(2000, self.onTimeout)

    #
    # Status Area
    #
    statusCollapsibleButton = ctk.ctkCollapsibleButton()
    statusCollapsibleButton.text = "Smart Template angles"
    self.layout.addWidget(statusCollapsibleButton)

    statusFormLayout = qt.QFormLayout(statusCollapsibleButton)

    self.systemStatus = qt.QLabel()
    self.systemStatus.setText("No zFrame ; No connection ")
    self.systemStatus.setStyleSheet("background-color: white;border: 1px solid black;")
    self.targetStatus = qt.QLabel()
    self.targetStatus.setText("No target ; No angle ")
    self.targetStatus.setStyleSheet("background-color: white;border: 1px solid black;")
    
    statusFormLayout.addRow("Target and angle:", self.systemStatus)
    statusFormLayout.addRow("zFrame and connection:", self.targetStatus)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()


  def onTimeout(self):
    try:
      self.igtl = slicer.util.getNode('OIGTL*')
      if self.igtl.GetState() == 0:
        self.connectionStatus.setStyleSheet("background-color: pink;border: 1px solid black;")
        self.connectionStatus.setText("IGTL - OFF")
      elif self.igtl.GetState() == 1:
        self.connectionStatus.setStyleSheet("background-color: yellow;border: 1px solid black;")
        self.connectionStatus.setText("IGTL - WAIT")
      elif self.igtl.GetState() == 2:
        self.connectionStatus.setStyleSheet("background-color: green;border: 1px solid black;")
        self.connectionStatus.setText("IGTL - ON")
        try:
          self.status1 = slicer.util.getNode('statusTarget')
          self.status2 = slicer.util.getNode('statusZ-Frame')
          self.targetStatus.setText(self.status2.GetText())
          self.systemStatus.setText(self.status1.GetText())
        except:
          print("No status received yet")
    except:
      print("timer4")
      self.systemStatus.setText("No connection")
      self.targetStatus.setText("No connection")
      
    qt.QTimer.singleShot(2000, self.onTimeout)

  def onzFrameButton(self):
    if self.logic.sendZFrame():
      print('- zFrame sent -\n')
    else:
      print('- zFrame NOT sent -\n')

  def onSendAngleButton(self):
    try:
      self.angleTransformation = slicer.util.getNode('angleTransformation')
    except:
      self.angleTransformation = slicer.vtkMRMLLinearTransformNode()
      self.angleTransformation.SetName("angleTransformation")
      slicer.mrmlScene.AddNode(self.angleTransformation)
    if self.logic.sendAngle(self.angleTransformation,self.angleXWidget,self.angleYWidget):
      print('- Angle sent -\n')
    else:
      print('- Angle NOT sent -\n')

  def onSendInitButton(self):
    if self.logic.sendInit():
      print('- Initialization code sent -\n')
    else:
      print('- Initialization code NOT sent -\n')

  def onSendReconnectButton(self):
    if self.logic.sendReconnect():
      print('- Reconnection code sent -\n')
    else:
      print('- Reconnection code NOT sent -\n')


  def onSendTargetButton(self):
    try:
      self.targetTransformation = slicer.util.getNode('targetTransformation')
    except:
      self.targetTransformation = slicer.vtkMRMLLinearTransformNode()
      self.targetTransformation.SetName("targetTransformation")
      slicer.mrmlScene.AddNode(self.targetTransformation)
    try:
      target_list = slicer.util.getNode("target")
      ras_target = [0.0,0.0,0.0]
      target_list.GetNthFiducialPosition(0, ras_target)
    except:
      print('- No Target selected -\n')
      return
    
    if self.logic.sendTarget(self.targetTransformation,ras_target):
      print('- Target sent -\n')
    else:
      print('- Target NOT sent -\n')


  def onOpenIGTL(self):
    if self.logic.openConnection():
      self.connectionStatus.setStyleSheet("background-color: green;border: 1px solid black;")
      self.connectionStatus.setText("OpenIGTL")
      self.zFrameButton.enabled = True
      self.sendTargetButton.enabled = True
      self.sendAngleButton.enabled = True
      
      self.sendInitButton.enabled = True
      self.sendReconnectButton.enabled = True


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
    self.applyButton.enabled = self.inputSelector.currentNode()

  def onApplyButton(self):

    imageThreshold = 0
    self.logic.run(self.inputSelector.currentNode(), self.angleXWidget, self.angleYWidget)


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


  def sendInit(self):
    try:
      self.initText = slicer.util.getNode('INIT')
    except:
      self.initText = slicer.vtkMRMLTextNode()
      self.initText.SetName("INIT")
      self.initText.SetText("INIT")
      slicer.mrmlScene.AddNode(self.initText)
    if self.cnode.GetState() == 2:
      self.cnode.RegisterOutgoingMRMLNode(self.initText)
      self.cnode.PushNode(self.initText)
      time.sleep(0.1)
      self.cnode.UnregisterOutgoingMRMLNode(self.initText)    
      return True
    else:
      print(' Connection not stablished, check OpenIGTLink -')
      return False


  def sendReconnect(self):
    try:
      self.ReconnectText = slicer.util.getNode('SERIAL')
    except:
      self.ReconnectText = slicer.vtkMRMLTextNode()
      self.ReconnectText.SetName("SERIAL")
      self.ReconnectText.SetText("SERIAL")
      slicer.mrmlScene.AddNode(self.ReconnectText)
    if self.cnode.GetState() == 2:
      self.cnode.RegisterOutgoingMRMLNode(self.ReconnectText)
      self.cnode.PushNode(self.ReconnectText)
      time.sleep(0.1)
      self.cnode.UnregisterOutgoingMRMLNode(self.ReconnectText)    
      return True
    else:
      print(' Connection not stablished, check OpenIGTLink -')
      return False



  def sendAngle(self,angleTransformation,sliderX,sliderY):

    X = sliderX.value
    Y = sliderY.value

    try:
      vTransform = vtk.vtkTransform()
      vTransform.RotateX(X)
      vTransform.RotateY(Y)  
      angleTransformation.SetAndObserveMatrixTransformToParent(vTransform.GetMatrix())
      print(angleTransformation)
      
      if self.cnode.GetState() == 2:
        self.cnode.RegisterOutgoingMRMLNode(angleTransformation)
        self.cnode.PushNode(angleTransformation)
        time.sleep(0.1)
        self.cnode.UnregisterOutgoingMRMLNode(angleTransformation)    
        return True
      else:
        print(' Connection not stablished yet -')
        return False
    except:
      e = sys.exc_info()
      print(e)
      print('- Check openIGTLink connection-')
      return False


  def sendTarget(self,targetTransformation,ras_target):
    
    try:
      vTransform = vtk.vtkTransform()
      vTransform.Translate(ras_target[0],ras_target[1],ras_target[2])      
      targetTransformation.SetAndObserveMatrixTransformToParent(vTransform.GetMatrix())
      
      if self.cnode.GetState() == 2:

        self.cnode.RegisterOutgoingMRMLNode(targetTransformation)
        self.cnode.PushNode(targetTransformation)
        time.sleep(0.1)
        self.cnode.UnregisterOutgoingMRMLNode(targetTransformation)    
        return True
      else:
        print(' Connection not stablished yet -')
        return False
    except slicer.util.MRMLNodeNotFoundException:
      print('- There is no Target on Slicer scene -')
      return False
    except:
      e = sys.exc_info()
      print(e)
      print('- Check openIGTLink connection-')
      return False



  def sendZFrame(self):
    try:
      try:
        self.zFrameTransformation = slicer.util.getNode('zFrameTransformation')
      except:
        self.zFrameTransformation = slicer.mrmlScene.CopyNode(slicer.util.getNode('*ZFrameT*'))
        self.zFrameTransformation.SetName("zFrameTransformation")
      print(' - Z frame there. -')
      if self.cnode.GetState() == 2:
        self.cnode.RegisterOutgoingMRMLNode(self.zFrameTransformation)
        self.cnode.PushNode(self.zFrameTransformation)
        print(self.cnode.GetState())
        time.sleep(0.1)
        self.cnode.UnregisterOutgoingMRMLNode(self.zFrameTransformation)    
        return True
      else:
        print('- Connection not stablished yet -')
        return False
    except slicer.util.MRMLNodeNotFoundException:
      print('- There is no zFrame on Slicer scene -')
      return False
    except:
      e = sys.exc_info()
      print(e)
      print('- Check openIGTLink connection-')
      return False

  def openConnection(self):

    if slicer.util.getNodesByClass('vtkMRMLIGTLConnectorNode'):
      self.cnode = slicer.util.getNode('OIGTL*')
      print(' - openIGTLink already open -')
    else:
      self.cnode = slicer.vtkMRMLIGTLConnectorNode()
      slicer.mrmlScene.AddNode(self.cnode)
      self.cnode.SetTypeServer(18944)
      self.cnode.SetName("OIGTL")
      self.cnode.Start()
    
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

  def run(self, inputVolume,angleXWidget, angleYWidget):

    slicer.util.selectModule('ZFrameRegistrationWithROI')

    slicer.util.selectModule('CurveMaker')
    cmlogic = slicer.modules.CurveMakerWidget.logic

    
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
