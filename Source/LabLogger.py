import sys
from   datetime import date, time
import numpy as np
import pyvisa
import time
import random
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt6.QtWidgets import QMainWindow, QComboBox, QRadioButton, QLabel, QButtonGroup, QApplication, QWidget, QListWidget, QFormLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import QTimer,Qt

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
    def __init__(self, name = "", call = "", fetch = "", check = "", delay = 100, show = False):
        self.name = name
        self.call = call
        self.fetch = fetch
        self.check = check
        self.delay = delay
        self.show = show

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

class Experiment():
    def __init__(self):
        self.experiment = []

    def addMeasureGroup(self, MeasureGroupe):
        self.experiment.append(MeasureGroupe)

class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setMinimumSize(900, 660)
        self.setMaximumSize(900, 660)    
        self.setWindowTitle("LabLogger")

        # local variables
        self.running = False
        self.connected = False
        self.PPause = False
        self.deviceList = []
        self.connectDevise = ""
        self.timeDelay = 5000
        self.x = []
        self.y = []
        
        self.rm = pyvisa.ResourceManager()
        self.instrument = False #= Resource #self.rm.open_resource("ASRL3::INSTR")
        self.measExp = Experiment() 
        self.measData = {}

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
        
        self.EdLineName = QLineEdit(self)
        self.EdLineCall = QLineEdit(self)
        self.EdLineCheck = QLineEdit(self)
        self.EdLineFetch = QLineEdit(self)

        self.EdLineMGName = QLineEdit(self)
        self.EdLineMGCall = QLineEdit(self)
        self.EdLineMGCheck = QLineEdit(self)

        self.RadButShowExp = QRadioButton(self)
        
        MulParamLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        MulParamLayout.addWidget(self.AddMButton, 0,0,1,1)
        MulParamLayout.addWidget(self.RemMButton, 0,1,1,1)
        MulParamLayout.addWidget(QLabel("Name"), 1,0,1,1)
        MulParamLayout.addWidget(QLabel("Call"), 1,1,1,1)
        MulParamLayout.addWidget(QLabel("Check"), 1,2,1,1)
        MulParamLayout.addWidget(QLabel("Fetch"), 1,3,1,1)
        MulParamLayout.addWidget(QLabel("Plot"), 1,4,1,1)
        MulParamLayout.addWidget(self.EdLineName , 2,0,1,1)
        MulParamLayout.addWidget(self.EdLineCall , 2,1,1,1)
        MulParamLayout.addWidget(self.EdLineCheck, 2,2,1,1)
        MulParamLayout.addWidget(self.EdLineFetch, 2,3,1,1)
        MulParamLayout.addWidget(self.RadButShowExp, 2,4,1,1)
        MulParamLayout.addWidget(self.AddMGButton, 3,0,1,1)
        MulParamLayout.addWidget(self.RemMGButton, 3,1,1,1)
        MulParamLayout.addWidget(QLabel("Name"), 4,0,1,1)
        MulParamLayout.addWidget(QLabel("Call"), 4,1,1,1)
        MulParamLayout.addWidget(QLabel("Check"), 4,2,1,1)
        MulParamLayout.addWidget(QLabel(" "), 4,3,1,1)
        MulParamLayout.addWidget(self.EdLineMGName , 5,0,1,1)
        MulParamLayout.addWidget(self.EdLineMGCall , 5,1,1,1)
        MulParamLayout.addWidget(self.EdLineMGCheck, 5,2,1,1)
        MulParamLayout.addWidget(QLabel(""), 6,0,5,9)
        
        #self.StartButton.clicked.connect(self.StartButtonUpdate)
        
        experimentRun = QWidget(self)
        experimentRunLay = QGridLayout(self)
        experimentRun.setLayout(experimentRunLay)

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
        self.LabelFile.setText("Experiment_"+str(date.today())+".csv")

        experimentRunLay.setColumnMinimumWidth(50,40)
        experimentRunLay.setRowMinimumHeight(50,30)
        
        experimentRunLay.setAlignment(Qt.AlignmentFlag.AlignTop)
        experimentRunLay.addWidget(self.StartButton, 0,0,1,1)
        experimentRunLay.addWidget(self.PPauseButton, 0,1,1,1)
        experimentRunLay.addWidget(self.ClearButton, 0,2,1,1)
        experimentRunLay.addWidget(self.SaveButton, 0,3,1,1)
        experimentRunLay.addWidget(QLabel("Time delta(S):"), 1,0,1,1)
        experimentRunLay.addWidget(self.LabelTime, 1,1,1,3)
        experimentRunLay.addWidget(QLabel("File Name:"), 2,0,1,1)
        experimentRunLay.addWidget(self.LabelFile, 2,1,1,3)

        experimentRunLay.addWidget(self.toolbar, 0,4,2,30)
        experimentRunLay.addWidget(self.canvas, 3,0,55,55)

        testFrequency = QWidget(self)
        FrequencyLayout = QGridLayout(self)
        testFrequency.setLayout(FrequencyLayout)

        tabwidget.addTab(connection, "Connection")
        tabwidget.addTab(measurement, "Measurement")
        tabwidget.addTab(ExperimentParams, "Experiment settings")
        tabwidget.addTab(experimentRun, "Experiment")
        tabwidget.addTab(testFrequency, "Frequency")
       
        self.show()

        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QTimer()
        self.timer.setInterval(self.timeDelay)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def AddMeasGrop(self):
        name = self.EdLineMGName.text()
        call = self.EdLineMGCall.text()
        check= self.EdLineMGCheck.text()

        self.measExp.addMeasureGroup(MasurementGroupe(name, call, check))

    def AddMeas(self):
        l = len(self.measExp.experiment)
        if(l == 0): 
            return
        name = self.EdLineName.text()
        call = self.EdLineCall.text()
        check= self.EdLineCheck.text()
        fetch= self.EdLineFetch.text()
        show = True#self.RadButShowExp.toggled()

        self.measExp.experiment[l-1].addMeasurement(Measurement(name, call, fetch, check, delay = 400, show = show))

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