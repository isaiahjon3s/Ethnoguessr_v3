# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 10:44:57 2018

@author: Jan Jezersek
"""
import os
import sqlite3
from wtforms import Form, TextField, PasswordField, validators
import ast

import os
path = os.getcwd()

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
    validators.Required(),
    validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    
def populate_pictures(path):
#    dir = os.path.dirname(__file__)
    dir = path
    
    with open(os.path.join(dir, 'pictures.txt'),'r') as f:
        pics = f.readlines()
        
    pics2 = []
    
    for i in range(0,16,2):
        pics2.append((pics[i][:-1],pics[i+1][:-1],1))
            
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.executemany("INSERT INTO pictures (link,coordinates,show_in_continuous) VALUES (?,?,?)",pics2)
    
#    for i in range(0,len(pics),2):
#        c.execute("INSERT INTO pictures (link,coordinates,show_in_continuous) VALUES ('{0}','{1}',1)".format(pics[i][:-1],pics[i+1][:-1]))
        
    conn.commit()
    conn.close()
        
    
def create_challenge(chnum,filename,path,show_in_continuous=0):
    dir = path
    
    with open(os.path.join(dir, filename),'r') as f:
        chdata = f.readlines()
        
    chdata2 = []
    
    for i in range(0,len(chdata),2):
        chdata2.append([chdata[i][:-1],chdata[i+1][:-1]])
    
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.execute("CREATE TABLE challenge{0} (ROUND INTEGER NOT NULL,PICTUREID INTEGER NOT NULL)".format(chnum))
    c.execute("CREATE TABLE challenge{0}_results (USERNAME TEXT NOT NULL,ROUND INTEGER NOT NULL,SCORE INTEGER NOT NULL,GUESSED TEXT,CORRECT TEXT NOT NULL)".format(chnum))
    c.execute("CREATE TABLE challenge{0}_leaderboard (USERNAME TEXT NOT NULL,CUM_SCORE INTEGER NOT NULL)".format(chnum))
    
    for i in range(len(chdata2)):
        c.execute("INSERT INTO pictures (link,coordinates,show_in_continuous) VALUES ('{0}','{1}',{2})".format(chdata2[i][0],chdata2[i][1],show_in_continuous))
        print(chdata2[i][0],chdata2[i][1],show_in_continuous)
        c.execute("SELECT id FROM pictures WHERE link = '{}'".format(chdata2[i][0]))
        picID = c.fetchall()
        print(picID)
        c.execute("INSERT INTO challenge{0} (round,pictureid) VALUES ({1},{2})".format(chnum,i,picID[0][0]))
        
    c.execute("INSERT INTO challenges (chnum,rounds) VALUES ('{0}',{1})".format(chnum,len(chdata2)))
      
    conn.commit()
    conn.close()
    
def coordinates_f(a,b):
    return '{"lat": ' + str(a) + ',"lng": ' + str(b) + '}'

def link_validator(link):
    if link[:18] == "https://imgur.com/":
        return 1
    else:
        return 0
    
def challenge_validator(data):   
    try:
        for i in range(len(data)):
            coordinates = ast.literal_eval(data[i][1])
            if not(str(data[i][0][:8]) == "https://" or str(data[i][0][:7]) == "http://"):
                return 1,i
            elif coordinates['lat'] < -90 or coordinates['lat'] > 90 or coordinates['lng'] < -180 or coordinates['lng'] > 180:
                return 2,i
        return 0,i
    except:
        return 3,i
    
def create_tables(path):
    dir = path
            
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.execute("CREATE TABLE pictures (ID INTEGER PRIMARY KEY AUTOINCREMENT,LINK TEXT NOT NULL,COORDINATES TEXT NOT NULL,SHOW_IN_CONTINUOUS INTEGER NOT NULL);")
    c.execute("CREATE TABLE users (ID INTEGER PRIMARY KEY AUTOINCREMENT,USERNAME TEXT NOT NULL,PASSWORD TEXT NOT NULL,EMAIL TEXT,CONFIRMED INTEGER NOT NULL);")
    c.execute("CREATE TABLE leaderboard (USERNAME TEXT NOT NULL,N_GAMES INTEGER NOT NULL,CUM_SCORE INTEGER NOT NULL,AVG_SCORE DOUBLE NOT NULL);")
    c.execute("CREATE TABLE challenges (CHNUM TEXT NOT NULL,ROUNDS INTEGER NOT NULL);")
    c.execute("CREATE TABLE challenge_states (CHNUM TEXT NOT NULL,USERNAME TEXT NOT NULL,CURRENT_ROUND INTEGER NOT NULL,FINISHED INTEGER NOT NULL,CURRENT_SCORE INTEGER NOT NULL);")
    
    conn.commit()
    conn.close()
            
    

        
    
    