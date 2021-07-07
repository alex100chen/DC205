# one small change


#from PyQt5.QtCore import *
#from PyQt5.QtGui import *
#from PyQt5.QtWidgets import *
#from PyQt5.QtWidgets import QMessageBox
#from PyQt5.QtWidgets import QInputDialog
#from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtCore import pyqtSignal, QThread
import sys
import visa
import os
import serial
#import serial.tools.list_ports
import time
import random
import numpy as np
from constants import *
import settings
from interfacesnew import *
from multiprocessing import Process
import matplotlib
import matplotlib.pyplot as plt
from time import strftime
#from Scavenger import *
import binascii
from pathlib import Path
#import requests as reqs
from datetime import datetime, timezone
#from device_tests import timestamp_now
import wip_api
from mainfile import client
#import ref_burn
#from burner import hpmeter, time_str_now
#from burner import time_str_now
#import hpmeter
#from burner import burner_wip
#import burner_wip
#from ref_burn import VRef
#from datetime import datetime
#from dateutil.tz import tzlocal
#from operator import itemgetter
#import zlib
#import base64
#from copy import copy
"""
def datetimefromisofmt(isotime):
    Tloc = isotime.find('T')
    ymd = isotime[:Tloc]
    t = isotime[Tloc+1:]
    dash = ymd.find('-')
    y = ymd[:dash]
    md = ymd[dash + 1:]
    md = md.replace('-', '/')
    mdy = md + '/' + y
    return mdy,t

def isofmtfromdatetime(date, time):
    dr = date[::-1]
    slash = dr.find('/')
    yr = dr[:slash]
    y = yr[::-1]
    mdr = dr[slash+1:]
    md = mdr[::-1]
    md = md.replace('/', '-')
    ymd = y + '-' + md
    isofmt = ymd + 'T' + time
    return isofmt

def plot_graph(*args):
    fig = plt.figure(figsize=(9, 5.5))
    plt.plot(*args, markersize=2)
    plt.xlabel('Temperature (C)')
    plt.ylabel('Volts')
    plt.show(block=True)

def plot_multi(self, *args):
    range = 2
    fig = plt.figure(figsize=(9,8))
    fig.suptitle('Close this window to continue', fontsize=16)
    #fig.canvas.manager.window.wm_geometry("+%d+%d" % (900,250))
    plt.subplot(311)
    plt.ylabel('ppm')
    #plt.xlim(-1.0,1.0)
    if (max(args[1]) <= range) and (min(args[1]) >= -range):
        plt.ylim(-range, +range)
    else:
        plt.autoscale(enable=True, axis='y')
    plt.plot(args[0], args[1], 'bo', markersize=3)
    plt.subplot(312)
    plt.ylabel('ppm')
    if (max(args[3]) <= range) and (min(args[3]) >= -range):
        plt.ylim(-range, +range)
    else:
        plt.autoscale(enable=True, axis='y')
    plt.plot(args[2], args[3], 'ro', markersize=3)
    plt.subplot(313)
    plt.ylabel('ppm')
    plt.xlabel('normalized voltage')
    if (max(args[5]) <= range) and (min(args[5]) >= -range):
        plt.ylim(-range, +range)
    else:
        plt.autoscale(enable=True, axis='y')
    plt.plot(args[4], args[5], 'go', markersize=3)
    plt.show()

def log_plot(*args):
    t = args[0]
    t0 = args[1]
    norm = args[2]
    fig, ax = plt.subplots()
    fig.suptitle('Close this window to continue', fontsize=16)
    fig.canvas.manager.window.wm_geometry("+%d+%d" % (900,250))
    ax.set_title('DC Settling Time, 10V Range, 100%FS rising step')
    ax.set_xlabel('time(s)')
    ax.set_ylabel('Normalized step')
    ax.loglog(t - t0, norm, 'o-')
    ax.grid(which='both')
    ax.set_xlim(left=0.001, right=1)
    ax.set_ylim(bottom=1e-7, top=2)

    plt.show()
"""

#
# The following class definitions are associated with the column of buttons on the left side of the main window.
#


class InstructionExample(QThread):

    test_signal = pyqtSignal(str, str)      # This signal is for posting text to the main window of the page
    btns_signal = pyqtSignal(bool)           # This signal is for disabling/reenabling the buttons while a test is running
    chk_signal = pyqtSignal(int, int)       # This signal is for updating the check-box status associated with the test's button
    msg_signal = pyqtSignal(str)            # This signal is for displaying a message in a pop-up window with an button to continue

    def run(self):
        dc205 = settings.instruments['DC205']
        self.btns_signal.emit(False)
        self.chk_signal.emit(INSTRUCTION_EXAMPLE, GREENARROW) # placing a green arrow in the checkbox indicates that this test is in progress
        self.test_signal.emit("This is where you can record the progress of a test...\n", REPLACE) # 'REPLACE' clears progress window; if you don't want to clear it, then use 'APPEND'

        instructions = "This is where you can add pop-up instructions\n\n"
        self.test_signal.emit(instructions, APPEND) # the progress window is updated with an 'APPENDED' string
        self.msg_signal.emit(instructions)
        time.sleep(1)
        while settings.msg.isActiveWindow(): # This loop halts thread until the message window is closed
            time.sleep(0.5)
        dc205.write("volt 3")
        self.btns_signal.emit(True)

        # 'result' can be defined as an overall pass/fail boolean for your test
        # this code places a mark in the checkbox window by the button
        # it can be a check or a red 'x' for true and false
        # or it can be left blank if neither is appropriate by using 'UNCHECKED'
        result = True
        if result:
            icon = CHECKED
        else:
            icon = REDX
        self.chk_signal.emit(INSTRUCTION_EXAMPLE, icon)


class TextInputExample(QThread):
    test_signal = pyqtSignal(str, str)  # This signal is for posting text to the main window of the page
    btns_signal = pyqtSignal(bool)  # This signal is for disabling/reenabling the buttons while a test is running
    chk_signal = pyqtSignal(int, int)  # This signal is for updating the check-box status associated with the test's button
    txt_signal = pyqtSignal(str, str, int)

    def run(self):
        self.btns_signal.emit(False)
        self.chk_signal.emit(TEXT_INPUT_EXAMPLE, GREENARROW)
        self.test_signal.emit("This is a series of dialog types...\n", REPLACE)

        instructions = "Serial number to be recorded (for example)"
        snum = '123456'
        self.txt_signal.emit(instructions, snum, SERIAL_NUM_WRITE)
        time.sleep(1)
        while settings.txtdial.isModal():
            time.sleep(0.5)

        if settings.choice_rslt:
            self.test_signal.emit(settings.snum, APPEND)
        else:
            self.test_signal.emit('You chose to cancel...', APPEND)

        self.btns_signal.emit(True)

        result = True
        if result:
            icon = CHECKED
        else:
            icon = REDX
        self.chk_signal.emit(TEXT_INPUT_EXAMPLE, icon)

class DataPlotExample(QThread):
    test_signal = pyqtSignal(str, str)  # This signal is for posting text to the main window of the page
    btns_signal = pyqtSignal(bool)  # This signal is for disabling/reenabling the buttons while a test is running
    chk_signal = pyqtSignal(int, int)  # This signal is for updating the check-box status associated with the test's button
    plot_signal = pyqtSignal()

    def run(self):
        self.btns_signal.emit(False)
        self.chk_signal.emit(DATA_PLOT_EXAMPLE, GREENARROW)
        self.test_signal.emit("This plots data from a test...\n", REPLACE)

        settings.plotdata = [] # This is a global container for the data to plot
        x_data = range(0, 10)
        settings.plotdata.append(x_data)
        y0_data = []
        y1_data = []
        for x in x_data:
            y0_data.append(np.sqrt(x))
            y1_data.append(x*x)
        settings.plotdata.append(y0_data)
        settings.plotdata.append(y1_data)

        self.plot_signal.emit() # This initiates the plot window

        self.btns_signal.emit(True)
        result = True
        if result:
            icon = CHECKED
        else:
            icon = REDX
        self.chk_signal.emit(DATA_PLOT_EXAMPLE, icon)

class DataRecExample(QThread):
    test_signal = pyqtSignal(str, str)  # This signal is for posting text to the main window of the page
    btns_signal = pyqtSignal(bool)  # This signal is for disabling/reenabling the buttons while a test is running
    chk_signal = pyqtSignal(int, int)  # This signal is for updating the check-box status associated with the test's button
    plot_signal = pyqtSignal()

    def run(self):
        self.btns_signal.emit(False)
        self.chk_signal.emit(DATA_REC_EXAMPLE, GREENARROW)
        self.test_signal.emit("Data from HP3458...\n", REPLACE)

        hp = settings.instruments['HP3458']
        hp.write('PRESET NORM')
        hp.write('NPLC 1')

        settings.plotdata = [] # This is a global container for the data to plot
        x_data = range(0, 10)
        settings.plotdata.append(x_data)
        y0_data = []
        for x in x_data:
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)
            time.sleep(0.1)
        settings.plotdata.append(y0_data)
        print(y0_data)

#y1_data is a manipulated data example
        y1_data = []
        avg_num = 10
        for i in range(len(y0_data)):
            y = 0
            for j in range(avg_num):
                if i+j < len(y0_data):
                    y += y0_data[i+j]
                else:
                    y += y0_data[j]
            y /= avg_num
            y1_data.append(y)

        settings.plotdata.append(y1_data)

        self.plot_signal.emit() # This initiates the plot window

        self.btns_signal.emit(True)
        result = True
        if result:
            icon = CHECKED
        else:
            icon = REDX
        self.chk_signal.emit(DATA_REC_EXAMPLE, icon)


