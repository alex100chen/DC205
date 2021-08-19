import time
from constants import *
import settings


def set_dc205_voltage_measure_with_3458a(self, temp):
    self.temp = temp

    if settings.hp_34401a:
        hp = settings.instruments['HP34401A']  # may use HP3458A
        hp.write('*CLS')
    else:
        hp = settings.instruments['HP3458A']
        hp.write('PRESET NORM')  # needed for HP3458A
        hp.write('NPLC 1')  # needed for HP3458A

    dc205 = settings.instruments['DC205']

    rows, cols = 5, 10
    arr = [[0 for i in range(cols)] for j in range(rows)]

    y0_data =[]

    self.test_signal.emit(f'\r\n---Chamber at {self.temp} DegC---', APPEND)

    op = range(cols - 1)
    soak = 0.1  # wait time for output to be stable
    for ops in op:
        if ops == 0:
            dc205.write("sout 0")
            dc205.write("rnge 2")
            dc205.write("volt 100")
            dc205.write("sout 1")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")#remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)

        if ops == 1:
            dc205.write("volt 0")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")  # remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)

        if ops == 2:
            dc205.write("volt -100")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")  # remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)

        if ops == 3:
            dc205.write("sout 0")
            dc205.write("rnge 1")
            dc205.write("volt 10")
            dc205.write("sout 1")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")  # remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)

        if ops == 4:
            dc205.write("volt 0")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")  # remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)

        if ops == 5:
            dc205.write("volt -10")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")  # remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)

        if ops == 6:
            dc205.write("sout 0")
            dc205.write("rnge 0")
            dc205.write("volt 1")
            dc205.write("sout 1")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")  # remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)

        if ops == 7:
            dc205.write("volt 0")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")  # remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)

        if ops == 8:
            dc205.write("volt -1")
            time.sleep(soak)
            if settings.hp_34401a:
                hp.write("read?")  # remove this command if use HP3458A
            y = float(hp.read())
            y0_data.append(y)
            self.test_signal.emit(f'{y}', APPEND)
            dc205.write("sout 0")

    print(y0_data)

    #x0_data = range(len(y0_data))
    #settings.plotdata.append(x0_data)
    #settings.plotdata.append(y0_data)
    #self.plot_signal.emit() # This initiates the plot window
    file1 = open(Data_File_Name, "a")
    file1.write("\r" + str(time.ctime()) + ",     " + str(self.temp) + ",    ")  # add date and time and temperature
    for i in range(0, 9):
        file1.write(str(y0_data[i]) + ",  ")  # add x value,
        #file1.write(str(instr.y_data[i]) + "\r")  # add y value \r
    file1.close()
