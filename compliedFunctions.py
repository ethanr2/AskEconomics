# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 08:18:10 2019

@author: ethan
"""
import math
import os
from datetime import datetime as dt
from datetime import timedelta as td
import praw
import numpy as np
import pandas as pd

# Global variables

df = pd.read_pickle('data/fullDataBase.pkl')
creds = pd.read_csv('credentials.csv').T.to_dict()[0]
reddit = praw.Reddit(**creds)
print(df.shape)

def getMods():
    red = []
    yel = []
    for mod in reddit.subreddit('AskEconomics').moderator():
        if mod.mod_permissions[0] == 'all': 
            red.append(mod.name)
        else: 
            yel.append(mod.name) 
    return red,yel

# Don't use this unless the fullDataBase.pkl file gets messed up in some way.
def complieAllCSVs():
    files = ['data/' + file for file in os.listdir('data') if file.endswith('.csv')]
    df = pd.read_csv('data\modlog_2019-06-02.csv',index_col = 0)
    df['Time'] = pd.to_datetime(df['Time'])
    end = df['Time'].max()
    start = df['Time'].min()
                   
    for file in files:
        df2 = pd.read_csv(file,index_col = 0)
        df2['Time'] = pd.to_datetime(df2['Time'])
        df2 = df2.loc[(df2['Time'] > end) | (df2['Time'] < start), :]
        df = df.append(df2, ignore_index = True,sort=False).sort_values('Time')
        end = df['Time'].max()
        start = df['Time'].min()
        print( df['Time'].min(), df['Time'].max(), file)
        #break
    df.to_pickle('data/fullDataBase.pkl')
    return df

def newQuery(limit=9000):
    mod = []
    action = []
    time = []
    ids = []
    body = []
    end = df['Time'].max()
    
    for log in reddit.subreddit('AskEconomics').mod.log( limit=limit):
        
        #print("{} - Mod: {}, Action: {}, Time: {}".format(i,log.mod,log.action, dt.utcfromtimestamp(log.created_utc)))
        mod.append(log.mod)
        action.append(log.action)
        time.append(dt.utcfromtimestamp(log.created_utc))
        if log.target_fullname == None:
            ids.append(None)
            body.append(None)
        else:
            ids.append(log.target_fullname)
            body.append(log.target_body)
        
        print(time[-1],log.mod)
        if time[-1] < end:
            break

    temp = pd.DataFrame({
            'Mod': mod,
            'Action': action,
            'Time': time,
            'ID': ids,
            'Body': body
            })
    print('Query Done: ')
    print(temp)
    name = 'data\modlog_' + str(dt.now())[:10] + '.csv'
    temp.to_csv(name)
    appendCSV(name)

def appendCSV(name):
    global df
    end = df['Time'].max()
    start = df['Time'].min()
    
    df2 = pd.read_csv(name,index_col = 0)
    df2['Time'] = pd.to_datetime(df2['Time'])
    df2 = df2.loc[(df2['Time'] > end) | (df2['Time'] < start), :]
    df = df.append(df2, ignore_index = True,sort=True)
    
    df.to_pickle('data/fullDataBase.pkl')
    return df

def filterActions(start = None):
    filt = lambda x: x == 'approvecomment' or x == 'removecomment'
    bools = df['Action'].apply(filt)
    newDF = df.loc[bools,:]
    if start != None:
        newDF = newDF.loc[newDF['Time'] > start,:]
    return newDF

def modShareDF(limit = .01, start = None):
    data = filterActions(start)
    
    g = data.groupby('Mod')
    agg = g.agg(np.size).sort_values('Action', ascending = False).iloc[1:,:]
    agg = agg/agg['Action'].sum()
    
    red, yel = getMods()
    
    def colorcode(x):
        if x in red: return 'red'
        return 'yellow'
    agg['color'] = agg.index.to_series().apply(colorcode)
    agg = agg.loc[agg['Action'] > .01, ['Action','color']]
    agg['Action'] = agg['Action']/agg['Action'].sum()
    
    return agg

def makeBarChart(data, start = None):
    from bokeh.io import show, output_file
    from bokeh.plotting import figure
    from bokeh.models import NumeralTickFormatter
    output_file('imgs/' + str(dt.now())[:10]+ "_bars.html")
    
    agg = modShareDF(start = start)
    mods = agg.index.tolist()
    shares = agg['Action']
    
    if start == None:
        start = data['Time'].min().date() 
    else:
        start = start.date()
    end = data['Time'].max().date()
    p = figure(x_range = mods, plot_width = 1256, 
               title="/r/AskEconomics Moderator Activity: {} to {}".format(start, end), 
               x_axis_label = 'Moderator', y_axis_label = 'Share of Mod Actions')
    
    p.vbar(x = mods,color = agg['color'], width = .9, top = shares)
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.xaxis.major_label_orientation = math.pi/4
    
    p.yaxis.formatter=NumeralTickFormatter(format="0.0%")
    show(p)
    print('done')

start = dt.now() - td(days = 90)
makeBarChart(df, start = start)