# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 10:44:57 2018

@author: Jan Jezersek
"""
import os
#import sqlite3
from wtforms import Form, TextField, PasswordField, validators
import ast
import psycopg2
import os
import auth

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
            
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
    c.executemany("INSERT INTO pictures (link,coordinates,show_in_continuous) VALUES (%s,%s,%s)",pics2)
    
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
    
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
#    c.execute("CREATE TABLE challenge{0} (ROUND INTEGER NOT NULL,PICTUREID INTEGER NOT NULL)".format(chnum))
#    c.execute("CREATE TABLE challenge{0}_results (USERNAME TEXT NOT NULL,ROUND INTEGER NOT NULL,SCORE INTEGER NOT NULL,GUESSED TEXT,CORRECT TEXT NOT NULL)".format(chnum))
#    c.execute("CREATE TABLE challenge{0}_leaderboard (USERNAME TEXT NOT NULL,CUM_SCORE INTEGER NOT NULL)".format(chnum))
    
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

def create_test_challenge():
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
    ids_of_pics = [1,3,4,5]
    chnum = "Test"
    
    c.execute("INSERT INTO challenges (chnum) VALUES (%s)",[chnum])
    
    for i in range(len(ids_of_pics)):
        c.execute("INSERT INTO picture_challenge (round,pictureid,challengeid) VALUES (%s,%s,1)",[i+1,ids_of_pics[i]])
    
    conn.commit()
    conn.close()

    
    
def create_tables(path):
    dir = path
            
    #conn = psycopg2.connect(os.path.join(dir, 'database.db'))
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
#    c.execute("CREATE TABLE pictures (ID INTEGER PRIMARY KEY AUTOINCREMENT,LINK TEXT NOT NULL,COORDINATES TEXT NOT NULL,SHOW_IN_CONTINUOUS INTEGER NOT NULL);")
#    c.execute("CREATE TABLE users (ID INTEGER PRIMARY KEY AUTOINCREMENT,USERNAME TEXT NOT NULL,PASSWORD TEXT NOT NULL,EMAIL TEXT,CONFIRMED INTEGER NOT NULL);")
#    c.execute("CREATE TABLE leaderboard (USERNAME TEXT NOT NULL,N_GAMES INTEGER NOT NULL,CUM_SCORE INTEGER NOT NULL,AVG_SCORE DOUBLE NOT NULL);")
#    c.execute("CREATE TABLE challenges (CHNUM TEXT NOT NULL,ROUNDS INTEGER NOT NULL);")
#    c.execute("CREATE TABLE challenge_states (CHNUM TEXT NOT NULL,USERNAME TEXT NOT NULL,CURRENT_ROUND INTEGER NOT NULL,FINISHED INTEGER NOT NULL,CURRENT_SCORE INTEGER NOT NULL);")
    
#    c.execute("CREATE TABLE pictures (ID SERIAL PRIMARY KEY,LINK TEXT NOT NULL,COORDINATES TEXT NOT NULL,SHOW_IN_CONTINUOUS INTEGER NOT NULL);")
#    c.execute("CREATE TABLE users (ID SERIAL PRIMARY KEY,USERNAME TEXT NOT NULL,PASSWORD TEXT NOT NULL,EMAIL TEXT,CONFIRMED INTEGER NOT NULL,NGAMES INTEGER NOT NULL,CUM_SCORE INTEGER NOT NULL);")
#    c.execute("CREATE TABLE challenges (ID SERIAL PRIMARY KEY,CHNUM TEXT NOT NULL);")
    
    #Relacije
    c.execute("CREATE TABLE picture_challenge (ID SERIAL PRIMARY KEY,ROUND INTEGER NOT NULL,PICTUREID INTEGER REFERENCES pictures(id),CHALLENGEID INTEGER REFERENCES challenges(id));")
    c.execute("CREATE TABLE user_challenge (ID SERIAL PRIMARY KEY,FINISHED_ROUNDS INTEGER NOT NULL,SCORE INTEGER NOT NULL, USERID INTEGER REFERENCES users(id), CHALLENGEID INTEGER REFERENCES challenges(id));")
    
    
    conn.commit()
    conn.close()
    
    
def drop_table():
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    c.execute("DROP TABLE user_challenge")
    c.execute("CREATE TABLE user_challenge (ID SERIAL PRIMARY KEY,FINISHED_ROUNDS INTEGER NOT NULL,SCORE INTEGER NOT NULL, USERID INTEGER REFERENCES users(id), CHALLENGEID INTEGER REFERENCES challenges(id));")
    conn.commit()
    conn.close()
    
            
    

        
    
    