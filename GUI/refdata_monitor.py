############################################################################################################################################################################
# refdata_monitor.py
#
# Author: Pierre Guillaud
# Data modified: 04/03/2019
#
# This program inputs data obtained by a dedicated ADC MCU measuring 36 temperatures using thermistors and data obtained from a dedicated IP MCU measuring 36 temperatures
# using radiometric cameras, and outputs 12 voltage percents to a dedicated MCU powering simulation electronics resistors.
# Different frames display the data inputs and outputs, and allow for data saving and serial testing
#
############################################################################################################################################################################

# ----- Imports ------------------------------------------------------------------------------------------------------------------------------------------------------------

# Tkinter
try:
    import Tkinter as tk
    import ttk
    from tkFileDialog import askopenfilename
    import tkMessageBox
    import tkSimpleDialog
    from tkSimpleDialog import Dialog
except ModuleNotFoundError:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename
    from tkinter.filedialog import askdirectory
    import tkinter.messagebox as tkMessageBox
    import tkinter.simpledialog as tkSimpleDialog
    from tkinter.simpledialog import Dialog
    from tkinter.scrolledtext import ScrolledText

# Numpy
import numpy as np
import math

# OS
import os as os

# pySerial
import serial

# Threading
import threading

# Sys
import sys

# Matplotlib
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import style
style.use('ggplot')

# DateTime
import datetime as dt

# Time
import time

# ----- Global variables ---------------------------------------------------------------------------------------------------------------------------------------------------

# serial_data1 : global variable containing thermistor temperatures
#   set by serial1, used graph1, table1
# serial_data2 : global variable containing camera temperatures
#   set by serial2, used by graph2, table2

# data_template: temperature index string array
#   used by datatable
# b1_rec, b2_rec, b3_rec used for ping tests with ADC board
# IP_flag : control decisions from IP
#   set by serial2, unused
# heat1, heat2 : percent set for simulation electronics
#   set by logframe, used by serial3

# errorlist : global list of exceptions encountered

serial_data1 = [00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,
                00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0]
serial_data2 = [00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,
                00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0]
data_template =['  1','  2','  3','  4','  5','  6','  7','  8','  9',' 10',' 11',' 12',' 13',' 14',' 15',' 16',
                ' 17',' 18',' 19',' 20',' 21',' 22',' 23',' 24',' 25',' 26',' 27',' 28',' 29',' 30',' 31',' 32',
                ' 33',' 34',' 35',' 36']
b1_rec = False
b2_rec = False
b3_rec = False
heat1 = [0, 0, 0, 0, 0, 0]
heat2 = [0, 0, 0, 0, 0, 0]
errorlist = []
IP_flag = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

 # Save current time to errorlist for future references
errorlist.append(dt.datetime.now())
errorlist.append(matplotlib.dates.date2num(dt.datetime.now()))

# ----- Serial -------------------------------------------------------------------------------------------------------------------------------------------------------------

# --- Serial1 ---
    # This serial port is used to input and output to the ADC MCU (8-N-9600) on COM3
serial1 = serial.Serial(timeout=1,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS)
serial1.baudrate = 9600
serial1.port = 'COM3'
errorlist.append('Port ' + serial1.name + ' used (1).')

# --- Serial2 ---
    # This serial port is used to input and output to the IP MCU (8-N-9600)
serial2 = serial.Serial(timeout=1,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS)
serial2.baudrate = 9600
serial2.port = 'COM6'
errorlist.append('Port ' + serial2.name + ' used (2).')

# --- Serial3 ---
    # This serial port is used to output to the HEATER MCU (8-N-9600)
serial3 = serial.Serial(timeout=1,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS)
serial3.baudrate = 9600
serial3.port = 'COM4'
errorlist.append('Port ' + serial3.name + ' used (3).')
errorlist.append('---')
try:
    serial3.open()
except Exception as e:
    errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
    errorlist.append(e)
    errorlist.append('---')


# ----- Threads ------------------------------------------------------------------------------------------------------------------------------------------------------------

# --- Serial listener (Thermistors system & Image Processing System) ---
    # This function continuously waits for incoming serial data to read, and writes to serial communication on a fixed time interval

def seriallisten():
    # Global variable call
    global b1_rec
    global b2_rec
    global b3_rec
    global serial_data1
    global serial_data2
    global update1
    global errorlist
    global IP_flag

    # Local variable definition
    n = 0
    rec_data_status = 0
    rec_ind = 0
    rec_data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    conc_rec_data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                     0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    closest_temp_array = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,0,0]
    nonordered_data = [00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,
                00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0,00.0]

    rec_data_status_2 = 0
    rec_ind_2 = 0
    rec_data_2 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    
        # Constant conversion factors from ADC resistance readings to actual temperatures
    res_to_temp = [190953, 145953, 112440, 87285, 68260, 53762,
                   42636, 34038, 27348, 22108, 17979, 14706, 12094,
                   10000, 8310.8, 6941.1, 5824.9, 4910.6, 4158.3,
                   3536.2, 3019.7, 2588.8, 2228.0, 1924.6, 1668.4,
                   1451.3, 1266.7, 1109.2, 974.26, 858.33]
    
    while 1:
        if serial1.isOpen() == True:
            try:
                n += 1
                ini_input1 = ''
                    # If incoming serial data buffer full, decode serial data and save
                if serial1.inWaiting() > 0:
                    ini_input1_raw = serial1.readline()
                    ini_input1 = ini_input1_raw.decode('utf-8')

                    # Send first ping to ADC MCU, to check if serial communication works correctly
                if n == 200000 and rec_data_status == 0:
                    ser_output = 'b' + '1' + '\n'
                    serial1.write(ser_output.encode('ascii'))
                    b1_rec = False

                    # Send second ping to ADC MCU, to check if MCU can communicate with the ADC board
                if n == 250000 and rec_data_status == 0:
                    ser_output = 'b' + '2' + '\n'
                    serial1.write(ser_output.encode('ascii'))
                    n = 0
                    b2_rec = False
                    b3_rec = False

                    # Send fetch message to ADC MCU, to start receiving ADC data
                if n == 100000:
                    rec_data_status = 0
                    ser_output = 'd' + 'r' + 'e' + 'q' + '\n'
                    serial1.write(ser_output.encode('ascii'))

                    # if currently in the process of receiving ADC data, save data to specific array, then increment array
                if rec_data_status == 1 and ini_input1 != 'endd\n' and ini_input1 != '':
                    rec_data[rec_ind] = ini_input1
                    rec_ind += 1

                    # if first ping successful, set to true appropriate variable
                if ini_input1 == 'b1c\n':
                    b1_rec = True

                    # if second ping partially successful, set to true and false appropriate variables
                if ini_input1 == 'b2c\n':
                    b2_rec = True
                    b3_rec = True

                    # if second ping fully successful, set to true appropriate variables
                if ini_input1 == 'b2n\n':
                    b2_rec = True

                    # if received, indicates that next 40 serial data inputs will be ADC data
                elif ini_input1 == 'begd\n':
                    rec_data_status = 1
                    rec_ind = 0

                    # if received, indicates that ADC data finished transfering, can proceed to transform into useful temperature data
                elif ini_input1 == 'endd\n':
                    rec_data_status = 0
                    for i in range(0,40): # for each data point
                        data_temp = rec_data[i]
                        data_temp_2 = [0,0,0,0]
                        for j in range(0,4):
                            data_temp_2[j] = data_temp[j]
                        if int(''.join(data_temp_2)) != 0:
                                # Convert ADC data to resistance
                            conc_rec_data[i] = round(18000/(3.3/(3.3*int(''.join(data_temp_2))/4095)-1))
                            nonordered_data[i] = 0
                            if conc_rec_data[i] < 190953:
                                    # Convert resistance values to temperatures, if resistance is within the min and max convertion factors
                                #closest_temp_array[:] = [abs(conc_rec_data[i]-m) for m in res_to_temp]
                                #closest_temp_ind = closest_temp_array.index(min(closest_temp_array))
                                #if conc_rec_data[i] < res_to_temp[closest_temp_ind]:
                                #    closest_temp_ind += 1
                                #resulting_temp = (-40+5*(closest_temp_ind))-5*((conc_rec_data[i]-res_to_temp[closest_temp_ind])/(res_to_temp[closest_temp_ind-1]-res_to_temp[closest_temp_ind]))
                                resulting_temp = 1/(1/298+1/3435*(math.log(conc_rec_data[i]/10000)))-273
                                nonordered_data[i] = abs(round(resulting_temp,2))
                    temp = nonordered_data[16]
                    nonordered_data[16] = nonordered_data[18]
                    nonordered_data[18] = temp
                    temp = nonordered_data[17]
                    nonordered_data[17] = nonordered_data[19]
                    nonordered_data[19] = temp
                        # Manual reordering of data
                    serial_data1[0:8] = nonordered_data[0:8]
                    serial_data1[6:14] = nonordered_data[8:16]
                    serial_data1[12:20] = nonordered_data[16:24]
                    serial_data1[18:26] = nonordered_data[24:32]
                    serial_data1[24:32] = nonordered_data[32:40]

            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                errorlist.append('---')
                
        if serial2.isOpen() == True:
            try:
                ini_input2 = ''
                    # If incoming serial data buffer full, decode serial data and save
                if serial2.inWaiting() > 0:
                    ini_input2_raw = serial2.readline()
                    ini_input2 = ini_input2_raw.decode('utf-8')

                    # if received, indicates that next 36 serial data inputs will be IP data
                if ini_input2 == 'begin\n':
                    rec_data_status_2 = 1
                    rec_ind_2 = 0

                    # if currently in the process of receiving IP data, save data to specific array, then increment array
                if rec_data_status_2 == 1 and ini_input2 != 'end\n' and ini_input2 != '' and ini_input2 != 'begin\n':
                    rec_data_2[rec_ind_2] = ini_input2
                    rec_ind_2 += 1

                    # if received, indicates that IP data finished transfering, can proceed to transform into useful temperature data
                    # format of inputs FSTTTT\n, where F is flag (normal, too hot, too cold), S is sign of temperature, T is temperature
                elif ini_input2 == 'end\n':
                    rec_data_status_2 = 0
                    for i in range(0,36): # For each data point
                        data_temp = str(rec_data_2[i])
                        IP_flag[i] = int(data_temp[0]) # Sets correct flag in global variables
                        if int(data_temp[2]) == 0:
                            sign = 1
                        else:
                            sign = -1
                        serial_data2[i] = sign*(float(data_temp[4:(len(data_temp)-1)])) # Sets correct temperature in global variables

            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                errorlist.append('---')


# ----- Classes ------------------------------------------------------------------------------------------------------------------------------------------------------------

# MonitorFrame
    # Main GUI window, handles graphs, controls, table, save options
class MonitorFrame():
    def __init__(self,parent):
            # Create main window frame
        self.mainframe = ttk.Frame(parent, style = 'main.TFrame' )
        self.mainframe.place(height=850, width=1500, x=50, y=25)

            # Create graph subframes
        self.graph1 = ttk.Frame(self.mainframe,style = 'graph.TFrame')
        self.graph1.place(height=400, width=650, x=25, y=10)
        self.graph2 = ttk.Frame(self.mainframe,style = 'graph.TFrame')
        self.graph2.place(height=400, width=650, x=825, y=10)
        self.LEDframe = ttk.Frame(self.mainframe,style = 'controls.TFrame')
        self.LEDframe.place(height=400, width=140, x=680, y=10)
        self.initialize_LEDs()

            # Create table and initialize values
        self.initialize_table()

            # Create controls subframe
        self.controls = ttk.Frame(self.mainframe,style = 'controls.TFrame')
        self.controls.place(height=285, width=1450, x=25, y=555)
                # Create serial toggle data
        self.onoff_data1 = ttk.Button(self.controls, text = 'Toggle Ref Data', style = 'button.TButton',command=lambda : self.togglegraph(1))
        self.onoff_data2 = ttk.Button(self.controls, text = 'Toggle IP Data', style = 'button.TButton',command=lambda : self.togglegraph(2))
        self.onoff_data1.place(height=127,width=200,x=25,y=10)
        self.onoff_data2.place(height=127,width=200,x=25,y=148)
        self.data1_status = ttk.Frame(self.controls, style = 'off.TFrame')
        self.data1_status.place(height=127,width = 50, x = 250, y=10)
        self.data2_status = ttk.Frame(self.controls, style = 'off.TFrame')
        self.data2_status.place(height=127,width = 50, x = 250, y=148)

        self.state1 = 0
        self.state2 = 0
        self.check1 = ttk.Button(self.controls, text = 'Test connection1', style = 'button.TButton', command=lambda : self.opentest(1))
        self.check2 = ttk.Button(self.controls, text = 'Test connection2', style = 'button.TButton', command=lambda : self.opentest(2))
        self.logview = ttk.Button(self.controls, text = 'Configuration', style = 'button.TButton', command=lambda : self.openlog())
        self.check1.place(height=58,width=200,x=500,y=10)
        self.check2.place(height=58,width=200,x=500,y=79)
        self.logview.place(height=58,width=200,x=500,y=217)
        
        ttk.Separator(self.controls, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=1, sticky='ns')
        self.controls.columnconfigure(1, weight=1)
        self.controls.columnconfigure(2, weight=1)
        self.controls.columnconfigure(3, weight=1)
        self.controls.rowconfigure(0, weight=1)

        self.save_status = 0
        self.save_index = 0
        self.save_file_exists = False
        self.commentbox = tk.Text(self.controls)
        self.commentbox.place(height=195,width=675,x=750,y=10)
        self.saveone = ttk.Button(self.controls, text = 'Save Once', style='button.TButton',state=tk.DISABLED, command=lambda : self.save_data(1))
        self.savemultiple = ttk.Button(self.controls, text = 'Save Continuously', style='button.TButton',state=tk.DISABLED, command=lambda : self.save_data(2))
        self.savingcont = ttk.Frame(self.controls, style = 'off.TFrame')
        self.saveone.place(height=58,width=133,x=750,y=217)
        self.savemultiple.place(height=58,width=133,x=895,y=217)
        self.savingcont.place(height=58,width=50,x=1040,y=217)
        self.filechoose = ttk.Button(self.controls, text = 'Choose Save Location', style='button.TButton', command=lambda : self.choosefile())
        self.filechoose.place(height=58,width=133,x=1292,y=217)

        self.rd = ReceiveData()
        self.creategraphs()


    def save_data(self,ind):
        try:
            if self.save_file_exists == False:
                self.filename_RD = 'refdata' + str(round(matplotlib.dates.date2num(dt.datetime.now())*100000)) + '.txt'
                self.filename_RD = os.path.join(self.saveloc, self.filename_RD)
                print(self.filename_RD)
                self.filename_IP = 'IPdata' + str(round(matplotlib.dates.date2num(dt.datetime.now())*100000)) + '.txt'
                self.filename_IP = os.path.join(self.saveloc, self.filename_IP)
                print(self.filename_IP)
                self.open_savefile_RD = open(self.filename_RD,"w+")
                self.open_savefile_IP = open(self.filename_IP,"w+")
                self.save_file_exists = True
            else:
                self.open_savefile_RD = open(self.filename_RD,"a")
                self.open_savefile_IP = open(self.filename_IP,"a")
            if ind == 1:
                self.savingcont.configure(style = 'error.TFrame')

                try:
                    self.open_savefile_RD.write('\n'+'# '+self.commentbox.get("1.0",tk.END))
                    to_write = str(self.rd.rec_data1_2[-1])
                    for i in range(36):
                        to_write = to_write + ' ' + str(self.rd.rec_data1_1[i][-1])
                    to_write = to_write + '\n'
                    self.open_savefile_RD.write(to_write)
                except Exception as e:
                    errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                    errorlist.append(e)
                    errorlist.append('---')

                try:
                    self.open_savefile_IP.write('\n'+'# '+self.commentbox.get("1.0",tk.END))
                    to_write = str(self.rd.rec_data2_2[-1])
                    for i in range(36):
                        to_write = to_write + ' ' + str(self.rd.rec_data2_1[i][-1])
                    to_write = to_write + '\n'
                    self.open_savefile_IP.write(to_write)
                except Exception as e:
                    errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                    errorlist.append(e)
                    errorlist.append('---')
                
                self.savingcont.configure(style = 'off.TFrame')
                
            if ind == 2:
                if self.save_status == 0:
                    self.save_index = self.rd.rec_data1_2[-1]
                    self.save_status = 1
                    self.savingcont.configure(style = 'on.TFrame')
                else:
                    self.save_status = 0
                    self.savingcont.configure(style = 'error.TFrame')

                    try:
                        self.open_savefile_RD.write('\n'+'# '+self.commentbox.get("1.0",tk.END))
                        for j in range(self.save_index, self.rd.rec_data1_2[-1]):
                            to_write = str(self.rd.rec_data1_2[j])
                            for i in range(36):
                                to_write = to_write + ' ' + str(self.rd.rec_data1_1[i][j])
                            to_write = to_write + '\n'
                            self.open_savefile_RD.write(to_write)
                    except Exception as e:
                        errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                        errorlist.append(e)
                        errorlist.append('---')                    

                    try:
                        self.open_savefile_IP.write('\n'+'# '+self.commentbox.get("1.0",tk.END))
                        for j in range(self.save_index, self.rd.rec_data2_2[-1]):
                            to_write = str(self.rd.rec_data2_2[j])
                            for i in range(36):
                                to_write = to_write + ' ' + str(self.rd.rec_data2_1[i][j])
                            to_write = to_write + '\n'
                            self.open_savefile_RD.write(to_write)
                    except Exception as e:
                        errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                        errorlist.append(e)
                        errorlist.append('---')
                        
                    self.savingcont.configure(style = 'off.TFrame')

            self.open_savefile_RD.close()
            self.open_savefile_IP.close()
            
        except Exception as e:
            errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
            errorlist.append(e)
            errorlist.append('---')

    def initialize_LEDs(self):
        self.LED_hot = [0,0,0,0,0,0]
        self.LED_hot[0] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_hot[0].place(height=30,width = 60, x = 75, y=39)
        self.LED_hot[1] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_hot[1].place(height=30,width = 60, x = 75, y=103)
        self.LED_hot[2] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_hot[2].place(height=30,width = 60, x = 75, y=167)
        self.LED_hot[3] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_hot[3].place(height=30,width = 60, x = 75, y=231)
        self.LED_hot[4] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_hot[4].place(height=30,width = 60, x = 75, y=295)
        self.LED_hot[5] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_hot[5].place(height=30,width = 60, x = 75, y=359)

        self.LED_cold = [0,0,0,0,0,0]
        self.LED_cold[0] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_cold[0].place(height=30,width = 60, x = 5, y=39)
        self.LED_cold[1] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_cold[1].place(height=30,width = 60, x = 5, y=103)
        self.LED_cold[2] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_cold[2].place(height=30,width = 60, x = 5, y=167)
        self.LED_cold[3] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_cold[3].place(height=30,width = 60, x = 5, y=231)
        self.LED_cold[4] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_cold[4].place(height=30,width = 60, x = 5, y=295)
        self.LED_cold[5] = ttk.Frame(self.LEDframe, style = 'disabled.TFrame')
        self.LED_cold[5].place(height=30,width = 60, x = 5, y=359)

        tk.Label(self.LEDframe,text='Tray 1',font=('fixedsys',12),background='lightgrey').place(height=20,width = 130, x = 5, y=15)
        tk.Label(self.LEDframe,text='Tray 2',font=('fixedsys',12),background='lightgrey').place(height=20,width = 130, x = 5, y=79)
        tk.Label(self.LEDframe,text='Tray 3',font=('fixedsys',12),background='lightgrey').place(height=20,width = 130, x = 5, y=143)
        tk.Label(self.LEDframe,text='Tray 4',font=('fixedsys',12),background='lightgrey').place(height=20,width = 130, x = 5, y=207)
        tk.Label(self.LEDframe,text='Tray 5',font=('fixedsys',12),background='lightgrey').place(height=20,width = 130, x = 5, y=271)
        tk.Label(self.LEDframe,text='Tray 6',font=('fixedsys',12),background='lightgrey').place(height=20,width = 130, x = 5, y=335)

        

    def update_LEDs(self):
        self.LED_cold[0].configure(style = 'disabled.TFrame')
        self.LED_hot[0].configure(style = 'disabled.TFrame')
        for i in range(0,6):
            if IP_flag[i] == 1:
                self.LED_cold[0].configure(style = 'toocold.TFrame')
            if IP_flag[i] == 2:
                self.LED_hot[0].configure(style = 'toohot.TFrame')
        self.LED_cold[1].configure(style = 'disabled.TFrame')
        self.LED_hot[1].configure(style = 'disabled.TFrame')
        for i in range(6,12):
            if IP_flag[i] == 1:
                self.LED_cold[1].configure(style = 'toocold.TFrame')
            if IP_flag[i] == 2:
                self.LED_hot[1].configure(style = 'toohot.TFrame')
        self.LED_cold[2].configure(style = 'disabled.TFrame')
        self.LED_hot[2].configure(style = 'disabled.TFrame')
        for i in range(12,18):
            if IP_flag[i] == 1:
                self.LED_cold[2].configure(style = 'toocold.TFrame')
            if IP_flag[i] == 2:
                self.LED_hot[2].configure(style = 'toohot.TFrame')
        self.LED_cold[3].configure(style = 'disabled.TFrame')
        self.LED_hot[3].configure(style = 'disabled.TFrame')
        for i in range(18,24):
            if IP_flag[i] == 1:
                self.LED_cold[3].configure(style = 'toocold.TFrame')
            if IP_flag[i] == 2:
                self.LED_hot[3].configure(style = 'toohot.TFrame')
        self.LED_cold[4].configure(style = 'disabled.TFrame')
        self.LED_hot[4].configure(style = 'disabled.TFrame')
        for i in range(24,30):
            if IP_flag[i] == 1:
                self.LED_cold[4].configure(style = 'toocold.TFrame')
            if IP_flag[i] == 2:
                self.LED_hot[4].configure(style = 'toohot.TFrame')
        self.LED_cold[5].configure(style = 'disabled.TFrame')
        self.LED_hot[5].configure(style = 'disabled.TFrame')
        for i in range(30,36):
            if IP_flag[i] == 1:
                self.LED_cold[5].configure(style = 'toocold.TFrame')
            if IP_flag[i] == 2:
                self.LED_hot[5].configure(style = 'toohot.TFrame')
        
    def initialize_table(self):
        try:
            self.datatable.destroy()
        except Exception as e:
            ...
        self.datatable = ttk.Frame(self.mainframe,style = 'table.TFrame')
        self.datatable.place(height=125, width=1450, x=25, y=420)
        self.databox = []
        for i in range(6):
            self.databox.append('')
        for row in range(3):
            self.datatable.rowconfigure(row, weight=1)
            for col in range(2):
                self.databox[row*2+col] = tk.Text(self.datatable)
                if row == 0 and col != 0:
                    self.databox[row*2+col].place(height=43,width=1339,x=111,y=0)
                    for i in range(36):
                        self.databox[row*2+col].insert(tk.END, str(data_template[i]))
                        self.databox[row*2+col].insert(tk.END, ' ')
                elif row == 1 and col == 0:
                    self.databox[row*2+col].place(height=41,width=111,x=0,y=43)
                    self.databox[row*2+col].insert(tk.END, 'Ref Data')
                elif row == 1 and col != 0:
                    self.databox[row*2+col].place(height=41,width=1339,x=111,y=43)
                    self.databox[row*2+col].insert(tk.END, serial_data1[0:36])
                elif row == 2 and col == 0:
                    self.databox[row*2+col].place(height=41,width=111,x=0,y=84)
                    self.databox[row*2+col].insert(tk.END, 'IP')
                elif row == 2 and col != 0:
                    self.databox[row*2+col].place(height=41,width=1339,x=111,y=84)
                    self.databox[row*2+col].insert(tk.END, serial_data2[0:36])
                    self.datatable.columnconfigure(col, weight=0)
                self.databox[row*2+col].config(state=tk.DISABLED,font=("Courier",11))

    def update_table(self):
        for row in range(2):
            for col in range(1):
                self.databox[(row+1)*2+(col+1)].config(state='normal')
                self.databox[(row+1)*2+(col+1)].delete(1.0, tk.END)
                if row == 0:
                    temp = []
                    for i in range(36):
                        temp.append(str(serial_data1[i]))
                        if temp[i] == '0':
                            temp[i] = "0.0"
                    self.databox[(row+1)*2+(col+1)].insert(tk.END, temp)
                elif row == 1:
                    temp = []
                    for i in range(36):
                        temp.append(str(serial_data2[i]))
                        if temp[i] == '0':
                            temp[i] = "0.0"
                    self.databox[(row+1)*2+(col+1)].insert(tk.END, temp)
                self.databox[(row+1)*2+(col+1)].config(state=tk.DISABLED)
    
    def opentest(self,ind):
        if ind == 1:
            try:
                self.test_window1.lift()
                self.test_window1.deiconify() 
            except:
                self.test_window1 = tk.Toplevel(root)
                self.test_window1.title('Connection Test (1)')
                self.test_window1.geometry("300x400")
                self.test_window1.resizable(width=False, height=False)
                self.tframe1 = TestFrame(self.test_window1,1)
                self.tframe1.runtest(ind)
        elif ind == 2:
            try:
                self.test_window2.lift()
                self.test_window2.deiconify() 
            except:
                self.test_window2 = tk.Toplevel(root)
                self.test_window2.title('Connection Test (2)')
                self.test_window2.geometry("300x400")
                self.test_window2.resizable(width=False, height=False)
                self.tframe2 = TestFrame(self.test_window2,2)
                self.tframe2.runtest(ind)
                
    def openlog(self):
        try:
            self.logwindow.lift()
            self.logwindow.deiconify() 
        except:
            self.logwindow = tk.Toplevel(root)
            self.logwindow.title('Configuration')
            self.logwindow.geometry("500x725")
            self.logwindow.resizable(width=False, height=False)
            self.logframe = LogFrame(self.logwindow)

    def togglegraph(self,ind):
        if ind == 1:
            if self.state1 == 1:
                serial1.close()
                self.data1_status.configure(style='off.TFrame')
                self.state1 = 0
            else:
                try:
                    serial1.open()
                    self.data1_status.configure(style='on.TFrame')
                    self.state1 = 1
                except Exception as e:
                    self.data1_status.configure(style='error.TFrame')
                    errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                    errorlist.append(e)
                    errorlist.append('---')
        elif ind == 2:
            if self.state2 == 1:
                serial2.close()
                self.data2_status.configure(style='off.TFrame')
                self.state2 = 0
            else:
                try:
                    serial2.open()
                    self.data2_status.configure(style='on.TFrame')
                    self.state2 = 1
                except Exception as e:
                    self.data2_status.configure(style='error.TFrame')
                    errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                    errorlist.append(e)
                    errorlist.append('---')

    def choosefile(self):
        self.saveloc = askdirectory()
        if self.saveloc == '':
            self.saveloc= os.getcwd()
        print(self.saveloc)
        self.saveone.configure(state=tk.NORMAL)
        self.savemultiple.configure(state=tk.NORMAL)

    def creategraphs(self):
        self.fig1 = Figure(figsize=(20,20),dpi=100)
        self.fig1_info = self.fig1.add_subplot(111)
        self.fig2 = Figure(figsize=(20,20),dpi=100)
        self.fig2_info = self.fig2.add_subplot(111)

        self.canvas1 = FigureCanvasTkAgg(self.fig1, self.graph1)
        self.canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand = True)
        self.fig1_info.plot([0],[0], 'red', label='Legend')
        self.legend1 = self.fig1_info.legend(loc='upper left', shadow=False, fontsize='large')
        self.legend1.get_frame().set_facecolor('white')
        self.canvas1.draw()

        self.fig2_info.plot(0,0, 'red', label='Legend')
        self.legend2 = self.fig2_info.legend(loc='upper left', shadow=False, fontsize='large')
        self.legend2.get_frame().set_facecolor('white')
        self.canvas2 = FigureCanvasTkAgg(self.fig2, self.graph2)
        self.canvas2.draw()
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand = True)

        self.graph_colors = ['aqua', 'azure', 'blue', 'cyan', 'chartreuse', 'coral', 'brown', 'crimson', 'darkblue', 'darkgreen', 'fuchsia', 'gold', 'grey', 'khaki',
                             'green', 'lightblue', 'lavender', 'lightgreen', 'magenta', 'orange', 'pink', 'purple', 'red', 'sienna', 'silver', 'teal', 'violet','yellow',
                             'yellowgreen', 'white', 'tan', 'salmon', 'navy', 'ivory', 'beige', 'black']

    def updategraphs(self,fignum,datapoints):
        if fignum == 1:
            self.fig1_info.cla()
            lastind = len(self.rd.rec_data1_1[1][:])
            for i in datapoints:
                if lastind > 10:
                    self.fig1_info.plot(self.rd.rec_data1_2[lastind-10:lastind].tolist(),self.rd.rec_data1_1[i-1][lastind-10:lastind].tolist(), self.graph_colors[i-1], label=('Grid-'+str(i)))
                else:
                    self.fig1_info.plot(self.rd.rec_data1_2[0:lastind],self.rd.rec_data1_1[i-1][0:lastind], self.graph_colors[i-1], label=('Grid-'+str(i)))
                self.legend1 = self.fig1_info.legend(loc='upper left', shadow=False)
                self.legend1.get_frame().set_facecolor('white')
                self.canvas1.draw()
        elif fignum == 2:
            self.fig2_info.cla()
            lastind = len(self.rd.rec_data2_1[1][:])
            for i in datapoints:
                if lastind > 10:
                    self.fig2_info.plot(self.rd.rec_data2_2[lastind-10:lastind].tolist(),self.rd.rec_data2_1[i-1][lastind-10:lastind].tolist(), self.graph_colors[i-1], label=('Grid-'+str(i)))
                else:
                    self.fig2_info.plot(self.rd.rec_data2_2[0:lastind],self.rd.rec_data2_1[i-1][0:lastind], self.graph_colors[i-1], label=('Grid-'+str(i)))
                self.legend2 = self.fig2_info.legend(loc='upper left', shadow=False)
                self.legend2.get_frame().set_facecolor('white')
                self.canvas2.draw()
            
class TestFrame():
    def __init__(self,parent,ind):
        self.par = parent
        self.mainframe = ttk.Frame(parent, style = 'second.TFrame' )
        self.mainframe.place(height=310, width=280, x=10, y=10)
        self.refreshbutton = ttk.Button(parent,style='button.TButton', text='Run Test', state = tk.DISABLED, command=lambda : self.runtest(ind))
        self.refreshbutton.place(height=60,width = 280,y=330,x=10)

    def serial_test(self,ind):
        if ind == 1:
            try:
                if serial1.isOpen():
                    return 1
                else:
                    return 0
            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                errorlist.append('---')
                return -1
        else:
            try:
                if serial2.isOpen():
                    return 1
                else:
                    return 0
            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                errorlist.append('---')
                return -1
        
    def connect_test(self,ind):
        if ind == 1:
            try:
                if serial1.isOpen():
                    if b1_rec == True:
                        return 1
                    else:
                        return 0
                else:
                    return 0
            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                errorlist.append('---')
                return -1
        else:
            try:
                if serial2.isOpen():
                    if False == True: #TEST IP
                        return 1
                    else:
                        return 0
                else:
                    return 0
            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                errorlist.append('---')
                return -1
        
    def read_test(self,ind):
        if ind == 1:
            try:
                if serial1.isOpen():
                    if b2_rec == True:
                        return 1
                    else:
                        return 0
                else:
                    return 0
            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                ferrorlist.append('---')
                return -1
        else:
            try:
                if serial2.isOpen():
                    if False == True: #TEST IP
                        return 1
                    else:
                        return 0
                else:
                    return 0
            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                ferrorlist.append('---')
                return -1
        
    def write_test(self,ind):
        if ind == 1:
            try:
                if serial1.isOpen():
                    if b3_rec == True:
                        return 1
                    else:
                        return 0
                else:
                    return 0
            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                errorlist.append('---')
                return -1
        else:
            try:
                if serial2.isOpen():
                    if False == True: #TEST IP
                        return 1
                    else:
                        return 0
                else:
                    return 0
            except Exception as e:
                errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
                errorlist.append(e)
                errorlist.append('---')
                return -1
        
    def temp_test(self,ind):
        try:
            partial = 0
            all_temp = 1
            if ind == 1:
                if sum(serial_data1) == 0:
                    all_temp = 0
                else:
                    for i in serial_data1[0:36]:
                        if i != 0:
                            partial = 1
                        else:
                            all_temp = 0
            elif ind == 2:
                if sum(serial_data2) == 0:
                    all_temp = 0
                else:
                    for i in serial_data2[0:36]:
                        if i != 0:
                            partial = 1
                        else:
                            all_temp = 0
            if all_temp == 1:
                return 1
            elif partial == 1:
                return 2
            else:
                return 0
        except Exception as e:
            errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
            errorlist.append(e)
            errorlist.append('---')
            return -1
        
                

    def runtest(self,ind):
        try:
            self.mainframe.destroy()
        except Exception as e:
            errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
            errorlist.append(e)
            errorlist.append('---')
        self.mainframe = ttk.Frame(self.par, style = 'second.TFrame' )
        self.mainframe.place(height=310, width=280, x=10, y=10)
        for i in range(1,11):
            self.mainframe.rowconfigure(i, weight=1)
        
        self.refreshbutton.configure(state = tk.DISABLED)
        tk.Label(self.mainframe,text='Checking Monitor Serial Input...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=1,stick='w')
        res = self.serial_test(ind)
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=2)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato',anchor='w').grid(column=0,row=2)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=2)
            
        tk.Label(self.mainframe,text='Checking Monitor Connection...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=3,stick='w')
        res = self.connect_test(ind)
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=4)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato').grid(column=0,row=4)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=4)

        tk.Label(self.mainframe,text='Checking MCU Input Connections...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=5,stick='w')
        res = self.read_test(ind)
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=6)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato').grid(column=0,row=6)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=6)

        tk.Label(self.mainframe,text='Checking MCU Output Connections...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=7,stick='w')
        res = self.write_test(ind)
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=8)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato').grid(column=0,row=8)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=8)

        tk.Label(self.mainframe,text='Checking wired connections...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=9,stick='w')
        res = self.temp_test(ind)
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=10)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato').grid(column=0,row=10)
        elif res == 2:
            tk.Label(self.mainframe,text='PARTIAL SUCCESS',font=('fixedsys',12),background='orange').grid(column=0,row=10)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=10)
        self.refreshbutton.configure(state = 'normal')

class LogFrame():
    def __init__(self,parent):
        self.mainframe = ttk.Frame(parent, style = 'second.TFrame' )
        self.mainframe.place(height=705, width=480, x=10, y=10)
        self.errorbox = ScrolledText(self.mainframe,state=tk.DISABLED)
        self.errorbox.place(height=274, width=470,x=5,y=420)
        self.errorbox.configure(state='normal')
        for i in errorlist:
            self.errorbox.insert(tk.END,str(i))
            self.errorbox.insert(tk.END,'\n\n')
        self.errorbox.configure(state=tk.DISABLED)        

        self.heater_nb = ttk.Notebook(self.mainframe)
        self.heater_nb.place(x=5, y=250, height=160, width=470)
        self.heater_frame = [0, 0, 0, 0 ,0 ,0]
        self.heater1_slider = [0, 0, 0, 0, 0 ,0]
        self.heater2_slider = [0, 0, 0, 0, 0 ,0]
        self.confirm1 = [0, 0, 0, 0, 0 ,0]
        self.confirm2 = [0, 0, 0, 0, 0 ,0]

        for i in range(6):
            self.heater_frame[i] = ttk.Frame(self.heater_nb, style = 'second.TFrame')
            self.heater_nb.add(self.heater_frame[i], text='Tray '+str(i+1))

        for i in range(6):     
            self.heater1_slider[i] = tk.Scale(self.heater_frame[i], from_=0, to=100,orient=tk.HORIZONTAL)
            self.heater1_slider[i].place(height= 58, width=240, x=5,y=5)
            self.heater1_slider[i].set(heat1[i])
            self.confirm1[i] = ttk.Button(self.heater_frame[i], text ="Confirm (Heater 1)",style='button.TButton', command=lambda : self.heaterconfirm(1))
            self.confirm1[i].place(height = 58, width = 200, x = 260, y = 5)
            self.heater2_slider[i] = tk.Scale(self.heater_frame[i], from_=0, to=100,orient=tk.HORIZONTAL)
            self.heater2_slider[i].place(height= 58, width=240, x=5,y=68)
            self.heater2_slider[i].set(heat2[i])
            self.confirm2[i] = ttk.Button(self.heater_frame[i], text ="Confirm (Heater 2)",style='button.TButton', command=lambda : self.heaterconfirm(2))
            self.confirm2[i].place(height = 58, width = 200, x = 260, y = 68)

        self.heater_nb.select(self.heater_frame[0])
        self.heater_nb.enable_traversal()

        self.grid_list = tk.StringVar()
        self.grid_list.set("Grid-01 Grid-02 Grid-03 Grid-04 Grid-05 Grid-06 Grid-07 Grid-08 \
Grid-09 Grid-10 Grid-11 Grid-12 Grid-13 Grid-14 Grid-15 Grid-16 \
Grid-17 Grid-18 Grid-19 Grid-20 Grid-21 Grid-22 Grid-23 Grid-24 \
Grid-25 Grid-26 Grid-27 Grid-28 Grid-29 Grid-30 Grid-31 Grid-32 \
Grid-33 Grid-34 Grid-35 Grid-36")
        self.grid_select = tk.Listbox(self.mainframe, listvariable=self.grid_list, selectmode=tk.MULTIPLE)
        self.grid_select.place(x=10,y=10, width=240, height=230)
        self.grid_scroll = tk.Scrollbar(self.grid_select, orient="vertical")
        self.grid_scroll.configure(command=self.grid_select.yview)
        self.grid_scroll.pack(side="right", fill="y")
        self.grid_select.configure(yscrollcommand=self.grid_scroll.set)
        self.grid_confirm = ttk.Button(self.mainframe, text ="Confirm",style='button.TButton', command=lambda : self.gridconfirm())
        self.grid_confirm.place(height = 58, width = 200, x = 270, y = 182)

        tk.Label(self.mainframe,text='Graph Plotting Selection',font=('fixedsys',10)).place(height=15, width=200,x=270,y=10)
        tk.Label(self.mainframe,text='Heater Control',font=('fixedsys',10)).place(height=15, width=200,x=270,y=255)

    def heaterconfirm(self, ind):
        i = self.heater_nb.index(self.heater_nb.select())
        if ind == 1:
            heat1[i] = self.heater1_slider[i].get()
            temp = heat1[i]
        elif ind == 2:
            heat2[i] = self.heater2_slider[i].get()
            temp = heat2[i]
        self.send_cmd(i,ind,temp)

    def gridconfirm(self):
        grid_selection = self.grid_select.curselection()
        mf.rd.datapoints = []
        for i in grid_selection:
            curr_string = self.grid_select.get(i)
            mf.rd.datapoints.append(int(curr_string[5:8]))
        print(mf.rd.datapoints)

    def send_cmd(self,ind,ind2,temp):
        try:
            if (2*ind+ind2) < 10:
                output = '0'+str(2*ind+ind2-1)+ ' ' +str(temp)+'\n'
            else:
                output = str(2*ind+ind2-1)+ ' ' +str(temp)+'\n'
            serial3.write(output.encode('ascii'))
        except Exception as e:
            errorlist.append('{}'.format(sys.exc_info()[-1].tb_lineno))
            errorlist.append(e)
            errorlist.append('---')
        

class ReceiveData():
    def __init__(self):
        self.rec_data1_1 = np.array([[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]], np.float32)
        self.rec_data2_1 = np.array([[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]], np.float32)
        self.rec_data1_2 = np.array([[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]], np.int32)
        self.rec_data2_2 = np.array([[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]], np.int32)
        self.time_ind = 0
        self.time_ind_1 = 0
        self.time_ind_2 = 0
        self.datapoints = [1,2,3,4,5,6]
        
    def updateAll(self):
        if mf.state1 == 1 or mf.state2 == 1:
            mf.update_table()
            if mf.state1 == 1:
                self.rec_data1_1 = np.insert(self.rec_data1_1, self.time_ind_1, serial_data1[0:36], axis=1)
                self.rec_data1_2 = np.insert(self.rec_data1_2, self.time_ind_1, self.time_ind)
                self.time_ind_1 += 1
            if mf.state2 == 1:
                self.rec_data2_1 = np.insert(self.rec_data2_1, self.time_ind_2, serial_data2[0:36], axis=1)
                self.rec_data2_2 = np.insert(self.rec_data2_2, self.time_ind_2, self.time_ind)
                self.time_ind_2 += 1
            self.time_ind += 1
            
            if (self.time_ind%5)==0 or self.time_ind==0:
                if mf.state1 == 1:
                    mf.updategraphs(1,self.datapoints)
                if mf.state2 == 1:
                    mf.updategraphs(2,self.datapoints)
                    mf.update_LEDs()
                
        root.after(1000,self.updateAll)
            
# Main Window
root = tk.Tk()
root.geometry("1600x900")
root.resizable(width=False, height=False)
root.title('Reference Data Monitor')

# Style definitions
s = ttk.Style()
s.configure('main.TFrame',background = 'grey',relief='sunken')
s.configure('second.TFrame',background = 'lightgrey',relief='flat')
s.configure('graph.TFrame',background = 'lightgrey',relief='sunken')
s.configure('table.TFrame')
s.configure('controls.TFrame',background = 'lightgrey')
s.configure('button.TButton',background = 'darkgrey',relief='raised')
s.configure('off.TFrame',background='brown2',relief='raised')
s.configure('on.TFrame',background='green3',relief='raised')
s.configure('error.TFrame',background='orange',relief='raised')
s.configure('disabled.TFrame',background='grey63',relief='raised')
s.configure('toohot.TFrame',background='orangered3',relief='raised')
s.configure('toocold.TFrame',background='dodgerblue3',relief='raised')

# Frame creations
mf = MonitorFrame(root)


# ----- Thread initialization ----------------------------------------------------------------------------------------------------------------------------------------------

thr1 = threading.Thread(target=seriallisten)
thr1.start()

root.after(2000,mf.rd.updateAll)
root.mainloop()
