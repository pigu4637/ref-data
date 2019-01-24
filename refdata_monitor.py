#!/usr/bin/env python3
import tkinter as tk
import tkinter.ttk as ttk

#---------- Functions ----------

def initialize_table():
    
    tk.Label(datatable,text='',font=10).grid(column=1,row=0)
    datatable.rowconfigure(0, weight=1)
    tk.Label(datatable,text='Temp 1',font=('ubuntu',12)).grid(column=1,row=2)
    datatable.rowconfigure(2, weight=1)
    tk.Label(datatable,text='Temp 2',font=('ubuntu',12)).grid(column=1,row=4)
    datatable.rowconfigure(4, weight=1)
    ttk.Separator(datatable, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=3, sticky='ns')
    datatable.columnconfigure(1, weight=1)
    
    for i in range(1,37):
        tk.Label(datatable,text=i,font=('ubuntu',12)).grid(column=i*2+1,row=0)
        tk.Label(datatable,text='00.0',font=('ubuntu',8)).grid(column=i*2+1,row=2)
        tk.Label(datatable,text='00.0',font=('ubuntu',8)).grid(column=i*2+1,row=4)
        ttk.Separator(datatable, orient=tk.VERTICAL).grid(column=i*2, row=0, rowspan=5, sticky='ns')
        datatable.columnconfigure(i*2+1, weight=1)

    ttk.Separator(datatable, orient=tk.HORIZONTAL).grid(column = 1, row=1, columnspan=73,sticky='we')
    ttk.Separator(datatable, orient=tk.HORIZONTAL).grid(column = 1, row=3, columnspan=73,sticky='we')

def test_1():
    test_window = tk.Toplevel(root)
    print("test")

#---------- Window creation ----------
root = tk.Tk()
root.geometry("1600x900")
root.resizable(width=False, height=False)
root.title('Reference Data Monitor')

s = ttk.Style()
s.configure('main.TFrame',background = 'grey',relief='sunken')
s.configure('graph.TFrame',background = 'lightgrey',relief='sunken')
s.configure('table.TFrame')
s.configure('controls.TFrame',background = 'lightgrey')
s.configure('button.TButton',background = 'darkgrey',relief='raised')
s.configure('off.TFrame',background='red',relief='raised')
s.configure('on.TFrame',background='green',relief='raised')

mainframe = ttk.Frame(root, style = 'main.TFrame')
mainframe.place(height=850, width=1500, x=50, y=25)

graph1 = ttk.Frame(mainframe,style = 'graph.TFrame')
graph1.place(height=400, width=712, x=25, y=10)

graph2 = ttk.Frame(mainframe,style = 'graph.TFrame')
graph2.place(height=400, width=715, x=763, y=10)

ttk.Label(graph1, text="Graph 1", font=('ubuntu',15)).grid(row=0)
ttk.Label(graph2, text="Graph 2", font=('ubuntu',15)).grid(row=0)

datatable = ttk.Frame(mainframe,style = 'table.TFrame')
datatable.place(height=125, width=1450, x=25, y=420)
initialize_table()

controls = ttk.Frame(mainframe,style = 'controls.TFrame')
controls.place(height=285, width=1450, x=25, y=555)

onoff_data1 = ttk.Button(controls, text = 'Toggle data1', style = 'button.TButton')
onoff_data2 = ttk.Button(controls, text = 'Toggle data2', style = 'button.TButton')
onoff_data1.place(height=127,width=200,x=25,y=10)
onoff_data2.place(height=127,width=200,x=25,y=148)

data1_status = ttk.Frame(controls, style = 'off.TFrame')
data1_status.place(height=127,width = 50, x = 250, y=10)
data2_status = ttk.Frame(controls, style = 'off.TFrame')
data2_status.place(height=127,width = 50, x = 250, y=148)

print('1')
check1 = ttk.Button(controls, text = 'Test connection1', style = 'button.TButton', command=lambda : test_1())
check2 = ttk.Button(controls, text = 'Test connection2', style = 'button.TButton')
logview = ttk.Button(controls, text = 'View Logs', style = 'button.TButton')
check1.place(height=58,width=200,x=500,y=10)
check2.place(height=58,width=200,x=500,y=79)
logview.place(height=58,width=200,x=500,y=217)
print('2')

ttk.Separator(controls, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=1, sticky='ns')
controls.columnconfigure(1, weight=1)
controls.columnconfigure(2, weight=1)
controls.columnconfigure(3, weight=1)
controls.rowconfigure(0, weight=1)

commentbox = tk.Text(controls)
commentbox.place(height=195,width=675,x=750,y=10)

saveone = ttk.Button(controls, text = 'Save Once', style='button.TButton',state=tk.DISABLED)
savemultiple = ttk.Button(controls, text = 'Save Continuously', style='button.TButton',state=tk.DISABLED)
savingcont = ttk.Frame(controls, style = 'off.TFrame')
saveone.place(height=58,width=133,x=750,y=217)
savemultiple.place(height=58,width=133,x=895,y=217)
savingcont.place(height=58,width=50,x=1040,y=217)

filechoose = ttk.Button(controls, text = 'Choose Save Location', style='button.TButton')
filechoose.place(height=58,width=133,x=1292,y=217)

root.mainloop()
