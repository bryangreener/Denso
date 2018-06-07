# -*- coding: utf-8 -*-
"""
Created on Fri May 25 16:14:27 2018

@author: Bryan Greener
"""

import pandas as pd
import tkinter as tk
from tkinter import ttk

df = pd.read_csv('OUAdjacency.csv', delimiter=',')

if __name__ == '__main__':
    root = tk.Tk()
    frame = tk.Frame(root)
    tree = ttk.Treeview(root)
    
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    ysb = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
    xsb = ttk.Scrollbar(root, orient=tk.HORIZONTAL, command=tree.xview)
    ysb.pack(side=tk.RIGHT, fill=tk.Y)
    xsb.pack(side=tk.BOTTOM, fill=tk.X)
    tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
    for column in df:
        ou = tree.insert("", index="end", text=column, values=column)
        for row in range(len(df[column])):
            if df[column][row] == 1:
                tree.insert(ou, index="end", text=df.columns[row], 
                            values=df.columns[row])
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    frame.pack(fill=tk.BOTH, expand=True)
    root.mainloop()