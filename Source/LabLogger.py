import sys
import xlsxwriter
import os
from   datetime import datetime, date, time
import numpy as np
import pyvisa
import time
import random
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt6.QtWidgets import QMainWindow, QComboBox, QStackedLayout, QRadioButton, QLabel, QButtonGroup, QApplication, QWidget, QListWidget, QFormLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import QTimer,Qt, QRect
from PyQt5.QtGui import QPainter, QBrush, QPen

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class DeviceCanvas():
    def __init__(self) -> None:
        pass

class Measurement():
    def __init__(self, name = "", call = "", check = "", fetch = "", delay = 100, show = False):
        self.name = name
        self.call = call
        self.check = check
        self.fetch = fetch
        self.delay = delay
        self.show = show
        self.data = []

    def setName(self, string):
        self.name = string

    def setCall(self, command):
        self.call = command

    def setFetch(self, command):
        self.fetch = command

    def setCheck(self, command):
        self.check = command
    
    def setDelay(self, delay_ms):
        self.delay = delay_ms
    
    def insertData(self, data):
        self.data.append(data)

    def getName(self):
        return self.name

    def getCall(self):
        return self.call

    def getFetch(self):
        return self.fetch
    
    def getCheck(self):
        return self.check

class MasurementGroupe():
    def __init__(self, name = "", call = "", check = ""):
        self.name = name
        self.call = call
        self.check = check
        self.measurements = []

    def setName(self, string):
        self.name = string

    def setCall(self, command):
        self.call = command
    
    def setCheck(self, command):
        self.check = command
    
    def addMeasurement(self, meas):
        self.measurements.append(meas)

    def clearMeasurement(self):
        self.measurements.clear()

    def madifyMeasurement(self, meas, index):
        self.measurements[index] = meas

    def getName(self):
        return self.name

    def getCall(self):
        return self.call
    
    def getCheck(self):
        return self.check

class Sensor():
    def __init__(self, number = "", name = ""):
        self.number = number
        self.name = name
        self.sensor = []
    
    def addMeasureGroup(self, MeasureGroupe):
        self.sensor.append(MeasureGroupe)

    def removeMeasureGroup(self, index):
        self.sensor.pop(index-1)

class Experiment():
    def __init__(self):
        self.experiment = []

    def addSensor(self, Sensor):
        self.experiment.append(Sensor)

    def removeSensor(self, index):
        self.experiment.pop(index-1)

class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setMinimumSize(900, 660)
        self.setMaximumSize(900, 660)    
        self.setWindowTitle("LabLogger")

        # local variables
        self.now = datetime.now()
        self.running = False
        self.connected = False
        self.PPause = False
        self.deviceList = []
        self.connectDevise = ""
        self.openScriptFile = ""
        self.scriptList = []
        self.timeDelay = 5000
        self.x = []
        self.y = []
        self.manx = []
        self.many = []
        self.plotSensorNum = 0
        self.plotMeasGroup = 0
        self.plotMeasurement = 0
        
        self.rm = pyvisa.ResourceManager()
        self.instrument = False #= Resource #self.rm.open_resource("ASRL3::INSTR")
        self.measExp = Experiment() 
        self.measExpSensorCursor = 0
        self.measExpMeasGroupCursor = 0
        self.measExpMeasurementCursor = 0
        self.measData = {}

        self.measSensorNum = 1

        self.canvas = MplCanvas(self, width=9, height=5, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.update_plot()

        #
        tabwidget = QTabWidget(self)

        ###########################################################################################
        # Connection tab
        ###########################################################################################
        connection = QWidget(self)
        lConnection = QGridLayout(self)
        connection.setLayout(lConnection)

        self.FindButton = QPushButton("Find devices", self)
        self.FindButton.clicked.connect(self.FindButtonUpdate)

        self.ConnectButton = QPushButton("Connect", self)
        self.ConnectButton.clicked.connect(self.ConnectButtonUpdate)

        lDevices = QLabel("Active devices", self)

        self.listDevices = QListWidget(self)
        self.listDevices.clicked.connect(self.ListSelectedItem)

        lConnection.setAlignment(Qt.AlignmentFlag.AlignTop)
        lConnection.setColumnMinimumWidth(50,45)
        lConnection.setRowMinimumHeight(52,30)
        lConnection.addWidget(lDevices, 0,0,1,2)
        lConnection.addWidget(self.FindButton, 1,4,1,2)
        lConnection.addWidget(QLabel(" "), 1,6,1,1)
        lConnection.addWidget(self.ConnectButton, 2,4,1,2)
        lConnection.addWidget(self.listDevices, 1,0,15,3)

        ###########################################################################################
        # Measurement tab
        ###########################################################################################
        measurement = QWidget(self)
        measuringLayout = QGridLayout(self)
        measurement.setLayout(measuringLayout)
        measuringLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.PrimaryM = QComboBox(self)
        self.PrimaryM.addItem("AUTO")
        self.PrimaryM.addItem("C")
        self.PrimaryM.addItem("R")
        self.PrimaryM.addItem("L")
        self.PrimaryM.addItem("Z")
        self.PrimaryM.addItem("ECAP")
        self.PrimaryM.addItem("DCR")
        self.PrimaryM.currentIndexChanged.connect(self.MeasFunc)

        self.SecondaryM = QComboBox(self)
        self.SecondaryM.addItem("Q")
        self.SecondaryM.addItem("Theta")
        self.SecondaryM.addItem("ESR")
        self.SecondaryM.addItem("X")
        self.SecondaryM.addItem("D")
        self.SecondaryM.currentIndexChanged.connect(self.MeasFuncSec)

        self.Frequency = QComboBox(self)
        self.Frequency.addItem("100")
        self.Frequency.addItem("120")
        self.Frequency.addItem("200")
        self.Frequency.addItem("400")
        self.Frequency.addItem("800")
        self.Frequency.addItem("1000")
        self.Frequency.addItem("2000")
        self.Frequency.addItem("4000")
        self.Frequency.addItem("8000")
        self.Frequency.addItem("10000")
        #self.Frequency.addItem("20000")
        self.Frequency.currentIndexChanged.connect(self.MeasFreq)
        
        self.Voltage = QComboBox(self)

        self.Bias = QComboBox(self)
        self.Bias.addItem("0")
        self.Bias.addItem("5")
        self.Bias.addItem("10")
        self.Bias.addItem("25")
        self.Bias.addItem("50")
        self.Bias.addItem("75")
        self.Bias.addItem("100")
        self.Bias.addItem("250")
        self.Bias.addItem("500")
        self.Bias.addItem("750")
        self.Bias.addItem("1000")
        self.Bias.addItem("1250")
        self.Bias.addItem("1500")
        self.Bias.currentIndexChanged.connect(self.MeasBiasVolt)

        self.Speed = QComboBox(self)
        self.Speed.addItem("Slow")
        self.Speed.addItem("Medium")
        self.Speed.addItem("Fast")
        self.Speed.currentIndexChanged.connect(self.MeasSpeed)

        measuringLayout.addWidget(QLabel("LCR Meter"), 0,0,1,1)
        measuringLayout.addWidget(QLabel("EL4401"), 1,0,1,1)
        measuringLayout.addWidget(QLabel(""), 2,2,1,9)
        measuringLayout.addWidget(QLabel("Primary:"), 2,0,1,1)
        measuringLayout.addWidget(QLabel("Secondary:"), 3,0,1,1)
        measuringLayout.addWidget(QLabel("Frequency:"), 4,0,1,1)
        measuringLayout.addWidget(self.PrimaryM, 2,1,1,1)
        measuringLayout.addWidget(self.SecondaryM, 3,1,1,1)
        measuringLayout.addWidget(self.Frequency, 4,1,1,1)
        measuringLayout.addWidget(QLabel("Voltage:"), 2,2,1,1)
        measuringLayout.addWidget(QLabel("Range:"), 3,2,1,1)
        measuringLayout.addWidget(QLabel("Speed:"), 4,2,1,1)
        measuringLayout.addWidget(self.Voltage, 2,3,1,1)
        #measuringLayout.addWidget(self.SecondaryM, 3,3,1,1)
        measuringLayout.addWidget(self.Speed, 4,3,1,1)
        measuringLayout.addWidget(QLabel("Bias:"), 2,4,1,1)
        measuringLayout.addWidget(QLabel("Campare:"), 3,4,1,1)
        measuringLayout.addWidget(QLabel("List:"), 4,4,1,1)
        measuringLayout.addWidget(self.Bias, 2,5,1,1)

        ExperimentParams = QWidget(self)
        MulParamLayout = QGridLayout(self)
        ExperimentParams.setLayout(MulParamLayout)

        self.AddMButton = QPushButton("Add Measurement", self)
        self.AddMButton.clicked.connect(self.AddMeas)
        self.RemMButton = QPushButton("Remove Measurement", self)

        self.AddMGButton = QPushButton("Add MeasureGroup", self)
        self.AddMGButton.clicked.connect(self.AddMeasGrop)
        self.RemMGButton = QPushButton("Remove MeasureGroup", self)
        
        self.AddSButton = QPushButton("Add Sensor", self)
        self.AddSButton.clicked.connect(self.AddSensor)
        self.RemSButton = QPushButton("Remove Sensor", self)
        self.RemSButton.clicked.connect(self.removeSensor)

        self.saveButton = QPushButton("Save script", self)
        self.saveButton.clicked.connect(self.saveScript)

        self.EdLineName = QLineEdit(self)
        self.EdLineCall = QLineEdit(self)
        self.EdLineCheck = QLineEdit(self)
        self.EdLineFetch = QLineEdit(self)

        self.EdLineMGName = QLineEdit(self)
        self.EdLineMGCall = QLineEdit(self)
        self.EdLineMGCheck = QLineEdit(self)

        self.EdLineSNunber = QLineEdit(self)
        self.EdLineSName = QLineEdit(self)

        MulParamLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        MulParamLayout.addWidget(QLabel("Name"), 0,0,1,1)
        MulParamLayout.addWidget(QLabel("Call"), 0,1,1,1)
        MulParamLayout.addWidget(QLabel("Check"), 0,2,1,1)
        MulParamLayout.addWidget(QLabel("Fetch"), 0,3,1,1)
        MulParamLayout.addWidget(QLabel("Fetch"), 0,3,1,1)
        MulParamLayout.addWidget(self.EdLineName , 1,0,1,1)
        MulParamLayout.addWidget(self.EdLineCall , 1,1,1,1)
        MulParamLayout.addWidget(self.EdLineCheck, 1,2,1,1)
        MulParamLayout.addWidget(self.EdLineFetch, 1,3,1,1)
        MulParamLayout.addWidget(self.AddMButton, 2,0,1,1)
        MulParamLayout.addWidget(self.RemMButton, 2,1,1,1)

        MulParamLayout.addWidget(QLabel("Name"), 3,0,1,1)
        MulParamLayout.addWidget(QLabel("Call"), 3,1,1,1)
        MulParamLayout.addWidget(QLabel("Check"), 3,2,1,1)
        MulParamLayout.addWidget(QLabel(" "), 3,3,1,1)
        MulParamLayout.addWidget(self.EdLineMGName , 4,0,1,1)
        MulParamLayout.addWidget(self.EdLineMGCall , 4,1,1,1)
        MulParamLayout.addWidget(self.EdLineMGCheck, 4,2,1,1)
        MulParamLayout.addWidget(self.AddMGButton, 5,0,1,1)
        MulParamLayout.addWidget(self.RemMGButton, 5,1,1,1)
        
        MulParamLayout.addWidget(QLabel("Number"), 6,0,1,1)
        MulParamLayout.addWidget(QLabel("Name"), 6,1,1,1)
        MulParamLayout.addWidget(self.EdLineSNunber , 7,0,1,1)
        MulParamLayout.addWidget(self.EdLineSName , 7,1,1,1)
        MulParamLayout.addWidget(self.AddSButton, 8,0,1,1)
        MulParamLayout.addWidget(self.RemSButton, 8,1,1,1)

        MulParamLayout.addWidget(self.saveButton, 9,0,1,1)
        #MulParamLayout.addWidget(self.readButton, 9,1,1,1)
        MulParamLayout.addWidget(QLabel(""), 10,0,5,9)
        
        #self.StartButton.clicked.connect(self.StartButtonUpdate)
        
        plotterRun = QWidget(self)
        plotterRunLay = QGridLayout(self)
        plotterRun.setLayout(plotterRunLay)

        self.StartButton = QPushButton("Run", self)
        self.StartButton.clicked.connect(self.StartButtonUpdate)

        self.PPauseButton = QPushButton("Pause Plot", self)
        self.PPauseButton.clicked.connect(self.PPButtonUpdate)

        self.ClearButton = QPushButton("Clear", self)
        self.ClearButton.clicked.connect(self.ClearPlot)

        self.SaveButton = QPushButton("Save", self)
        self.SaveButton.clicked.connect(self.saveCSV)

        self.LabelTime = QLineEdit(self)
        self.LabelTime.setText(str(float(self.timeDelay)/1000))
        self.LabelTime.editingFinished.connect(self.measTimeLabelUpdate)
        self.LabelFile = QLineEdit(self)
        self.LabelFile.setText("Experiment_"+str(date.today())+"_"+self.now.strftime("%H-%M-%S")+".csv")

        plotterRunLay.setColumnMinimumWidth(50,40)
        plotterRunLay.setRowMinimumHeight(50,30)
        
        plotterRunLay.setAlignment(Qt.AlignmentFlag.AlignTop)
        plotterRunLay.addWidget(self.StartButton, 0,0,1,1)
        plotterRunLay.addWidget(self.PPauseButton, 0,1,1,1)
        plotterRunLay.addWidget(self.ClearButton, 0,2,1,1)
        plotterRunLay.addWidget(self.SaveButton, 0,3,1,1)
        plotterRunLay.addWidget(QLabel("Time delta(S):"), 1,0,1,1)
        plotterRunLay.addWidget(self.LabelTime, 1,1,1,3)
        plotterRunLay.addWidget(QLabel("File Name:"), 2,0,1,1)
        plotterRunLay.addWidget(self.LabelFile, 2,1,1,3)

        plotterRunLay.addWidget(self.toolbar, 1,4,2,35)
        plotterRunLay.addWidget(self.canvas, 3,0,55,55)

        self.expCanvas = MplCanvas(self, width=9, height=5, dpi=100)
        self.expToolbar = NavigationToolbar(self.expCanvas, self)

        #self.scriptFile = QLineEdit(self)
        #self.scriptFile.setText("")

        self.readButton = QPushButton("Read script", self)
        self.readButton.clicked.connect(self.readExperiment)

        self.saveResButton = QPushButton("Save result", self)
        self.saveResButton.clicked.connect(self.writeToXCEL)
        self.excelFile = QLineEdit(self)
        self.excelFile.setText("Experiment_"+str(date.today())+"_"+self.now.strftime("%H-%M-%S"))

        self.BurstButton = QPushButton("Measure", self)
        self.BurstButton.clicked.connect(self.measManually)
        self.BurstButton.setFixedHeight(54)

        self.sensorAmount = QLabel("Sensors: "+str(len(self.measExp.experiment)))
        self.sensorNumber = QLabel("Sensor:  "+str((self.measSensorNum)))
        self.sensorName   = QLabel("Name:    "+str(" - "))
        self.incSensNum = QPushButton("Next", self)
        self.incSensNum.clicked.connect(self.incNum)
        self.decSensNum = QPushButton("Prev", self)
        self.decSensNum.clicked.connect(self.decNum)
        self.clearLastMeas = QPushButton("Clear last", self)
        #self.clearLastMeas.clicked.connect(self.clearMeas)

        self.cbOpenScript = QComboBox(self)
        self.cbSensor = QComboBox(self)
        self.cbMeasGroup = QComboBox(self)
        self.cbMeasure = QComboBox(self)

        self.cbOpenScript.currentIndexChanged.connect(self.selectFile)
        self.cbSensor.currentIndexChanged.connect(self.buildCbMeasGroup)
        self.cbMeasGroup.currentIndexChanged.connect(self.buildCbMeasurement)
        self.cbMeasure.currentIndexChanged.connect(self.buildPlot)

        experimentRun = QWidget(self)
        experimentRunLay = QGridLayout(self)
        experimentRun.setLayout(experimentRunLay)

        experimentRunLay.addWidget(QLabel("Script name"), 0,0,1,1)
        experimentRunLay.addWidget(self.cbOpenScript, 0,1,1,3)
        experimentRunLay.addWidget(self.readButton, 0,4,1,1)
        experimentRunLay.addWidget(self.BurstButton, 0,5,2,2)
        experimentRunLay.addWidget(QLabel("File name"), 1,0,1,1)
        experimentRunLay.addWidget(self.excelFile, 1,1,1,3)
        experimentRunLay.addWidget(self.saveResButton, 1,4,1,1)
        experimentRunLay.addWidget(self.sensorAmount, 2,0,1,1)
        experimentRunLay.addWidget(self.sensorNumber, 2,1,1,1)
        experimentRunLay.addWidget(self.sensorName, 2,2,1,1)
        experimentRunLay.addWidget(self.incSensNum, 3,0,1,1)
        experimentRunLay.addWidget(self.decSensNum, 3,1,1,1)
        experimentRunLay.addWidget(self.clearLastMeas, 3,2,1,1)
        experimentRunLay.addWidget(self.cbSensor, 3,3,1,1)
        experimentRunLay.addWidget(self.cbMeasGroup, 3,4,1,1)
        experimentRunLay.addWidget(self.cbMeasure, 3,5,1,1)

        experimentRunLay.addWidget(self.expToolbar, 0,9,2,40)
        experimentRunLay.addWidget(self.expCanvas, 4,0,55,55)

        tabwidget.addTab(connection, "Connection")
        tabwidget.addTab(measurement, "Device parameters")
        tabwidget.addTab(ExperimentParams, "Edit script")
        tabwidget.addTab(plotterRun, "Plotter")
        tabwidget.addTab(experimentRun, "Experiment")

        self.scriptList = os.listdir("./Scripts")
        for i in self.scriptList:
            self.cbOpenScript.addItem(i)
       
        self.show()

        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QTimer()
        self.timer.setInterval(self.timeDelay)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()
    
    def writeToXCEL(self):
        name = self.excelFile.text()
        row = 0
        column = 0
        if name == "":
            name = "experiment_" +str(date.today())+"_"+self.now.strftime("%H:%M:%S")
        name = (name.split('.'))[0]
        #a = open(name+'.xlsx', 'r') 
        #if(a == 1):
        #    a.close()
        #    name += '1'
        workbook = xlsxwriter.Workbook("./Results/"+name+'.xlsx')
        worksheet = workbook.add_worksheet()
        for i in self.measExp.experiment:
            row = 0
            worksheet.write(row, column, i.name)
            column += 1
            for j in i.sensor:
                for k in j.measurements:
                    row = 1
                    worksheet.write(row, column, j.name +" "+ k.name)
                    for l in k.data:
                        row += 1
                        worksheet.write(row, column, l)
                    column += 1
        workbook.close()

        print(name)

    def selectFile(self):
        if(len(self.scriptList) == 0):
            return
        #self.openScriptFile = self.scriptList[(self.cbOpenScript.currentIndex() -1)]
        self.openScriptFile = self.scriptList[(self.cbOpenScript.currentIndex())]
        print(self.openScriptFile)

    def buildCbSensors(self):
        self.plotMeasGroup = 0
        self.plotSensorNum = 0
        self.plotMeasurement=0
        self.cbSensor.clear()
        for i in self.measExp.experiment:
            self.cbSensor.addItem(i.name)

    def buildCbMeasGroup(self):
        self.plotSensorNum = self.cbSensor.currentIndex() + 1
        self.plotMeasGroup = 0
        self.plotMeasurement=0
        self.cbMeasGroup.clear()
        for i in self.measExp.experiment[self.plotSensorNum - 1].sensor:
            self.cbMeasGroup.addItem(i.name)

    def buildCbMeasurement(self):
        self.plotMeasGroup = self.cbMeasGroup.currentIndex() + 1
        self.plotMeasurement=0
        self.cbMeasure.clear()
        for i in self.measExp.experiment[self.plotSensorNum - 1].sensor[self.plotMeasGroup-1].measurements:
            self.cbMeasure.addItem(i.name)

    def buildPlot(self):
        self.plotMeasurement = self.cbMeasure.currentIndex() + 1
        #print("Ok")
        self.buildManual()

    def buildManual(self):
        if(self.plotMeasGroup == 0 | self.plotMeasurement == 0 | self.plotSensorNum == 0):
            return
        if(len(self.measExp.experiment[self.plotSensorNum-1].sensor[self.plotMeasGroup-1].measurements[self.plotMeasurement-1].data) == 0):
            return
        self.many = self.measExp.experiment[self.plotSensorNum-1].sensor[self.plotMeasGroup-1].measurements[self.plotMeasurement-1].data
        self.manx.clear()
        for i in range(len(self.measExp.experiment[self.plotSensorNum-1].sensor[self.plotMeasGroup-1].measurements[self.plotMeasurement-1].data)):
            self.manx.append(i)
        #print("here")   
        self.expCanvas.axes.cla()
        self.expCanvas.axes.plot(self.manx, self.many, 'm')
        self.expCanvas.draw()
        #print("here")

    def saveScript(self):
        name = "defaultScript"
        fl = open(name+".exp", "w")
        #fl.write()
        for i in self.measExp.experiment:
            fl.write(str(i.number)+"|"+str(i.name)+"\n")
            for j in i.sensor:
                fl.write("\t"+str(j.name)+"|"+str(j.call)+"|"+str(j.check)+"\n")
                for k in j.measurements:
                    fl.write("\t"+"\t"+str(k.name)+"|"+str(k.call)+"|"+str(k.check)+"|"+str(k.fetch)+"\n") 
        fl.close()

    def incNum(self):
        self.measSensorNum += 1
        if (self.measSensorNum > len(self.measExp.experiment)):
            self.measSensorNum = 1
        self.sensorNumber.setText("Sensor:  "+str(self.measSensorNum))
        self.sensorAmount.setText("Sensors: "+str(len(self.measExp.experiment)))
        self.sensorName.setText("Name: "+str(self.measExp.experiment[self.measSensorNum-1].name))

    def decNum(self):
        self.measSensorNum -= 1
        if (self.measSensorNum == 0):
            self.measSensorNum = len(self.measExp.experiment)
        self.sensorNumber.setText("Sensor:  "+str(self.measSensorNum))
        self.sensorAmount.setText("Sensors: "+str(len(self.measExp.experiment)))
        self.sensorName.setText("Name: "+str(self.measExp.experiment[self.measSensorNum-1].name))

    def readExperiment(self):
        self.measExp.experiment.clear()
        self.measExpSensorCursor = 0
        self.measExpMeasGroupCursor = 0
        self.measExpMeasurementCursor = 0
        fin = open("./Scripts/" + self.openScriptFile, "r")
        while 1:
            textLine=""
            textLine = fin.readline()
            #print(textLine, " | ", len(textLine))
            if(len(textLine) == 0):
                break
            wordList = textLine.split('|')
            #print(wordList, " | ", len(wordList))
            if(wordList[0][0] == "\t"):
                if(wordList[0][1] == "\t"):
                    #print("Measurement")
                    self.measExp.experiment[self.measExpSensorCursor-1].sensor[self.measExpMeasGroupCursor-1].addMeasurement(Measurement(wordList[0].replace("\t",""), wordList[1], wordList[2], wordList[3].replace("\n","")))
                else:
                    #print("Measurement Group")
                    self.measExp.experiment[self.measExpSensorCursor-1].addMeasureGroup(MasurementGroupe(wordList[0].replace("\t",""), wordList[1], wordList[2].replace("\n","")))
                    self.measExpMeasGroupCursor += 1
                    self.measExpMeasurementCursor = 0
            else:
                self.measExp.addSensor(Sensor(wordList[0], wordList[1].replace("\n","")))
                self.measExpSensorCursor += 1
                self.measExpMeasGroupCursor = 0
                self.measExpMeasurementCursor = 0

            #print(wordList)

        fin.close()
        self.buildCbSensors()
        self.sensorAmount.setText("Sensors: "+str(len(self.measExp.experiment)))
        self.sensorName.setText("Name: "+str(self.measExp.experiment[self.measSensorNum-1].name))
        print("Sensors : ", self.measExpSensorCursor)

    def AddMeasGrop(self):
        name = self.EdLineMGName.text()
        call = self.EdLineMGCall.text()
        check= self.EdLineMGCheck.text()

        if(len(self.measExp.experiment) == 0):
            return
        self.measExp.experiment[self.measExpSensorCursor-1].addMeasureGroup(MasurementGroupe(name, call, check))
        self.measExpMeasGroupCursor += 1
        self.measExpMeasurementCursor = 0
        print("Mearurement group is added")

    def AddSensor(self):
        number = self.EdLineSNunber.text()
        name = self.EdLineSName.text()
        self.measExpSensorCursor += 1
        self.measExpMeasGroupCursor = 0
        self.measExpMeasurementCursor = 0

        self.measExp.addSensor(Sensor(number, name))
        print("Sensor is added")
    
    def removeSensor(self):
        self.measExp.removeSensor(self.measExpSensorCursor)
        if(self.measExpSensorCursor > (len(self.measExp.experiment) - 1)):
            self.measExpSensorCursor = (len(self.measExp.experiment) - 1)
            print("Sensor removed")


    def AddMeas(self):
        l = len(self.measExp.experiment)
        if(l == 0): 
            return
        name = self.EdLineName.text()
        call = self.EdLineCall.text()
        check= self.EdLineCheck.text()
        fetch= self.EdLineFetch.text()
        show = True#self.RadButShowExp.toggled()

        if(len(self.measExp.experiment) == 0):
            return
        if(len(self.measExp.experiment[self.measExpSensorCursor-1].sensor) == 0):
            return
        self.measExp.experiment[self.measExpSensorCursor-1].sensor[self.measExpMeasGroupCursor-1].addMeasurement(Measurement(name, call, fetch, check, delay = 400, show = show))
        #self.measExp.experiment[l-1].addMeasurement(Measurement(name, call, fetch, check, delay = 400, show = show))
        print("Mearurement is added")

    def StartButtonUpdate(self):
        if(self.connected == False): return

        self.running = ~self.running
        if(self.running):
            self.StartButton.setText("Pause")
        else:
            self.StartButton.setText("Run")

    def MeasFunc(self):
        text = self.PrimaryM.currentText()
        a = self.instrument.query(":FUNC:IMP:A " + text)
        print(a)

    def MeasFuncSec(self):
        text = self.SecondaryM.currentText()
        a = self.instrument.query(":FUNC:IMP:B " + text)
        print(a)

    def MeasFreq(self):
        text = self.Frequency.currentText()
        a = self.instrument.query(":FREQ "+text)
        print(a)

    def MeasBiasVolt(self):
        text = self.Bias.currentText()
        a = self.instrument.query(":BIAS:VOLT:LEV "+text)
        print(a)

    def measTimeLabelUpdate(self):
        self.timeDelay = int(float(self.LabelTime.text())*1000)
        self.timer.setInterval(self.timeDelay)

    def MeasSpeed(self):
        text = self.Speed.currentText()
        if(text == "Fast"):
            a = self.instrument.query(":APER FAST")
        elif(text == "Medium"):
            a = self.instrument.query(":APER MEDium")
        elif(text == "Slow"):
            a = self.instrument.query(":APER SLOW")
        print(a)

    def measureBurst(self):
        00000000000000000000000000000000
        measLine = []
        self.instrument.query(":FUNC:IMP:A C")
        self.instrument.query(":FREQ 200")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        self.instrument.query(":FREQ 1000")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        self.instrument.query(":FREQ 10000")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        time.sleep(800/1000)

        self.instrument.query(":FUNC:IMP:A R")
        self.instrument.query(":FREQ 200")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        self.instrument.query(":FREQ 1000")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        self.instrument.query(":FREQ 10000")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        time.sleep(800/1000)

        self.instrument.query(":FUNC:IMP:A Z")
        self.instrument.query(":FREQ 200")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        self.instrument.query(":FREQ 1000")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        self.instrument.query(":FREQ 10000")
        time.sleep(800/1000)
        b = self.instrument.query_ascii_values("FETC?")
        measLine.append(str(b[0]).replace('.',','))
        time.sleep(800/1000)

        print(measLine[0], measLine[1], measLine[2], measLine[3], measLine[4], measLine[5], measLine[6], measLine[7], measLine[8])
    
    def measManually(self):
        measLine = []

        i = self.measExp.experiment[self.measSensorNum-1]
        for j in i.sensor:
            self.instrument.query(j.call)  #(":FUNC:IMP:A C")
            for k in j.measurements :
                self.instrument.query(k.call)
                time.sleep(800/1000)
                b = self.instrument.query_ascii_values(k.fetch)
                k.insertData(b[0])
                measLine.append(str(b[0]).replace('.',',')+" ")

        stringOut = ""
        for i in measLine:
            stringOut += i

        print(stringOut)
        self.measSensorNum += 1
        if (self.measSensorNum > len(self.measExp.experiment)):
            self.measSensorNum = 1
        self.sensorNumber.setText("Sensor:  "+str(self.measSensorNum))
        self.sensorAmount.setText("Sensors: "+str(len(self.measExp.experiment)))
        self.sensorName.setText("Name: "+str(self.measExp.experiment[self.measSensorNum-1].name))
        self.buildManual()

    def measManuallyPlug(self):
        measLine = []

        i = self.measExp.experiment[self.measSensorNum-1]
        for j in i.sensor:
            #self.instrument.query(j.call)  #(":FUNC:IMP:A C")
            for k in j.measurements :
                #self.instrument.query(k.call)
                #time.sleep(800/1000)
                #b = self.instrument.query_ascii_values(k.fetch)
                a = random.random()
                k.insertData(a)
                measLine.append(str(a).replace('.',',')+" ")

        stringOut = ""
        for i in measLine:
            stringOut += i

        print(stringOut)
        self.measSensorNum += 1
        if (self.measSensorNum > len(self.measExp.experiment)):
            self.measSensorNum = 1
        self.sensorNumber.setText("Sensor:  "+str(self.measSensorNum))
        self.sensorAmount.setText("Sensors: "+str(len(self.measExp.experiment)))
        self.sensorName.setText("Name: "+str(self.measExp.experiment[self.measSensorNum-1].name))
        self.buildManual()

    def saveCSV(self):
        print("OK")

    def ListSelectedItem(self):
        a = self.listDevices.currentItem()

    def ConnectButtonUpdate(self):
        if(self.listDevices.currentItem() == None):
            return
        self.connectDevise = self.listDevices.currentItem().text()
        self.instrument = self.rm.open_resource(self.listDevices.currentItem().text())
        print(self.instrument.query("*IDN?"))
        print(self.connectDevise)

    def FindButtonUpdate(self):
        self.connected = True
        self.rm.list_resources()
        slrl = self.rm.list_resources()
        self.deviceList.clear()
        self.listDevices.clear()

        if(len(slrl) == 0):
            print("Device not fount")
            self.deviceList.append("COM3:1LCR:INST")
            self.deviceList.append("COM2:2LCR:INST")
            self.deviceList.append("COM5:6LCR:INST")
        else: 
            print("The next devices are founded")
            for i in slrl:
                self.deviceList.append(i)

        it = 0
        for i in self.deviceList:
            self.listDevices.insertItem(it, i)
            it += 1
        print(self.rm)
        print(self.deviceList)

    def ClearPlot(self):
        self.x.clear()
        self.y.clear()
        self.canvas.axes.cla()
        self.canvas.draw()

    def PPButtonUpdate(self):
        self.PPause = ~self.PPause
        if(self.PPause):
            self.PPauseButton.setText("Run Plot")
        else:
            self.PPauseButton.setText("Pause Plot")

    def update_plot(self):
        # Drop off the first y element, append a new one.
        if(self.running == False): return
    
        #self.y.append(random.random())
        for i in self.measExp.experiment:
            if(i.name not in self.measData): self.measData.update({i.name:{}})
            if len(self.measExp.experiment) > 1:
                a = self.instrument.query(i.call)
            for j in i.measurements:
                if( j.name not in self.measData[i.name]):
                    print(j.name)
                    self.measData[i.name].update({j.name:[]})
                print(j)
                a = self.instrument.query(j.call)
                print(j.call)
                time.sleep(500/1000)
                b = self.instrument.query_ascii_values(j.fetch)
                time.sleep(500/1000)
                print(j.fetch)
                print("Data = ", b)
                
                self.measData[i.name][j.name].append(b[0])

        if(len(self.x) == 0):
            self.x.append(0)
        else:
            self.x.append(self.x[len(self.x)-1]+self.timeDelay/1000)

        if(self.PPause): return

        self.xdata = self.x
        self.ydata = self.y
        self.ydata = self.ydata
        self.canvas.axes.cla()  # Clear the canvas.
        
        for i in self.measData:
            for j in self.measData[i]:
                self.canvas.axes.plot(self.x, self.measData[i][j], 'm')

        self.canvas.axes.xaxis.label.set_text("S")
        self.canvas.axes.yaxis.label.set_text("Capacitance, F")
        #self.toolbar = NavigationToolbar(self.canvas, self)
        # Trigger the canvas to update and redraw.
        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())