from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
import requests
import json
from wtforms import Form, BooleanField, StringField, validators
from helper_functions import RegistrationForm, coordinates_f, calculate_score
import random
import numpy as np
import os
import gc
import re
import psycopg2
import auth
import copy

app = Flask(__name__)
app.secret_key = '314159265358979323846'

# Updated Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = auth.email
app.config['MAIL_PASSWORD'] = auth.email_password
app.config['MAIL_DEFAULT_SENDER'] = 'chess.endings@gmail.com'

mail = Mail(app)

@app.route('/', methods=['POST','GET'])
def index_page():
    return render_template('index.html')

@app.route('/play_mode', methods=['POST','GET'])
def play_mode_page():
    return render_template('play_mode.html')

@app.route('/play',methods = ['GET'])
def play_page():
    return render_template("ethnoguessr.html")

@app.route('/choose_image',methods=['GET'])
def choose_image():
    if request.method == 'GET':
        conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        c = conn.cursor()
        
        c.execute("SELECT link,id FROM pictures WHERE show_in_continuous = 1 ORDER BY RANDOM() LIMIT 1")
        url,pic_id = c.fetchall()[0]
        conn.close()
        return jsonify(url,pic_id)

@app.route('/save_results',methods = ['POST'])
def save_results():
    try:
        lat = request.form['lat']
        lng = request.form['lng']
        picture_id = request.form['picture_id']
    except Exception as e:
        print(e)
        
    result,correct_lat,correct_lng,dist = calculate_score(lat,lng,picture_id)
    return jsonify(result,correct_lat,correct_lng,dist)

@app.route('/leaderboard',methods = ['GET'])
def leaderboard_page():
    # Leaderboard is now anonymous or stubbed
    return render_template("leaderboard.html",cl=[],al=[])

@app.route('/challenge', methods=['GET'])
def challenge_page():
    # Challenges are now open to all, no user tracking
    return render_template('challenges.html',challenges_list=[])

@app.route('/challenge/<chnum>', methods=['GET'])
def challenge(chnum):
    # Anonymous challenge mode
    return render_template('challenge.html',photo_url=None,picture_id=None)

@app.route('/challenge/<chnum>/photo', methods=['POST','GET'])
def next_challenge_photo(chnum):
    # Anonymous challenge photo
    return render_template('challenge.html',photo_url=None,photo_coord=None)

@app.route('/challenge/<chnum>/save_challenge_results', methods=['POST'])
def save_challenge_results(chnum):
    try:
        lat = request.form['lat']
        lng = request.form['lng']
        picture_id = request.form['picture_id']
        result,correct_lat,correct_lng,dist = calculate_score(lat,lng,picture_id)
        return jsonify(result,correct_lat,correct_lng,dist)
    except Exception as e:
        print(e)

@app.route('/challenge/<chnum>/results', methods=['POST','GET'])
def challenge_finished(chnum):
    # Anonymous challenge results
    return render_template("challenge_finished.html",cs=[])

if __name__ == '__main__':
    app.run(port=5001)
