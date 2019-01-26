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
import os as os

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import style
style.use('ggplot')

import datetime as dt
import time
#---------- Functions ----------

#---------- Classes ----------
    
class MonitorFrame():
    def __init__(self,parent):
        self.mainframe = ttk.Frame(parent, style = 'main.TFrame' )
        self.mainframe.place(height=850, width=1500, x=50, y=25)
        
        self.graph1 = ttk.Frame(self.mainframe,style = 'graph.TFrame')
        self.graph1.place(height=400, width=712, x=25, y=10)
        self.graph2 = ttk.Frame(self.mainframe,style = 'graph.TFrame')
        self.graph2.place(height=400, width=715, x=763, y=10)
        
        self.datatable = ttk.Frame(self.mainframe,style = 'table.TFrame')
        self.datatable.place(height=125, width=1450, x=25, y=420)
        self.initialize_table()
        
        self.controls = ttk.Frame(self.mainframe,style = 'controls.TFrame')
        self.controls.place(height=285, width=1450, x=25, y=555)
        
        self.onoff_data1 = ttk.Button(self.controls, text = 'Toggle data1', style = 'button.TButton',command=lambda : self.togglegraph(1))
        self.onoff_data2 = ttk.Button(self.controls, text = 'Toggle data2', style = 'button.TButton',command=lambda : self.togglegraph(2))
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
        self.logview = ttk.Button(self.controls, text = 'View Logs', style = 'button.TButton')
        self.check1.place(height=58,width=200,x=500,y=10)
        self.check2.place(height=58,width=200,x=500,y=79)
        self.logview.place(height=58,width=200,x=500,y=217)
        
        ttk.Separator(self.controls, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=1, sticky='ns')
        self.controls.columnconfigure(1, weight=1)
        self.controls.columnconfigure(2, weight=1)
        self.controls.columnconfigure(3, weight=1)
        self.controls.rowconfigure(0, weight=1)
        
        self.commentbox = tk.Text(self.controls)
        self.commentbox.place(height=195,width=675,x=750,y=10)
        self.saveone = ttk.Button(self.controls, text = 'Save Once', style='button.TButton',state=tk.DISABLED)
        self.savemultiple = ttk.Button(self.controls, text = 'Save Continuously', style='button.TButton',state=tk.DISABLED)
        self.savingcont = ttk.Frame(self.controls, style = 'off.TFrame')
        self.saveone.place(height=58,width=133,x=750,y=217)
        self.savemultiple.place(height=58,width=133,x=895,y=217)
        self.savingcont.place(height=58,width=50,x=1040,y=217)
        self.filechoose = ttk.Button(self.controls, text = 'Choose Save Location', style='button.TButton', command=lambda : self.choosefile())
        self.filechoose.place(height=58,width=133,x=1292,y=217)

        self.rd = ReceiveData()
        self.creategraphs()
        self.updategraphs()

    def initialize_table(self):
        tk.Label(self.datatable,text='',font=10).grid(column=1,row=0)
        self.datatable.rowconfigure(0, weight=1)
        tk.Label(self.datatable,text='Temp 1',font=('verdana',12)).grid(column=1,row=2)
        self.datatable.rowconfigure(2, weight=1)
        tk.Label(self.datatable,text='Temp 2',font=('verdana',12)).grid(column=1,row=4)
        self.datatable.rowconfigure(4, weight=1)
        ttk.Separator(self.datatable, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=3, sticky='ns')
        self.datatable.columnconfigure(1, weight=1)
        for i in range(1,37):
            tk.Label(self.datatable,text=i,font=('verdana',12)).grid(column=i*2+1,row=0)
            tk.Label(self.datatable,text='00.0',font=('verdana',8)).grid(column=i*2+1,row=2)
            tk.Label(self.datatable,text='00.0',font=('verdana',8)).grid(column=i*2+1,row=4)
            ttk.Separator(self.datatable, orient=tk.VERTICAL).grid(column=i*2, row=0, rowspan=5, sticky='ns')
            self.datatable.columnconfigure(i*2+1, weight=1)
        ttk.Separator(self.datatable, orient=tk.HORIZONTAL).grid(column = 1, row=1, columnspan=73,sticky='we')
        ttk.Separator(self.datatable, orient=tk.HORIZONTAL).grid(column = 1, row=3, columnspan=73,sticky='we')

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
                self.tframe1 = TestFrame(self.test_window1)
                self.tframe1.runtest()
        elif ind == 2:
            try:
                self.test_window2.lift()
                self.test_window2.deiconify() 
            except:
                self.test_window2 = tk.Toplevel(root)
                self.test_window2.title('Connection Test (2)')
                self.test_window2.geometry("300x400")
                self.test_window2.resizable(width=False, height=False)
                self.tframe2 = TestFrame(self.test_window2)
                self.tframe2.runtest()

    def togglegraph(self,ind):
        if ind == 1:
            if self.state1 == 1:
                self.data1_status.configure(style='off.TFrame')
                self.state1 = 0
            else:
                self.data1_status.configure(style='on.TFrame')
                self.state1 = 1
        elif ind == 2:
            if self.state2 == 1:
                self.data2_status.configure(style='off.TFrame')
                self.state2 = 0
            else:
                self.data2_status.configure(style='on.TFrame')
                self.state2 = 1

    def choosefile(self):
        self.saveloc = askdirectory()
        if self.saveloc == '':
            self.saveloc= os.getcwd()
            print(os.getcwd())
        self.saveone.configure(state=tk.NORMAL)
        self.savemultiple.configure(state=tk.NORMAL)

    def creategraphs(self):
        self.fig1 = Figure(figsize=(20,20),dpi=100)
        self.fig1_info = self.fig1.add_subplot(111)
        self.fig2 = Figure(figsize=(20,20),dpi=100)
        self.fig2_info = self.fig2.add_subplot(111)

    def updategraphs(self):
        self.fig1_info.plot(self.rd.rec_data1[:][0],self.rd.rec_data1[:][1])
        self.canvas1 = FigureCanvasTkAgg(self.fig1, self.graph1)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand = True)
        self.fig2_info.plot(self.rd.rec_data2[:][0],self.rd.rec_data2[:][1])
        self.canvas2 = FigureCanvasTkAgg(self.fig2, self.graph2)
        self.canvas2.draw()
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand = True)
            
            

class TestFrame():
    def __init__(self,parent):
        self.mainframe = ttk.Frame(parent, style = 'second.TFrame' )
        self.mainframe.place(height=310, width=280, x=10, y=10)
        for i in range(1,11):
            self.mainframe.rowconfigure(i, weight=1)

     #--- TESTS ---
            # TODO
    def serial_test(self):
        return 0
    def connect_test(self):
        return 0
    def ADC_test(self):
        return 0
    def DAC_test(self):
        return 0
    def temp_test(self):
        return 0

    def runtest(self):
        tk.Label(self.mainframe,text='Checking Monitor Serial Input...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=1,stick='w')
        res = self.serial_test()
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=2)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato',anchor='w').grid(column=0,row=2)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=2)
            
        tk.Label(self.mainframe,text='Checking Monitor Connection...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=3,stick='w')
        res = self.connect_test()
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=4)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato').grid(column=0,row=4)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=4)

        tk.Label(self.mainframe,text='Checking MCU Input Connections...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=5,stick='w')
        res = self.ADC_test()
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=6)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato').grid(column=0,row=6)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=6)

        tk.Label(self.mainframe,text='Checking MCU Output Connections...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=7,stick='w')
        res = self.DAC_test()
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=8)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato').grid(column=0,row=8)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=8)

        tk.Label(self.mainframe,text='Checking overall system...',font=('fixedsys',12),background='lightgrey').grid(column=0,row=9,stick='w')
        res = self.temp_test()
        if res == 1:
            tk.Label(self.mainframe,text='GOOD CONNECTION',font=('fixedsys',12),background='green3').grid(column=0,row=10)
        elif res == 0:
            tk.Label(self.mainframe,text='NO CONNECTION',font=('fixedsys',12),background='tomato').grid(column=0,row=10)
        else:
            tk.Label(self.mainframe,text='ERROR - CHECK LOGS',font=('fixedsys',12),background='lightgrey').grid(column=0,row=10)

class ReceiveData():
    def __init__(self):
        self.rec_data1 = [[0],[0]]
        self.rec_data2 = [[0],[0]]

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

# Frame creations
mf = MonitorFrame(root)

print(dt.datetime.now())
print(matplotlib.dates.date2num(dt.datetime.now()))

root.mainloop()
# Main

