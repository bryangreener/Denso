from tkinter import ttk
from tkinter.ttk import Progressbar
from tkinter import *
from tkinter.filedialog import askdirectory
import time
import threading
import os

class App:
    def __init__(self, root, maximum):
        self.root = root
        self.maximum = maximum
        self.variable_progress = IntVar()
        self.bin_folder = None
        self.out_folder = None
    
    def get_bin(self):
        global bf
        Tk().withdraw()
        dirname = askdirectory(initialdir=os.getcwd(), title='Select Folder')
        in_var.set(dirname)
        
    def get_out(self):
        global bf
        Tk().withdraw()
        dirname = askdirectory(initialdir=os.getcwd(), title='Select Folder')
        out_var.set(dirname)
    
    def build_frame(self, status, name):
        self.root.wm_title('GPO Report Compare Tool')
        
        # ===========
        # INPUT FRAME
        # ===========
        self.frame = LabelFrame(self.root)
        self.frame.grid(row=0, columnspan=7, sticky='W', padx=5, pady=5, ipadx=5, ipady=5)
        
        self.in_label = Label(self.frame, text='Bin Folder:')
        self.in_label.grid(row=0, column=0, sticky='E', padx=5, pady=2)
        
        self.in_button = Button(self.frame, text='Browse ...', command=self.get_bin)
        self.in_button.grid(row=0, column=8, sticky='W', padx=5, pady=2)
        
        self.text = status
        self.in_var = StringVar(self.root)
        self.in_var.set(self.text)
        
        self.in_text = Entry(self.frame, textvariable=self.in_var)
        self.in_text.grid(row=0, column=1, columnspan=7, sticky='WE', pady=3)
        
        self.out_label = Label(self.frame, text='Out Folder:')
        self.out_label.grid(row=1, column=0, sticky='E', padx=5, pady=2)
    
        self.out_button = Button(self.frame, text='Browse ...', command=self.get_out)
        self.out_button.grid(row=1, column=8, sticky='W', padx=5, pady=2)
    
        self.text = status
        self.out_var = StringVar(self.root)
        self.out_var.set(self.text)
    
        self.out_text = Entry(self.frame, textvariable=self.out_var)
        self.out_text.grid(row=1, column=1, columnspan=7, sticky='WE', pady=2)
        
        # ============
        # SUBMIT FRAME
        # ============
        self.submit_frame = LabelFrame(self.root)
        self.submit_frame.grid(row=1, columnspan=7, sticky='W', padx=5, pady=5, ipadx=5, ipady=5)
        
        self.submit_button = Button(self.submit_frame, text='Compare', command=self.start_app)
        self.submit_button.grid(row=0, column=0, sticky='W', padx=5, pady=2)
        
        self.progress = ttk.Progressbar(self.submit_frame, variable=self.variable_progress, maximum=self.maximum)
        self.progress.grid(row=0, column=1, sticky='W', padx=5, pady=5)
        return self.in_text, self.out_text, self.in_var, self.out_var
    
    def start_app(self):
        

if __name__ == '__main__':
    root = Tk()
    gui = App(root, 100)
    in_dir, out_dir, in_var, out_var = gui.build_frame('', 'Directory')
    root.mainloop()