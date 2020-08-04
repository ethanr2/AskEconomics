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
import pprint
# Global variables
pr = pprint.PrettyPrinter(indent=4)
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
    

date = dt(year = 2020, month = 6, day = 15)
#newQuery()
makeBarChart(df, date)


#%%
mods,b = getMods()
mods.extend(b)
other = ['AskEconMod','groupbot_ae', 'BainBotBeepBoop', 'jenbanim']
for mod in other:
    mods.remove(mod)

modDict = {
        'mods':mods
        }

modDict['Admin'] = [mods.pop(0)]

red = ['a_s_h_e_n',
       'BainCapitalist', 
       'smalleconomist',
       'Cutlasss',
       'MrDannyOcean',
       'DrunkenAsparagus',
       'isntanywhere',
       'Serialk'
       ]
modDict['Moderator'] = red
for mod in red:
    mods.remove(mod)

modDict['REN'] = []
for mod in reddit.subreddit('AskEconomics').moderator():
     if mod.mod_permissions[0] == 'all' and mod.name in modDict['mods']:
         modDict['REN'].append(mod.name)
         mods.remove(mod)

modDict['QualityContributor'] = modDict.pop('mods')

modDict['Other'] = other

for cat in modDict:
    names = ''
    for mod in modDict[cat]:
        names = names + '/u/' + mod + ', '
    names = names[:-2]
    print('{}: {}'.format(cat, names))
    print()
    
mods = {}
for key, value in modDict.items():
    for val in value:
        mods[val] = key
print(mods)
reddit.subreddit('AskEconomics').flair.set('BainBotBeepBoop',css_class= 'Other')
ex = ['Quality Contributor', 'Moderator', None]
texts = {
        'Moderator': 'AE Team',
        'REN': 'REN Team',
        'QualityContributor': 'Quality Contributor',
        'Other': ''
        }
#for name, css_class in mods.items():
#    mod = reddit.redditor(name)
#    flair = reddit.subreddit('AskEconomics').flair(redditor=mod).next()
#    if flair['flair_text'] in ex:       
#        reddit.subreddit('AskEconomics').flair.set(mod, texts[css_class], css_class)
#    print(name)
#    flair = reddit.subreddit('AskEconomics').flair(redditor=mod)
#    for f in flair:
#        print(f['user'], f['flair_text'])
    
#%%
#def calcGini(data):
#    data = modShareDF(data)
#    data = data.loc[data['Action'][::-1].index, :]
#    dx = 1/data['Action'].size
#    eqs = np.linspace(dx, 1, data['Action'].size)
#    cums = data['Action'].cumsum()
#    ints = (eqs - cums)*dx
#    
#    return sum(ints)
#def giniShareDF(data, limit = .01, start = None):
#    
#    g = data.groupby('Mod')
#    agg = g.agg(np.size).sort_values('Action', ascending = False).iloc[1:,:]
#    agg = agg/agg['Action'].sum()
#    
#    red, yel = getMods()
#    
#    def colorcode(x):
#        if x in red: return 'red'
#        return 'yellow'
#    agg['color'] = agg.index.to_series().apply(colorcode)
#    agg = agg.loc[agg['Action'] > .001, ['Action','color']]
#    agg['Action'] = agg['Action']/agg['Action'].sum()
#    print(agg)
#    return agg
#def makeGiniChart(wind = "30d"):
#    data = filterActions()
#    data = data.set_index('Time').sort_index()
#    print(data)
#    
#    g = data.groupby('Mod')
#    for group in g:
#        if group[0] == 'BainCapitalist':
#            print(group)
#    print()
#    #newSer = data['Action'].rolling(wind).apply(calcGini)
#    print(newSer)
#    return newSer
    
#newQuery()
start = dt.now() - td(days = 30)
#makeBarChart(df,start = start)

g = df.groupby('ID')
df = g.filter(lambda x: len(x['Action']) == 2)
temp = df['Action'] == 'approvecomment'
df['Count'] = temp.cumsum()
#g = df.grouby('ID')
#for group in g:
#    print(group)
#    break






