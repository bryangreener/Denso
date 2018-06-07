# -*- coding: utf-8 -*-
"""
Created on Wed May 16 15:51:16 2018

@author: Bryan Greener
"""

import csv
import numpy as np
import pandas as pd
from itertools import groupby
from operator import itemgetter

#### Open CSV and read into list
with open('rg.csv', 'r') as f:
    reader = csv.reader(f)
    cl = list(reader)

temp = {}
gpos = {}
members = {}

#### Group by GPO then save into Dict of Lists by GPO Name
cl.sort(key=itemgetter(0))
for elt, items in groupby(cl, itemgetter(0)):
    temp[elt] = np.array(list(items))

#### Take GPO list and restructure for easier addressing
for gpo in temp:
    gpos[gpo] = {}
    members[gpo] = {}
    for elt, items in groupby(temp[gpo], itemgetter(2)):
        gpos[gpo][elt] = np.array(list(items))
        members[gpo][elt] = ''.join(np.array([gpos[gpo][elt][x][4] for x in 
                range(gpos[gpo][elt].shape[0])]))
#### Delete group item from innermost list
    for g in gpos[gpo]:
        gpos[gpo][g] = np.delete(gpos[gpo][g], 0, 0)

#### Find duplicate groups between gpos


df = pd.DataFrame.from_dict(members, orient='index')
# Can change this to be any group name...
duplicates = df.groupby(['BUILTIN\Administrators'])

# Store Pandas Series items
dup = []
for d in list(duplicates):
    dup.append(d[1]['BUILTIN\Administrators'])

# Output index results to file. The index is the title
# (GPO Name) of each comparison.
outf = open('duplicateGroups.txt', 'w')
outf.write("Below is a list of GPOs with duplicate \n"
           "RestrictedGroups member lists for\n"
           "the BUILTIN\Administrators group.\n"
           "\n")
for d in dup:
    if(len(d.index) > 1): # remove items with no duplicates
        outf.write("======DUPLICATES======\n")
        for i in d.index:
            outf.write("{0}\n".format(i))
        outf.write("\n")

'''
Dictionary Structure
gpos = { 
        Gpo1Key, { 
            Group1Key, [Member1,Member2,...,MemberN] 
            Group2Key, [Member1,Member2,...,MemberN]
            ...
            GroupNKey, [Member1,Member2,...,MemberN] } }
        Gpo2Key, {
            Group1Key, [Member1,Member2,...,MemberN] 
            Group2Key, [Member1,Member2,...,MemberN]
            ...
            GroupNKey, [Member1,Member2,...,MemberN] } }
        ...
        GpoNKey, {
            Group1Key, [Member1,Member2,...,MemberN] 
            Group2Key, [Member1,Member2,...,MemberN]
            ...
            GroupNKey, [Member1,Member2,...,MemberN] } }
'''