import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time

#
# Homing
#

class Homing(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Homing" # TODO make this more human readable by adding spaces
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
# HomingWidget
#

class HomingWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Ultrasonic motors Area
    #
    ultrasonicMotorsCollapsibleButton = ctk.ctkCollapsibleButton()
    ultrasonicMotorsCollapsibleButton.text = "Shinsei motors"
    self.layout.addWidget(ultrasonicMotorsCollapsibleButton)
    ultrasonicFormLayout = qt.QFormLayout(ultrasonicMotorsCollapsibleButton)
    # Apply Button
    self.applyButton = qt.QPushButton("Homing Shinsei")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = True
    ultrasonicFormLayout.addRow(self.applyButton)
    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    # Add vertical spacer
    self.layout.addStretch(1)


    #
    # Piezo motors Area
    #
    piezoMotorsCollapsibleButton = ctk.ctkCollapsibleButton()
    piezoMotorsCollapsibleButton.text = "Piezo motors"
    self.layout.addWidget(piezoMotorsCollapsibleButton)
    piezoFormLayout = qt.QFormLayout(piezoMotorsCollapsibleButton)


    #
    # Add target table
    #
    self.positionTable = qt.QTableWidget()
    self.positionTable.setRowCount(3)
    self.positionTable.setColumnCount(3)
    self.positionTable.setHorizontalHeaderLabels(['1', '2', '3'])

    self.cbh = qt.QComboBox()
    self.cbh.addItem("Left")
    self.cbh.addItem("Center")
    self.cbh.addItem("Right")
    self.cbh.currentIndexChanged.connect(self.onSelectionChange)
		
    piezoFormLayout.addRow("Horizontal:",self.cbh)


    self.cbv = qt.QComboBox()
    self.cbv.addItems([str('Top'), str('Center'), str('Bottom')])
    self.cbv.currentIndexChanged.connect(self.onSelectionChange)
		
    piezoFormLayout.addRow("Vertical:",self.cbv)


    self.label = qt.QLabel()
    pixmap = qt.QPixmap('/Resources/CB.png')
    self.label.setPixmap(pixmap)

    piezoFormLayout.addRow(self.label)


    # Apply Button
    self.piezoHomingButton = qt.QPushButton("Homing Piezo")
    self.piezoHomingButton.toolTip = "Run the algorithm."
    self.piezoHomingButton.enabled = True
    piezoFormLayout.addRow(self.piezoHomingButton)
    # connections
    self.piezoHomingButton.connect('clicked(bool)', self.onPiezoHomingButton)
    # Add vertical spacer

    # Apply Button
    self.doneHomingButton = qt.QPushButton("Done Homing")
    self.doneHomingButton.toolTip = "Run the algorithm."
    self.doneHomingButton.enabled = True
    piezoFormLayout.addRow(self.doneHomingButton)
    # connections
    self.doneHomingButton.connect('clicked(bool)', self.onDoneHoming)
    # Add vertical spacer

  def cleanup(self):
    pass


  def onSelectionChange(self):

    horizontalPosition = self.cbh.currentText
    verticalPosition = self.cbv.currentText
    if horizontalPosition == "Left":
      nameh = "L"
    elif horizontalPosition == "Center":
      nameh = "C"
    elif horizontalPosition == "Right":
      nameh = "R"
    if verticalPosition == "Top":
      namev = "T"
    elif verticalPosition == "Center":
      namev = "C"
    elif verticalPosition == "Bottom":
      namev = "B"
    name = nameh + namev
    pixmap = qt.QPixmap('/home/smart/Documents/Modules/AngulatedInsertionPlanner/Homing/Resources/'+name+'.png')
    self.label.setPixmap(pixmap)

  def onApplyButton(self):

    dlg = qt.QMessageBox()
    dlg.setWindowTitle("Alert!")
    dlg.setText("Are the protective COVER and the NEEDLE GUIDE removed from the Smart Template? \n \n \n Click OK to proceed")
    dlg.setStyleSheet("background-color: rgb(128, 0, 0);color: rgb(255, 255, 255);")
    button = dlg.exec()
 
    if button == qt.QMessageBox.Ok:
      logic = HomingLogic()
      if logic.checkConnection():
        if logic.sendInitUS():
          print('- Initialization code sent -\n')
        else:
          print('- Initialization code NOT sent -\n')
      else:
        print("No openIGTLink")


  def onPiezoHomingButton(self):
  
    dlg = qt.QMessageBox()
    dlg.setWindowTitle("Alert!")
    dlg.setText("Are the protective COVER and the NEEDLE GUIDE removed from the Smart Template? \n Click OK to proceed")
    button = dlg.exec()
    #if button == qt.QMessageBox.Ok:
    # print("cancel")
    #  return
    logic = HomingLogic()
    horizontalPosition = self.cbh.currentText
    verticalPosition = self.cbv.currentText
    if horizontalPosition == "Left":
      nameh = "L"
    elif horizontalPosition == "Center":
      nameh = "C"
    elif horizontalPosition == "Right":
      nameh = "R"
    if verticalPosition == "Top":
      namev = "T"
    elif verticalPosition == "Center":
      namev = "C"
    elif verticalPosition == "Bottom":
      namev = "B"
    name = nameh + namev
    if logic.checkConnection():
      if logic.sendInitPM(name):
        print('- Initialization code sent -\n')
      else:
        print('- Initialization code NOT sent -\n')
    else:
      print("No openIGTLink")
    

  def onDoneHoming(self):
    slicer.util.selectModule('PathPlanner')

#
# HomingLogic
#

class HomingLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def checkConnection(self):
    if slicer.util.getNodesByClass('vtkMRMLIGTLConnectorNode'):
      self.cnode = slicer.util.getNode('OIGTL*')
      print(' - openIGTLink already open -')
      return True
    else:
      return False


  def sendInitUS(self):
    try:
      self.initText = slicer.util.getNode('INIT')
    except:
      self.initText = slicer.vtkMRMLTextNode()
      self.initText.SetName("INIT")
      slicer.mrmlScene.AddNode(self.initText)
    self.initText.SetText("INITUS")
    if self.cnode.GetState() == 2:
      self.cnode.RegisterOutgoingMRMLNode(self.initText)
      self.cnode.PushNode(self.initText)
      time.sleep(2)
      self.cnode.UnregisterOutgoingMRMLNode(self.initText)    
      return True
    else:
      print(' Connection not stablished, check OpenIGTLink -')
      return False


  def sendInitPM(self,position):
    try:
      self.initText = slicer.util.getNode('INIT')
    except:
      self.initText = slicer.vtkMRMLTextNode()
      self.initText.SetName("INIT")
      slicer.mrmlScene.AddNode(self.initText)
    self.initText.SetText("INIT"+position)
    if self.cnode.GetState() == 2:
      self.cnode.RegisterOutgoingMRMLNode(self.initText)
      self.cnode.PushNode(self.initText)
      time.sleep(0.1)
      self.cnode.UnregisterOutgoingMRMLNode(self.initText)    
      return True
    else:
      print(' Connection not stablished, check OpenIGTLink -')
      return False
      


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

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('HomingTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True


class HomingTest(ScriptedLoadableModuleTest):
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
    self.test_Homing1()

  def test_Homing1(self):
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
    logic = HomingLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
