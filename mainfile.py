# -*- coding: utf-8 -*-

#
# Created by: Brian Mason
# This is a template for building cal stations using PyQt5 GUI
# It opens a main window with a progress window and buttons to initiate tests (or whatever)
# Some examples show how to have a pop-up instruction window, a data input window, and a plot window
#

import sys
from typing import List, Union

from PyQt5.QtCore import Qt, QRect, QMetaObject, QCoreApplication
from PyQt5.QtGui import QFont, QPixmap, QFontMetrics
from PyQt5.QtWidgets import *
from PyQt5 import QtPrintSupport
import serial
import pyvisa
#import visa
import time
import numpy as np
from constants import *
from DUT_tests import *
from interfacesnew import *
import settings
from multiprocessing import Process, freeze_support # this, and the call to 'freeze_support' below, are important for pyinstaller to work
from pathlib import Path
import os
import wip_api
import json
from operator import itemgetter
import random
#import DUT_tests
import copy

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# This method connects to WIP Tracker
def client(connection_details):
    client = wip_api.ApiClient(**connection_details)
    client.connect()
    return client


# Set up the main window...
class Ui_MainWindow(QMainWindow):

    connectionList: List[Union[str, List[str]]]

    def __init__(self, parent=None):
        super().__init__()

    def getPixmapFilePath(self, icon):
        dir = Path(__file__).parent
        file = dir / ICON_PIXMAP[icon]
        string = str(file)
        string = string.replace("\\", "/")
        print(string)
        return(string)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(840, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # This 'label' is for displaying text that identifies the project. It can contain whatever you want
        # You can add/change the text below in the 'retranslateUi' method
        self.label = QLabel(self.centralwidget)
        self.label.setGeometry(QRect(20, 20, 400, 50))
        font = QFont()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setObjectName("label")

        # This 'indexstring' is a bit of a misnomer, since it was originally intended to display an index value for a loop
        # but it evolved into a data display window, separate from the progress window.
        self.indexstring = QTextEdit(self.centralwidget)
        self.indexstring.setGeometry(QRect(500, 20, 320, 50))
        self.indexstring.setFontPointSize(11)
        self.indexstring.setObjectName("Index_string")

        # This 'ProgressText' is for displaying results or data.
        self.ProgressText = QTextEdit(self.centralwidget)
        self.ProgressText.setGeometry(QRect(220, 120, 600, 450))
        self.ProgressText.setFontPointSize(10)
        self.ProgressText.setObjectName("ProgressText")

        # button for closing the main window (and everything else)
        self.QuitButton = QPushButton(self.centralwidget)
        self.QuitButton.setGeometry(QRect(20, 530, 100, 40))
        font = QFont()
        font.setPointSize(16)
        self.QuitButton.setFont(font)
        self.QuitButton.setObjectName("QuitButton")
        self.QuitButton.clicked.connect(self.closeAll)

        # The following sets up the button group for tests in a convenient collumn beside the progress window
        self.buttonGroupBox = QGroupBox(self.centralwidget)
        self.buttonGroupBox.setGeometry(QRect(20, 115, 170, 10 + ((1 + len(BUTTON_LIST)) * BUTTON_HEIGHT)))
        self.buttonGroupBox.setObjectName("buttonGroupBox")
        
        self.verticalLayout = QVBoxLayout(self.buttonGroupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.buttonLabelList = []
        self.buttonList = []
        self.horizontalLayoutList = []

        # 'BUTTON_LIST' is defined in 'constants.py'
        # This will add as many buttons as are in the list
        for i in range(len(BUTTON_LIST)):
            self.horizontalLayoutList.append(QHBoxLayout())
            self.horizontalLayoutList[i].setObjectName("horizontalLayout_%d" % i)

            self.buttonLabelList.append(QLabel(self.buttonGroupBox))
            self.buttonLabelList[i].setFrameStyle(QFrame.Box)
            self.buttonLabelList[i].setFixedSize(16,16)
            self.buttonLabelList[i].setText("")
            self.buttonLabelList[i].setPixmap(QPixmap(self.getPixmapFilePath(UNCHECKED)))
            self.buttonLabelList[i].setObjectName("label_%d" % i)
            self.horizontalLayoutList[i].addWidget(self.buttonLabelList[i])

            self.buttonList.append(QPushButton(self.buttonGroupBox))
            #self.buttonList[i].setMinimumWidth(120)
            self.buttonList[i].setFixedSize(130,BUTTON_HEIGHT)
            self.buttonList[i].setObjectName("pushButton_%d" % i)
            string = 'self.on_click_' + BUTTON_LIST[i]['function']
            self.buttonList[i].clicked.connect(eval(string))
            self.horizontalLayoutList[i].addWidget(self.buttonList[i])
            self.verticalLayout.addLayout(self.horizontalLayoutList[i])

        self.btn_grp = QButtonGroup()
        self.btn_grp.setExclusive(True)
        for btn in self.buttonList:
            self.btn_grp.addButton(btn)

        # This creates an instrument group panel with a check-box to indicate whether each instrument was found at initialization time
        self.instrumentGroupBox = QGroupBox(self.centralwidget)
        self.instrumentGroupBox.setGeometry(QRect(20, 350, 130, 10 + (20 * (1 + len(INSTRUMENT_CHKLIST)))))
        self.instrumentGroupBox.setObjectName("instrumentGroupBox")
        self.instVerticalLayout = QVBoxLayout(self.instrumentGroupBox)
        self.instVerticalLayout.setObjectName("verticalLayout")
        self.instrumentCheckBoxList = []
        for i in range(len(INSTRUMENT_CHKLIST)):
            self.instrumentCheckBoxList.append(QCheckBox(self.instrumentGroupBox))
            self.instrumentCheckBoxList[i].setObjectName("checkBox_%d" % i)
            self.instVerticalLayout.addWidget(self.instrumentCheckBoxList[i])

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setGeometry(QRect(0, 0, 1073, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

        # This looks for connected instruments and creates a dictionary of instruments that you specify
        # The template uses HP3458 as an example. You can add instruments by including additional if... sections
        # in the for-loop
        self.connectionList = []
        rm = pyvisa.ResourceManager()
        #rm = visa.ResourceManager()
        resources = rm.list_resources()
        print(str(resources))
        settings.instruments = {}
        for item in resources:
            if 'GPIB0::22::' in item:
                resource = rm.open_resource(item)
                dict = {'HP3458': resource}
                settings.instruments.update(dict)
                try:
                    resource.write("END ALWAYS")
                    resource.write("ID?")
                    qry = resource.read()
                    #print(qry)
                    if qry.find("HP3458A") > -1:
                        self.connectionList.append(INSTRUMENT_CHKLIST[HP3458A])
                except:
                    print("Error: instrument HP3458A not found")

            if 'ASRL19::' in item:
                resource = rm.open_resource(item)
                dict = {'DC205': resource}
                settings.instruments.update(dict)
                try:
                    resource.baud_rate = 115200
                    resource.write("*IDN?")
                    qry = resource.read()
                    #print(qry)
                    if qry.find('DC205') > -1:
                        self.connectionList.append(INSTRUMENT_CHKLIST[DC205])
                except:
                    print("Error: instrument DC205 not found")


            if 'ASRL5::' in item:
                resource = rm.open_resource(item)
                dict = {'CS580': resource}
                settings.instruments.update(dict)
                try:
                    resource.baud_rate = 9600
                    resource.write("*IDN?")
                    qry = resource.read()
                    #print(qry)
                    if qry.find('CS580') > -1:
                        self.connectionList.append(INSTRUMENT_CHKLIST[CS580])
                except:
                    print("Error: instrument CS580 not found")

            #print(self.connectionList)


            if 'GPIB0::6::' in item:
                resource = rm.open_resource(item)
                dict = {'SIM900': resource}
                settings.instruments.update(dict)
                try:
                    resource.write('*IDN?')
                    qry = resource.read()
                    loc = qry.find('SIM900')
                    if loc > -1:
                        settings.snum = copy.copy(qry[loc+10 : loc+16])
                        print('Serial number of DUT is %s' % settings.snum)
                        self.connectionList.append(INSTRUMENT_CHKLIST[SIM900])

                        # Now, open the WIP Tracker client connection
                        # 'CONNECTION_DETAILS' is defined in 'constants.py' and contains the password/URLs for getting to WIP Tracker
                        # Here, we search for an open test session for the DUT. If none exists, and the serial number is in WIP Tracker
                        # a new test session will be opened in WIP Tracker
                        print('Connecting to WIP Tracker...')
                        settings.api_client = client(CONNECTION_DETAILS)
                        wip = settings.api_client
                        try:
                            bp = wip.get_built_part(settings.snum)
                            sessions = wip.search_test_sessions(settings.snum)
                            if len(sessions) > 0:
                                if not sessions[0]['passed']:
                                    settings.wip_session = sessions[0]
                            else:
                                settings.wip_session = wip.create_new_test_session(bp['url'])
                        except:
                            message = "Error: No part found in WIP Tracker with s/n=%s" % settings.snum
                            print(message)
                            self.onProgressUpdate(message, APPEND)
                except:
                    message = 'Error: DUT SIM900 not found'
                    print(message)
                    self.onProgressUpdate(message, APPEND)


        for checkbox in self.instrumentGroupBox.findChildren(QCheckBox):
            for connection in self.connectionList:
                if checkbox.text() == connection:
                    checkbox.setChecked(True)

        allInstrumentsConnected = True
        missingInstruments = []
        for checkbox in self.instrumentGroupBox.findChildren(QCheckBox):
            if not checkbox.isChecked():
                allInstrumentsConnected = False
                missingInstruments.append(checkbox.text())



    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "DC205 Thermal Drift Test \n(@45, 35, 25, 15, 5 DegC)"))
        self.QuitButton.setText(_translate("MainWindow", "Quit"))
        self.instrumentGroupBox.setTitle(_translate("MainWindow", "Instrument Connections"))
        for i in range(len(INSTRUMENT_CHKLIST)):
            self.instrumentCheckBoxList[i].setText(_translate("MainWindow", INSTRUMENT_CHKLIST[i]))
        for i in range(len(BUTTON_LIST)):
            self.buttonGroupBox.setTitle(_translate("MainWindow", "ButtonGroupBox"))
            self.buttonList[i].setText(_translate("MainWindow", BUTTON_LIST[i]['label']))

    # Handle test button tasks...
    # Each test class in 'DUT_tests.py' corresponds to a button in the test group and is instantiated here
    # Here is also where the signals defined in DUT_tests are connected to their slots
    # which are defined below

    def on_click_InstructionExample(self):
        self.test = InstructionExample()
        self.test.test_signal.connect(self.onProgressUpdate)
        self.test.btns_signal.connect(self.onButtonsUpdate)
        self.test.chk_signal.connect(self.onCheckUpdate)
        self.test.msg_signal.connect(self.onMessageUpdate)
        self.test.start()

    def on_click_TextInputExample(self):
        self.test = TextInputExample()
        self.test.test_signal.connect(self.onProgressUpdate)
        self.test.btns_signal.connect(self.onButtonsUpdate)
        self.test.chk_signal.connect(self.onCheckUpdate)
        self.test.txt_signal.connect(self.onTextUpdate)
        self.test.start()

    def on_click_DataPlotExample(self):
        self.test = DataPlotExample()
        self.test.test_signal.connect(self.onProgressUpdate)
        self.test.btns_signal.connect(self.onButtonsUpdate)
        self.test.chk_signal.connect(self.onCheckUpdate)
        self.test.plot_signal.connect(self.onPlotData)
        self.test.start()

    def on_click_DataRecExample(self):
        self.test = DataRecExample()
        self.test.test_signal.connect(self.onProgressUpdate)
        self.test.btns_signal.connect(self.onButtonsUpdate)
        self.test.chk_signal.connect(self.onCheckUpdate)
        self.test.plot_signal.connect(self.onPlotData)
        self.test.start()

    # Handle GUI related functions...

    def onProgressUpdate(self, text='\n', mode='r'):
        if mode == 'r':
            self.ProgressText.setText(text)
        elif mode == 'a':
            self.ProgressText.append(text)
        self.ProgressText.verticalScrollBar().setValue(self.ProgressText.verticalScrollBar().maximum()) # Auto scroll so that new text is always visible

    def onButtonsUpdate(self, bol):
        for i in range(len(self.buttonList)):
            self.buttonList[i].setEnabled(bol)

    def onCheckUpdate(self, btn, icon):
        self.buttonLabelList[btn].setPixmap(QPixmap(self.getPixmapFilePath(icon)))
        settings.history[btn] = icon

    def onMessageUpdate(self, text):
        settings.msg = QMessageBox()
        settings.msg.setText(text)
        settings.msg.setStandardButtons(QMessageBox.Ok)
        settings.msg.exec_()
        if settings.msg.result() == QMessageBox.Ok:
            settings.msg.done(0)

    def onTextUpdate(self, instructions, text, target):
        snum = settings.snum
        settings.txtdial = QInputDialog()
        settings.txtdial.setGeometry(QRect(100, 200, 800, 200))
        settings.txtdial.setWindowModality(True)
        txt, ok = settings.txtdial.getText(self, text, instructions, QLineEdit.Normal, text)

        settings.choice_rslt = False
        if ok and txt != '':
            if target == REFERENCE_SNUM_WRITE:
                num = int(txt)
                settings.refsnum = "%05d" % num
                settings.choice_rslt = True
            elif target == REFERENCE_RETRIEVE_DATA:
                settings.snum = txt
                settings.choice_rslt = True
            elif target == ANALYZE_NOISE:
                settings.snum = txt
                settings.choice_rslt = True

        settings.txtdial.setWindowModality(False)

    def onPlotData(self):
        plot_ui = PlotDialog()
        plot_ui.exec()

    def onCheckDialogUpdate(self):
        settings.dialog = QDialog()
        settings.chckbxui = Checkbox_Dialog()
        settings.chckbxui.setupUi(settings.dialog)
        settings.dialog.exec()

    def onTextUpdate(self, instructions, text, target):
        snum = settings.snum
        settings.txtdial = QInputDialog()
        settings.txtdial.setGeometry(QRect(100, 200, 800, 200))
        settings.txtdial.setWindowModality(True)
        txt, ok = settings.txtdial.getText(self, text, instructions, QLineEdit.Normal, text)

        settings.choice_rslt = False
        if ok and txt != '':
            if target == SERIAL_NUM_WRITE:
                settings.snum = txt
                settings.choice_rslt = True
            # Add additional conditionals here for other specific tasks
            # Just be sure to define a constant in 'constants.py' for the 'target' value
        settings.txtdial.setWindowModality(False)

    def closeAll(self):
        sys.exit(0)

class Checkbox_Dialog(object):

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(142, 210)

        self.checkBox = []
        for i in range(len(settings.choices)):
            self.checkBox.append(QCheckBox(Dialog))
            self.checkBox[i].setGeometry(QRect(30, 54+(i*23), 90, 17))
            self.checkBox[i].setObjectName("checkBox_%d" % i)

        self.pushButton = QPushButton(Dialog)
        self.pushButton.setGeometry(QRect(30, 123, 75, 23))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.setCheckboxes)
        self.pushButton_2 = QPushButton(Dialog)
        self.pushButton_2.setGeometry(QRect(30, 160, 75, 23))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.clicked.connect(Ui_MainWindow.closeCheckDialog)
        self.label = QLabel(Dialog)
        self.label.setGeometry(QRect(30, 10, 71, 31))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setObjectName("label")

        self.retranslateUi(Dialog)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))

        for i in range(len(self.checkBox)):
            self.checkBox[i].setText(_translate("Dialog", settings.choices[i]))

        self.pushButton.setText(_translate("Dialog", "Select all"))
        self.pushButton_2.setText(_translate("Dialog", "Continue"))
        self.label.setText(_translate("Dialog", "Select ranges\nto calibrate"))

    def setCheckboxes(self):
        for i in range(len(settings.choices)):
            self.checkBox[i].setChecked(True)

    def getCheckboxResult(self):
        checks = []
        for i in range(len(settings.choices)):
            checks.append(self.checkBox[i].isChecked())

        return checks

class PlotDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setObjectName("Dialog")
        self.setWindowTitle('Example data plot')
        self.resize(900, 650)
        self.close_button = QPushButton('Close', self)
        self.close_button.setGeometry(QRect(400, 600, 100, 30))
        self.close_button.setObjectName("pushButton")
        self.close_button.clicked.connect(self.closeDialog)

        self.plotCanvas = PlotCanvas(self, width=9, height=5.7)
        self.toolbar = NavigationToolbar(self.plotCanvas, self)
        self.toolbar.move(0, 600)

    def closeDialog(self):
        self.close()

class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=9, height=6, dpi=100):
        fig = Figure(figsize=(width,height), dpi=dpi)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        data = settings.plotdata

        self.ax1 = self.figure.add_subplot(111)
        self.ax1.plot(data[0], data[1], 'ro', markersize=5)
        self.ax1.set_title('Fig. 1')
        """"
        self.ax2 = self.figure.add_subplot(212)
        self.ax2.plot(data[0], data[2], 'g')
        self.ax2.set_title('Fig. 2')
        """
        self.figure.tight_layout()
        self.draw()


if __name__ == "__main__":
    import sys
    freeze_support()
    settings.init_globals()
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
