import os
import unittest
import vtk, qt, ctk, slicer
#from qt.QtWidgets import QTableWidgetItem
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
import sys
import time


AUTOMATIC_PATH = False
#
# PathPlanner
#

# dimentions from the center of the RCM to the edge of the needle guide:
DIM1 = 54.5
DIM2 = 49.5
DIM3 = 44.5
DIM4 = 39.5
DIM5 = 34.5

deg2rad = 3.14/180.0

#translation limits of Smart Template
LIMITS = [-25,25,-30,30]

class PathPlanner(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PathPlanner" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["Pedro Moreira (BWH)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """

"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
.
""" 

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
 #   parametersFormLayout.addRow("Prostate Volume: ", self.inputSelector)


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
    # zframe selector
    #
    self.zFrameSelector = slicer.qMRMLNodeComboBox()
    self.zFrameSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.zFrameSelector.selectNodeUponCreation = True
    self.zFrameSelector.addEnabled = False
    self.zFrameSelector.removeEnabled = False
    self.zFrameSelector.noneEnabled = False
    self.zFrameSelector.showHidden = False
    self.zFrameSelector.showChildNodeTypes = False
    self.zFrameSelector.setMRMLScene( slicer.mrmlScene )
    self.zFrameSelector.setToolTip( "Pick the zframe registration." )
    parametersFormLayout.addRow("zFrame: ", self.zFrameSelector)

    #
    # Target Button
    #
    self.selectTarget = qt.QPushButton("Select Target")
    self.selectTarget.toolTip = "Select Target"
    self.selectTarget.enabled = True
    parametersFormLayout.addRow(self.selectTarget)

    #
    # Add target table
    #
    self.targetTable = qt.QTableWidget()
    self.targetTable.setRowCount(1)
    self.targetTable.setColumnCount(4)
    self.targetTable.setHorizontalHeaderLabels(['Name', 'R', 'A', 'S'])

    parametersFormLayout.addRow(self.targetTable)

    #
    # segmentation selector
    #
    self.segmentationSelector = slicer.qMRMLNodeComboBox()
    self.segmentationSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.segmentationSelector.selectNodeUponCreation = True
    self.segmentationSelector.addEnabled = False
    self.segmentationSelector.removeEnabled = False
    self.segmentationSelector.noneEnabled = False
    self.segmentationSelector.showHidden = False
    self.segmentationSelector.showChildNodeTypes = False
    self.segmentationSelector.setMRMLScene( slicer.mrmlScene )
    self.segmentationSelector.setToolTip( "Pick the segmentation." )

    self.startSegmentation = qt.QPushButton("Segmentation")
    self.startSegmentation.toolTip = "Segmentation module"
    self.startSegmentation.enabled = True
    parametersFormLayout.addRow(self.startSegmentation,self.segmentationSelector)


    parametersFormLayout.addRow(self.selectTarget)

#    label = qt.QLabel(self)
#    pixmap = qt.QPixmap('/Users/pedro/Pictures/ChickenForce.png')
#    label.setPixmap(pixmap)
#    parametersFormLayout.addRow(label)

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
    angulationFormLayout.addRow("Coronal", self.angleXWidget)

    self.angleYWidget = ctk.ctkSliderWidget()
    self.angleYWidget.singleStep = 1
    self.angleYWidget.minimum = -20
    self.angleYWidget.maximum = 20
    self.angleYWidget.value = 0.0
    self.angleYWidget.setToolTip("needle guide angulation")
    angulationFormLayout.addRow("Sagittal", self.angleYWidget)

    # connections
    self.angleXWidget.connect('valueChanged(double)', self.onSliderChange)
    self.angleYWidget.connect('valueChanged(double)', self.onSliderChange)
    self.selectTarget.connect('clicked(bool)', self.onSelectTarget)
    self.zFrameSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onDefineZFrame)
    self.zFrameSelector.connect("nodeActivated(vtkMRMLNode*)", self.onDefineZFrame)
    self.targetSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onReloadTarget)
    self.targetSelector.connect("nodeActivated(vtkMRMLNode*)", self.onReloadTarget)

    # Insertion lengths for the 5 different needle guide positions
    insertionTable1 = qt.QLabel()
    insertionTable1.setText(" pos 1 ")
    insertionTable1.setStyleSheet("background-color: yellow;border: 1px solid black;")
    insertionTable2 = qt.QLabel()
    insertionTable2.setText(" pos 2 ")
    insertionTable2.setStyleSheet("background-color: yellow;border: 1px solid black;")
    insertionTable3 = qt.QLabel()
    insertionTable3.setText(" pos 3 ")
    insertionTable3.setStyleSheet("background-color: yellow;border: 1px solid black;")
    insertionTable4 = qt.QLabel()
    insertionTable4.setText(" pos 4 ")
    insertionTable4.setStyleSheet("background-color: yellow;border: 1px solid black;")
    insertionTable5 = qt.QLabel()
    insertionTable5.setText(" pos 5 ")
    insertionTable5.setStyleSheet("background-color: yellow;border: 1px solid black;")
    self.insertion1 = qt.QLabel()
    self.insertion1.setText(" -- ")
    self.insertion1.setStyleSheet("background-color: white;border: 1px solid black;")
    self.insertion2 = qt.QLabel()
    self.insertion2.setText(" -- ")
    self.insertion2.setStyleSheet("background-color: white;border: 1px solid black;")
    self.insertion3 = qt.QLabel()
    self.insertion3.setText(" -- ")
    self.insertion3.setStyleSheet("background-color: white;border: 1px solid black;")
    self.insertion4 = qt.QLabel()
    self.insertion4.setText(" -- ")
    self.insertion4.setStyleSheet("background-color: white;border: 1px solid black;")
    self.insertion5 = qt.QLabel()
    self.insertion5.setText(" -- ")
    self.insertion5.setStyleSheet("background-color: white;border: 1px solid black;")

    insertionCollapsibleButton = ctk.ctkCollapsibleButton()
    insertionCollapsibleButton.text = "Insertion lengths"
    insertionTable = qt.QGridLayout(insertionCollapsibleButton)
    insertionTable.addWidget(insertionTable1,0,1)
    insertionTable.addWidget(insertionTable2,0,2)
    insertionTable.addWidget(insertionTable3,0,3)
    insertionTable.addWidget(insertionTable4,0,4)
    insertionTable.addWidget(insertionTable5,0,5)
    insertionTable.addWidget(self.insertion1,1,1)
    insertionTable.addWidget(self.insertion2,1,2)
    insertionTable.addWidget(self.insertion3,1,3)
    insertionTable.addWidget(self.insertion4,1,4)
    insertionTable.addWidget(self.insertion5,1,5)
    self.layout.addWidget(insertionCollapsibleButton)

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

    self.galilStatus = qt.QLabel()
    self.galilStatus.setText("No Controller Connection")
    self.galilStatus.setStyleSheet("background-color: pink;border: 1px solid black;")

    self.footswitchStatus = qt.QLabel()
    self.footswitchStatus.setText("Footswitch OFF")
    self.footswitchStatus.setStyleSheet("background-color: pink;border: 1px solid black;")

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

    ConnectionFormLayout.addWidget(self.openIGTL,0,1)
    ConnectionFormLayout.addWidget(self.connectionStatus,0,2)
    ConnectionFormLayout.addWidget(self.galilStatus,0,3)

    ConnectionFormLayout.addWidget(self.zFrameButton,1,1)
    ConnectionFormLayout.addWidget(self.sendTargetButton,1,2)
    ConnectionFormLayout.addWidget(self.sendReconnectButton,1,3)

    ConnectionFormLayout.addWidget(self.zFrameStatus,2,1)
    ConnectionFormLayout.addWidget(self.targetStatus,2,2)
    ConnectionFormLayout.addWidget(self.angleStatus,2,3)

    ConnectionFormLayout.addWidget(self.sendMoveButton,3,2)
    ConnectionFormLayout.addWidget(self.sendInitButton,3,1)

    # connections
    self.openIGTL.connect('clicked(bool)', self.onOpenIGTL)
    self.zFrameButton.connect('clicked(bool)', self.onzFrameButton)
    self.sendTargetButton.connect('clicked(bool)', self.onSendTargetButton)
    self.sendInitButton.connect('clicked(bool)', self.onSendInitButton)
    self.sendReconnectButton.connect('clicked(bool)', self.onSendReconnectButton)
    self.sendMoveButton.connect('clicked(bool)', self.onsendMoveButton)
    self.startSegmentation.connect('clicked(bool)', self.onSegmentButton)
    

    qt.QTimer.singleShot(2000, self.onTimeout)

    #
    # Status Area
    #
    statusCollapsibleButton = ctk.ctkCollapsibleButton()
    statusCollapsibleButton.text = "Smart Template Movements"
    statusFormLayout = qt.QGridLayout(statusCollapsibleButton)
#    statusFormLayout = qt.QFormLayout(statusCollapsibleButton)

    self.USLabel0 = qt.QLabel()
    self.USLabel0.setText("US Motor:")
    self.USLabel0.setStyleSheet("background-color: white;border: 1px solid black;")
    
    self.USLabel1 = qt.QLabel()
    self.USLabel1.setText(" - ")
    self.USLabel1.setStyleSheet("background-color: white;border: 1px solid black;")
    self.USLabel2 = qt.QLabel()
    self.USLabel2.setText(" - ")
    self.USLabel2.setStyleSheet("background-color: white;border: 1px solid black;")

    self.PELabel0 = qt.QLabel()
    self.PELabel0.setText("PE Motor:")
    self.PELabel0.setStyleSheet("background-color: white;border: 1px solid black;")
    
    self.PELabel1 = qt.QLabel()
    self.PELabel1.setText(" - ")
    self.PELabel1.setStyleSheet("background-color: white;border: 1px solid black;")
    self.PELabel2 = qt.QLabel()
    self.PELabel2.setText(" - ")
    self.PELabel2.setStyleSheet("background-color: white;border: 1px solid black;")

    self.layout.addWidget(statusCollapsibleButton)
    statusFormLayout.addWidget(self.PELabel0,0,1)
    statusFormLayout.addWidget(self.PELabel1,0,2)
    statusFormLayout.addWidget(self.PELabel2,0,3)
    statusFormLayout.addWidget(self.USLabel0,1,1)
    statusFormLayout.addWidget(self.USLabel1,1,3)
    statusFormLayout.addWidget(self.USLabel2,1,2)

    layoutManager = slicer.app.layoutManager()
    self.redLogic = layoutManager.sliceWidget("Red").sliceLogic()
    self.greenLogic = layoutManager.sliceWidget("Green").sliceLogic()
    self.yellowLogic = layoutManager.sliceWidget("Yellow").sliceLogic()


    self.logic.loadzFrameModel()

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state

  def onTimeout(self):
    try:
      self.igtl = slicer.util.getNode('OIGTL*')
      if self.igtl.GetState() == 0:
        self.connectionStatus.setStyleSheet("background-color: pink;border: 1px solid black;")
        self.connectionStatus.setText("No connection")
      elif self.igtl.GetState() == 1:
        self.connectionStatus.setStyleSheet("background-color: yellow;border: 1px solid black;")
        self.connectionStatus.setText("IGTL - WAIT")
      elif self.igtl.GetState() == 2:
        self.connectionStatus.setStyleSheet("background-color: lightgreen;border: 1px solid black;")
        self.connectionStatus.setText("IGTL - ON")
        try:
          #get the motorPosition
          tempString1 = slicer.util.getNode('motorPosition')
          temp = tempString1.GetText()
          motorPositions = temp.split(", ")        
          self.USLabel1.setText(motorPositions[0])
          self.USLabel2.setText(motorPositions[1])
          self.PELabel1.setText(motorPositions[2])
          self.PELabel2.setText(motorPositions[3])
        except:
          self.USLabel1.setText("-")
          self.USLabel2.setText("-")
          self.PELabel1.setText("-")
          self.PELabel2.setText("-")
        try:
          tempString1 = slicer.util.getNode('status')
          temp = tempString1.GetText()
          self.galilStatus.setText(temp)
          if temp == "No Galil connection":
            self.galilStatus.setStyleSheet("background-color: pink;border: 1px solid black;")
          elif temp == "FTSW OFF":
            self.galilStatus.setStyleSheet("background-color: yellow;border: 1px solid black;")
          elif temp == "FTSW ON":
            self.galilStatus.setStyleSheet("background-color: lightgreen;border: 1px solid black;")           
        except:
          self.galilStatus.setText("No Controller connection")
          self.galilStatus.setStyleSheet("background-color: pink;border: 1px solid black;")
          self.footswitchStatus.setText("Footswitch OFF")
          self.footswitchStatus.setStyleSheet("background-color: pink;border: 1px solid black;")
        try:
          tempStatus2 = slicer.util.getNode('statusTarget')
          temp = tempStatus2.GetText()
          print(temp)
          targetValues = temp.split(" - ")
          self.targetStatus.setText(targetValues[0])
          self.targetStatus.setStyleSheet("background-color: lightgreen;border: 1px solid black;")  
          self.angleStatus.setText(targetValues[1])
          self.angleStatus.setStyleSheet("background-color: lightgreen;border: 1px solid black;")  
        except:
          print("stop here")
          self.targetStatus.setText("No Controller connection")
          self.targetStatus.setStyleSheet("background-color: pink;border: 1px solid black;")
          self.angleStatus.setText("No Controller connection")
          self.angleStatus.setStyleSheet("background-color: pink;border: 1px solid black;")
    except:
      self.connectionStatus.setText("IGTL - OFF")


    qt.QTimer.singleShot(2000, self.onTimeout)


  def getAngles(self,mtx):
    vTransform = vtk.vtkTransform()
    vTransform.SetMatrix(mtx)
    X = [0.0, 0.0, 0.0]
    vTransform.GetOrientation(X)
    return X


  def onzFrameButton(self):
    if self.logic.sendZFrame(self.zFrameSelector.currentNode()):
      self.zFrameStatus.setText("ZFrame sent")
      self.zFrameStatus.setStyleSheet("background-color: lightgreen;border: 1px solid black;")
      print('- zFrame sent -\n')
    else:
      print('- zFrame NOT sent -\n')

  def onSendInitButton(self):

    slicer.util.selectModule('Homing')
    #if self.logic.sendInit():
    #  print('- Initialization code sent -\n')
    #else:
    #  print('- Initialization code NOT sent -\n')

  def onReloadTarget(self):
    try:
      targets = self.targetSelector.currentNode()
      ras_target = [0.0,0.0,0.0]
      nOfFiducials = targets.GetNumberOfFiducials()
      self.targetTable.setRowCount(nOfFiducials)
      for n in range(nOfFiducials):
          targets.GetNthFiducialPosition(n, ras_target)
          self.targetTable.setItem(n,1, qt.QTableWidgetItem(str(ras_target[0])))
          self.targetTable.setItem(n,2, qt.QTableWidgetItem(str(ras_target[1])))
          self.targetTable.setItem(n,3, qt.QTableWidgetItem(str(ras_target[2])))
          self.targetTable.setItem(n,0, qt.QTableWidgetItem(targets.GetNthFiducialLabel(n)))
    except:
      print('- No target list? -\n')

  def onsendMoveButton(self):
    if self.logic.sendMove():
      print('- Move code sent -\n')
    else:
      print('- Move code NOT sent -\n')

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

    self.sendMoveButton.enabled = True
    
    if self.logic.sendTarget(self.targetTransformation,self.selectedTarget,self.angleXWidget,self.angleYWidget):
      print('- Target sent -\n')
    else:
      print('- Target NOT sent -\n')

  def onOpenIGTL(self):
    if self.logic.openConnection():
      self.connectionStatus.setStyleSheet("background-color: lightgreen;border: 1px solid black;")
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
    except:
      print('No path selected yet')
      return
    self.logic.updatePoints(path_points, 100.0,self.angleXWidget.value,self.angleYWidget.value,self.zFrameSelector.currentNode())
    self.upDateInsertionLength(self.zDistance2Target,1)

  def onDefineZFrame(self):
    self.logic.positionTemplate(self.zFrameSelector.currentNode())
    print("Position tamplate limits")

  def onSegmentButton(self):
    slicer.util.selectModule('Editor')
  
  def onSelectTarget(self):
    try:
        self.selectedTarget = [0.0,0.0,0.0];
        row = self.targetTable.currentItem().row()
        targets = self.targetSelector.currentNode()
        targets.GetNthFiducialPosition(row, self.selectedTarget)
        self.angleXWidget.value = 0.0
        self.angleYWidget.value = 0.0
        nOfRows = self.targetTable.rowCount
        if not AUTOMATIC_PATH:
            self.zDistance2Target = self.logic.pathStraight(self.selectedTarget,self.zFrameSelector.currentNode())
            self.upDateInsertionLength(self.zDistance2Target,0)
        else:
            self.zDistance2Target = self.logic.path(self.angleXWidget, self.angleYWidget,self.selectedTarget,self.segmentationSelector.currentNode(),self.zFrameSelector.currentNode())
            self.upDateInsertionLength(self.zDistance2Target, 1)
        for r in range(nOfRows):
            self.targetTable.item(r,1).setForeground(qt.QColor(1,1,1))
            self.targetTable.item(r,2).setForeground(qt.QColor(1,1,1))
            self.targetTable.item(r,3).setForeground(qt.QColor(1,1,1))
            self.targetTable.item(r,1).setBackground(qt.QColor(255,255,255))
            self.targetTable.item(r,2).setBackground(qt.QColor(255,255,255))
            self.targetTable.item(r,3).setBackground(qt.QColor(255,255,255)) 
        self.targetTable.item(row,1).setForeground(qt.QColor(125,1,1))
        self.targetTable.item(row,2).setForeground(qt.QColor(125,1,1))
        self.targetTable.item(row,3).setForeground(qt.QColor(125,1,1))
        self.targetTable.item(row,1).setBackground(qt.QColor(255,100,100))
        self.targetTable.item(row,2).setBackground(qt.QColor(255,100,100))
        self.targetTable.item(row,3).setBackground(qt.QColor(255,100,100))

        
        # Print current slice offset position
        print(self.selectedTarget)
        self.redLogic.SetSliceOffset(self.selectedTarget[2])
        self.greenLogic.SetSliceOffset(self.selectedTarget[1])
        self.yellowLogic.SetSliceOffset(-self.selectedTarget[0])

    except:
        slicer.util.errorDisplay("No target selected")

  def upDateInsertionLength(self,ins,type):
    if type == 0 and ins > 0:
      self.insertion1.setText(str(int(ins + DIM1)) + "mm")
      self.insertion2.setText(str(int(ins + DIM2)) + "mm")
      self.insertion3.setText(str(int(ins + DIM3)) + "mm")
      self.insertion4.setText(str(int(ins + DIM4)) + "mm")
      self.insertion5.setText(str(int(ins + DIM5)) + "mm")
    elif type == 1 and ins > 0:
      alpha = deg2rad*self.angleXWidget.value
      beta = deg2rad*self.angleYWidget.value
      ins = ins/np.cos(alpha)
      ins = ins/np.cos(beta)
      print(ins)
      self.insertion1.setText(str(int(ins + DIM1)) + "mm")
      self.insertion2.setText(str(int(ins + DIM2)) + "mm")
      self.insertion3.setText(str(int(ins + DIM3)) + "mm")
      self.insertion4.setText(str(int(ins + DIM4)) + "mm")
      self.insertion5.setText(str(int(ins + DIM5)) + "mm")

#
# PathPlannerLogic
#
class PathPlannerLogic(ScriptedLoadableModuleLogic):


  def positionTemplate(self,zFrame):


    vTransform_t = vtk.vtkTransform()
    vTransform_t.Translate(0,107.0,-114)
    vTransform_r = vtk.vtkTransform()
    vTransform_r.RotateX(-90)
    vT_temp = vtk.vtkTransform()
    vT_temp2 = vtk.vtkTransform()

    #vtk.vtkMatrix4x4.Multiply4x4(zFrame.GetMatrixTransformFromParent(),vTransform_r.GetMatrix(),vT_temp.GetMatrix())
    
    #vtk.vtkMatrix4x4.Multiply4x4(vTransform_r.GetMatrix(),vTransform_t.GetMatrix(),vT_temp.GetMatrix())
    vtk.vtkMatrix4x4.Multiply4x4(vTransform_t.GetMatrix(),vTransform_r.GetMatrix(),vT_temp.GetMatrix())
    vtk.vtkMatrix4x4.Multiply4x4(vT_temp.GetMatrix(),zFrame.GetMatrixTransformFromParent(),vT_temp2.GetMatrix())

    print(zFrame.GetMatrixTransformToParent())
    print(vT_temp.GetMatrix())
    print(vT_temp2.GetMatrix())

    mtx = vtk.vtkMatrix4x4()
    mtx_input = vtk.vtkMatrix4x4()
    zFrame.GetMatrixTransformToWorld(mtx_input)
    mtx = self.transformZframe(mtx_input)

    transformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode")
    transformNode.SetAndObserveMatrixTransformToParent(mtx)#vT_temp2.GetMatrix())
       
    self.zFrameModelNode.SetAndObserveTransformNodeID(transformNode.GetID())
    self.zFrameModelNode.GetDisplayNode().SetVisibility(True)
    self.zFrameModelNode.GetDisplayNode().SetSliceIntersectionVisibility(True)

  def loadzFrameModel(self):

    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(dir_path)
    _, self.zFrameModelNode = slicer.util.loadModel(dir_path+"/Resources/templateLimits.vtk", returnNode=True)
    slicer.mrmlScene.AddNode(self.zFrameModelNode)
    self.zFrameModelNode.GetDisplayNode().SetSliceIntersectionVisibility(False)
    self.zFrameModelNode.GetDisplayNode().SetSliceIntersectionThickness(3)
    self.zFrameModelNode.GetDisplayNode().SetColor(1,1,0)
    self.zFrameModelNode.GetDisplayNode().SetVisibility(False)

    try:
      destNode = slicer.util.getNode('pathModel')
    except:
      destNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelNode')
      destNode.SetName('pathModel')
      slicer.mrmlScene.AddNode(destNode)
    print("LOADED MODEL")

  def setzFrameVisibility(self,param):
    self.zFrameModelNode.SetDisplayVisibility(param)    

  def updatePoints(self,path_points,distance_to_zFrame,angleX,angleY,zFrameTransform):
    _point1 = [0.0, 0.0, 0.0]
    _point2 = [0.0, 0.0, 0.0]
    _point3 = [0.0, 0.0, 0.0]
    path_points.GetNthFiducialPosition(0, _point1)
    path_points.GetNthFiducialPosition(1, _point2)
    path_points.GetNthFiducialPosition(2, _point3)
    _angleX = (angleX)*3.14/180
    _angleY = (angleY)*3.14/180

    _point3[0] = _point1[0] + distance_to_zFrame * np.sin(_angleX)
    _point3[1] = _point1[1] + distance_to_zFrame * np.sin(_angleY)
    _point3[2] = _point1[2] - distance_to_zFrame


    _point2[0] = _point1[0] + distance_to_zFrame/2.0 * np.sin(_angleX)
    _point2[1] = _point1[1] + distance_to_zFrame/2.0 * np.sin(_angleY)
    _point2[2] = _point1[2] - distance_to_zFrame/2.0

    path_points.SetNthFiducialPosition(1, _point2[0], _point2[1], _point2[2])
    path_points.SetNthFiducialPosition(2, _point3[0], _point3[1], _point3[2])



    try:
      destNode = slicer.util.getNode('pathModel')
            
    except slicer.util.MRMLNodeNotFoundException:
      destNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelNode')
      destNode.SetName('pathModel')
      slicer.mrmlScene.AddNode(destNode)

    markupsToModel = slicer.modules.markupstomodel.logic()
    markupsToModel.UpdateClosedSurfaceModel(path_points, destNode, True)
    #destNode.GetDisplayNode().SetVisibility(True)

    mtx = vtk.vtkMatrix4x4()
    mtx_input = vtk.vtkMatrix4x4()
    zFrameTransform.GetMatrixTransformToWorld(mtx_input)
    mtx = self.transformZframe(mtx_input)

    mtx.Invert()
    _input = [_point3[0], _point3[1], _point3[2], 1]
    entry_z = [0.0, 0.0, 0.0, 1]
    mtx.MultiplyPoint(_input,entry_z)
    print(entry_z)
    self.setColorPath(entry_z)


  def setColorPath(self,entry):
    destNode = slicer.util.getNode('pathModel')
    if entry[0] < LIMITS[0] or entry[0] > LIMITS[1] or entry[1] < LIMITS[2] or entry[1] > LIMITS[3]:
      destNode.GetDisplayNode().SetColor(1, 0, 0)
    else:
      destNode.GetDisplayNode().SetColor(0, 1, 0)


  def sendMove(self):
    try:
      self.moveText = slicer.util.getNode('MOVE')
    except:
      self.moveText = slicer.vtkMRMLTextNode()
      self.moveText.SetName("MOVE")
      self.moveText.SetText("MOVE")
      slicer.mrmlScene.AddNode(self.moveText)
    if self.cnode.GetState() == 2:
      self.cnode.RegisterOutgoingMRMLNode(self.moveText)
      self.cnode.PushNode(self.moveText)
      time.sleep(0.1)
      self.cnode.UnregisterOutgoingMRMLNode(self.moveText)    
      return True
    else:
      print(' Connection not stablished, check OpenIGTLink -')
      return False

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
 #     e = sys.exc_info()
      print('- Check openIGTLink connection-')
      return False

  def sendTarget(self,targetTransformation,ras_target,sliderX,sliderY):
    X = -sliderX.value
    Y = -sliderY.value
    try:
      vTransform = vtk.vtkTransform()
      vTransform.Translate(ras_target[0],ras_target[1],ras_target[2]) 
      vTransform.RotateX(X)
      vTransform.RotateY(Y)     
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

  def sendZFrame(self,zFrame):

    if zFrame:
      zFrame.SetName("zFrameTransformation")
      if self.cnode.GetState() == 2:
        self.cnode.RegisterOutgoingMRMLNode(zFrame)
        self.cnode.PushNode(zFrame)
        time.sleep(0.1)
        self.cnode.UnregisterOutgoingMRMLNode(zFrame) 
        return True
      else:
        print('- Check openIGTLink connection-')
        return False
    else:
      print('- There is no zFrame on Slicer scene -')
      return False    

  def openConnection(self):

    try:
      slicer.util.getNodesByClass('vtkMRMLIGTLConnectorNode')
      self.cnode = slicer.util.getNode('OIGTL*')
      print(' - openIGTLink already open -')
    except:
      self.cnode = slicer.vtkMRMLIGTLConnectorNode()
      slicer.mrmlScene.AddNode(self.cnode)
      self.cnode.SetTypeClient('192.168.7.2',18944)
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

  def GetCenter(self, inputVolume2):

    try:
      chnode = slicer.util.getNode("Model_1_tissue")
    except:
      modelHierarchyNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelHierarchyNode")
      modelHierarchyNode.SetName("ModelHierarchy")
      slicer.mrmlScene.AddNode(modelHierarchyNode)
      self.createModels(inputVolume2, modelHierarchyNode)
      chnode = slicer.util.getNode("Model_1_tissue")
    print("test")

    #mnode = chnode.GetAssociatedNode()
    objectPoly = chnode.GetPolyData()
    print(chnode)
    centerOfmass = vtk.vtkCenterOfMass()
    centerOfmass.SetInputData(objectPoly)
    centerOfmass.SetUseScalarsAsWeights(False)
    centerOfmass.Update()
    #self.Center = centerOfmass.GetCenter()
    return centerOfmass.GetCenter()

  def transformZframe(self,zFrame):
    _rotation = vtk.vtkMatrix4x4()
    _translation = vtk.vtkMatrix4x4()

    _translation.Identity()
    _translation.SetElement(1,3,107.0)
    _translation.SetElement(2,3,-114.0)

    _rotation.Identity()
    _rotation.SetElement(1,1,0.0)
    _rotation.SetElement(1,2,1.0)
    _rotation.SetElement(2,1,-1.0)
    _rotation.SetElement(2,2,0.0)

    _temp = vtk.vtkMatrix4x4()
    rotatedZframe = vtk.vtkMatrix4x4()
    
    vtk.vtkMatrix4x4.Multiply4x4(zFrame, _rotation, _temp)
    vtk.vtkMatrix4x4.Multiply4x4(_translation, _temp, rotatedZframe)

    return rotatedZframe

  def pathStraight(self,selected_target,zFrameTransform):

    mtx = vtk.vtkMatrix4x4()
    mtx_input = vtk.vtkMatrix4x4()
    zFrameTransform.GetMatrixTransformToWorld(mtx_input)
    mtx = self.transformZframe(mtx_input)

    #TODO: check
    mtx.Invert()

    
    _input = [selected_target[0], selected_target[1], selected_target[2], 1]
    target_z = [0.0, 0.0, 0.0, 1]
    mtx.MultiplyPoint(_input,target_z)

    self.target_z = target_z

    zdist = target_z[2] #add 100, but we need to remove that.
    print("====")
    print(selected_target)
    print(target_z)
    print("StraightPath...")
    try:
      path_points = slicer.util.getNode('path')
    except slicer.util.MRMLNodeNotFoundException:
      path_points = slicer.vtkMRMLMarkupsFiducialNode()
      path_points.SetName('path')
      slicer.mrmlScene.AddNode(path_points)
      target_fiducial = slicer.modules.markups.logic().AddFiducial(0, 0, 0)
      anatomy_fiducial = slicer.modules.markups.logic().AddFiducial(0,0,0)
      template_fiducial = slicer.modules.markups.logic().AddFiducial(0,0,0)
      path_points.SetNthFiducialLabel(0, "target")
      path_points.SetNthFiducialLabel(1, "anatomy")
      path_points.SetNthFiducialLabel(2, "insertion")

    path_points.SetDisplayVisibility(False)
    center_z = [target_z[0], target_z[1], target_z[2]/2.0, 1.0]

    entry_z = [target_z[0], target_z[1], 0, 1.0]

    print(target_z)
    print("StraightPath...2")
    count = 0
    check = self.checkKinematics(entry_z,center_z,target_z,zdist) 
    if check == 1 or check == 2:
      entry_z = self.findEntry(entry_z,center_z,target_z)      
      center_z = [entry_z[0]+(target_z[0]-entry_z[0])/2.0, entry_z[1]+(target_z[1]-entry_z[1])/2.0, target_z[2]/2.0, 1.0]
    print(entry_z)
    check = self.checkKinematics(entry_z,center_z,target_z,zdist)
    if check == 1 or check == 2:
      center_z = self.findNewCenter(entry_z,center_z,target_z,zdist,check)
      _diff_R = -(zdist*(center_z[0]-target_z[0]))/(center_z[2]-target_z[2])
      _diff_A = -(zdist*(center_z[1]-target_z[1]))/(center_z[2]-target_z[2])
      entry_z = [target_z[0]+_diff_R, target_z[1]+_diff_A, target_z[2]-zdist, 1.0] 
    print(entry_z)

    entry = [0.0, 0.0, 0.0, 1]
    center = [0.0, 0.0, 0.0, 1]
    mtx.Invert()
    mtx.MultiplyPoint(entry_z,entry)
    mtx.MultiplyPoint(center_z,center)

    path_points.SetNthFiducialPosition(0, selected_target[0], selected_target[1], selected_target[2])
    path_points.SetNthFiducialPosition(1, center[0], center[1], center[2])
    path_points.SetNthFiducialPosition(2, entry[0], entry[1], entry[2])

    try:
      destNode = slicer.util.getNode('pathModel')
    except:
      destNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelNode')
      destNode.SetName('pathModel')
      slicer.mrmlScene.AddNode(destNode)

    markupsToModel = slicer.modules.markupstomodel.logic()
    markupsToModel.UpdateClosedSurfaceModel(path_points, destNode, True)
    destNode.SetDisplayVisibility(True)

    try:
      modelDisplay = slicer.util.getNode('displayPath')
      modelDisplay.SetColor(0,1,0)
    except:
      modelDisplay = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelDisplayNode')
      modelDisplay.SetName('displayPath')
      modelDisplay.SetColor(0,1,0)
      slicer.mrmlScene.AddNode(modelDisplay)


    modelDisplay.SetSliceIntersectionVisibility(True)
    modelDisplay.SetSliceIntersectionThickness(3)
    modelDisplay.SetVisibility(True)
    destNode.SetAndObserveDisplayNodeID(modelDisplay.GetID())

    
#    destNode.GetDisplayNode().SetSliceIntersectionVisibility(True)

    red_logic = slicer.app.layoutManager().sliceWidget("Red").sliceLogic()
    red_logic.GetSliceCompositeNode().SetBackgroundVolumeID(slicer.util.getNode('*PROSTATE*').GetID())
    return target_z[2]

  def findEntry(self,entry,center,target):
    print(entry)
    print(target)
    if target[0] > LIMITS[1]:
      entry[0] = LIMITS[1]
    if target[0] < LIMITS[0]:
      entry[0] = LIMITS[0]
    if target[1] > LIMITS[3]:
      entry[1] = LIMITS[3]
    if target[1] < LIMITS[2]:
      entry[1] = LIMITS[2]
    print(entry)
    print(target)
    return entry

  def path(self,angleXWidget, angleYWidget,selected_target,labelMapNode,zFrameTransform):

    mtx = vtk.vtkMatrix4x4()
    mtx_input = vtk.vtkMatrix4x4()
    zFrameTransform.GetMatrixTransformToWorld(mtx_input)
    mtx = self.transformZframe(mtx_input)

    mtx.Invert()
    center = self.GetCenter(labelMapNode)
    _input = [selected_target[0], selected_target[1], selected_target[2], 1]
    target_z = [0.0, 0.0, 0.0, 1]
    mtx.MultiplyPoint(_input,target_z)

    self.target_z = target_z

    _input = [center[0], center[1], center[2], 1]
    center_z = [0.0, 0.0, 0.0, 1]
    mtx.MultiplyPoint(_input,center_z)
    
    zdist = target_z[2] #add 100, but we need to remove that.

    try:
      path_points = slicer.util.getNode('path')
            
    except slicer.util.MRMLNodeNotFoundException:
      path_points = slicer.vtkMRMLMarkupsFiducialNode()
      path_points.SetName('path')
      slicer.mrmlScene.AddNode(path_points)
      target_fiducial = slicer.modules.markups.logic().AddFiducial(0, 0, 0)
      anatomy_fiducial = slicer.modules.markups.logic().AddFiducial(0,0,0)
      template_fiducial = slicer.modules.markups.logic().AddFiducial(0,0,0)
      path_points.SetNthFiducialLabel(0, "target")
      path_points.SetNthFiducialLabel(1, "anatomy")
      path_points.SetNthFiducialLabel(2, "insertion")

    path_points.SetDisplayVisibility(False)
    _diff_R = -(zdist*(center_z[0]-target_z[0]))/(center_z[2]-target_z[2])
    _diff_A = -(zdist*(center_z[1]-target_z[1]))/(center_z[2]-target_z[2])

    entry_z = [target_z[0]+_diff_R, target_z[1]+_diff_A, target_z[2]-zdist, 1.0]

    count = 0
    check = self.checkKinematics(entry_z,center_z,target_z,zdist) 

    if check == 1 or check == 2:
      center_z = self.findNewCenter(entry_z,center_z,target_z,zdist,check)
      _diff_R = -(zdist*(center_z[0]-target_z[0]))/(center_z[2]-target_z[2])
      _diff_A = -(zdist*(center_z[1]-target_z[1]))/(center_z[2]-target_z[2])
      entry_z = [target_z[0]+_diff_R, target_z[1]+_diff_A, target_z[2]-zdist, 1.0]       
    check = self.checkKinematics(entry_z,center_z,target_z,zdist)

    entry = [0.0, 0.0, 0.0, 1]
    center = [0.0, 0.0, 0.0, 1]
    mtx.Invert()
    mtx.MultiplyPoint(entry_z,entry)
    mtx.MultiplyPoint(center_z,center)

    path_points.SetNthFiducialPosition(0, selected_target[0], selected_target[1], selected_target[2])
    path_points.SetNthFiducialPosition(1, center[0], center[1], center[2])
    path_points.SetNthFiducialPosition(2, entry[0], entry[1], entry[2])

    try:
      destNode = slicer.util.getNode('pathModel')
    except:
      destNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelNode')
      destNode.SetName('pathModel')
      slicer.mrmlScene.AddNode(destNode)

    markupsToModel = slicer.modules.markupstomodel.logic()
    markupsToModel.UpdateClosedSurfaceModel(path_points, destNode, True)
    destNode.SetDisplayVisibility(True) 

    try:
      modelDisplay = slicer.util.getNode('displayPath')
      modelDisplay.SetColor(0,1,0)
    except:
      modelDisplay = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelDisplayNode')
      modelDisplay.SetName('displayPath')
      modelDisplay.SetColor(0,1,0)
      slicer.mrmlScene.AddNode(modelDisplay)

    modelDisplay.SetSliceIntersectionVisibility(True)
    modelDisplay.SetSliceIntersectionThickness(3)
    modelDisplay.SetVisibility(True)
    destNode.SetAndObserveDisplayNodeID(modelDisplay.GetID())

    angleXWidget.value = -np.arcsin((center[0]-selected_target[0])/(center[2]-selected_target[2]))*(180/3.14)
    angleYWidget.value = -np.arcsin((center[1]-selected_target[1])/(center[2]-selected_target[2]))*(180/3.14)

#    red_logic = slicer.app.layoutManager().sliceWidget("Red").sliceLogic()
#    red_logic.GetSliceCompositeNode().SetBackgroundVolumeID(slicer.util.getNode('*PROSTATE*').GetID())
    return zdist


  def findNewCenter(self,entry,center,target,zdist,case):
    if case == 1:
      if entry[0] < LIMITS[0]:
        entry[0] = LIMITS[0]
      if entry[0] > LIMITS[1]:
        entry[0] = LIMITS[1]
      if entry[1] < LIMITS[2]:
        entry[1] = LIMITS[2]
      if entry[1] > LIMITS[3]:
        entry[1] = LIMITS[3]
      _angle1 = (entry[0]-target[0])/zdist
      _angle2 = (entry[1]-target[1])/zdist
      print(_angle1)
      print(_angle2)
      if _angle1 < -1.0:
        _angle1 = -1.0
      if _angle1 > 1.0:
        _angle1 = 1.0
      if _angle2 < -1.0:
        _angle2 = -1.0
      if _angle2 > 1.0:
        _angle2 = 1.0
      angle1 = np.arcsin(_angle1)
      angle2 = np.arcsin(_angle2)
      print(angle1)
      print(angle2)
    else:
      _angle1 = (entry[0]-target[0])/zdist
      _angle2 = (entry[1]-target[1])/zdist
      if _angle1 < -1.0:
        _angle1 = -1.0
      if _angle1 > 1.0:
        _angle1 = 1.0
      if _angle2 < -1.0:
        _angle2 = -1.0
      if _angle2 > 1.0:
        _angle2 = 1.0
      angle1 = np.arcsin(_angle1)
      angle2 = np.arcsin(_angle2)
      if angle1 > 0.35:
        angle1 = 0.35
      if angle1 < -0.35:
        angle1 = -0.35
      if angle2 > 0.35:
        angle2 = 0.35
      if angle2 < -0.35:
        angle2 = -0.35
    centerNew = [0.0, 0.0, 0.0, 1]
    centerNew[0] = target[0]+np.sin(angle1)*(target[2]-center[2])
    centerNew[1] = target[1]+np.sin(angle2)*(target[2]-center[2])
    centerNew[2] = center[2]
    return centerNew

  def checkKinematics(self,entry,center,target,zdist):
    _test1 = np.arcsin((entry[0]-target[0])/zdist)
    _test2 = np.arcsin((entry[1]-target[1])/zdist)
    if _test1<-0.35 or _test1>0.35:
      print("angle limit reached")
      return 1
    if entry[0]<LIMITS[0] or entry[0]>LIMITS[1] or entry[1]<LIMITS[2] or entry[1]>LIMITS[3]:
      print("translation limit reached")
      return 2
    
    print("angle Ok")
    return 0
 


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
