from flask import Flask, render_template, request, jsonify, flash, url_for, redirect, session
from flask_mail import Mail, Message
import requests
import json
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from helper_functions import RegistrationForm, coordinates_f
import random
import numpy as np
import os
#import sqlite3
import gc
import re
from itsdangerous import URLSafeTimedSerializer
from passlib.hash import sha256_crypt
import psycopg2
import auth
import copy

app = Flask(__name__)
app.secret_key = '314159265358979323846'
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = auth.email,
    MAIL_PASSWORD = auth.email_password
)
mail = Mail(app)


@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/', methods=['POST','GET'])
def index_page():
    try:
        session['logged_in']
        return render_template('index.html')
    except:
        session['logged_in'] = False
        return render_template('index.html')
    
@app.route('/logout',methods=['POST'])
def logout():
    session['logged_in'] = False
    flash("You have successfully logged out")
    return redirect(url_for('index_page'))

@app.route('/login',methods = ['POST','GET'])
def login_page():
    try:
        if request.method == 'POST':            
            conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            c = conn.cursor()
    
            c.execute("SELECT * FROM users WHERE username = %s", [request.form['username']])
            
            data = c.fetchall()
            
            conn.close()
                        
            real_password = str(data[0][2])
            confirmed = data[0][4]

            entered_password = request.form['password']

            if sha256_crypt.verify(entered_password,real_password) and confirmed:
                session['logged_in'] = True
                session['username'] = request.form['username']
                return redirect(url_for('play_mode_page'))
            else:
                print('Wrong password. Please try again. Make sure your account is activated.')
                error = "Wrong username or password. Please try again. Make sure your account is activated."
                return render_template('login.html',error=error)
        else:
            return render_template('login.html')
    except Exception as e:
        print(e)
        error = "Wrong username or password. Please try again."
        return render_template('login.html',error=error)


@app.route('/register',methods = ['POST','GET'])
def register_page():
    try:
        form = RegistrationForm(request.form)
                
        if request.method == "POST" and form.validate():
            username  = form.username.data
            email = form.email.data
            password = sha256_crypt.hash((str(form.password.data)))
            
            conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            c = conn.cursor()
            
            c.execute("SELECT * FROM users WHERE username = %s", [username])
            x = c.fetchall()
            c.execute("SELECT * FROM users WHERE email = %s", [email])
            y = c.fetchall()
            

            if int(len(x)) == 1 or int(len(y)) == 1:
                flash("That username or email is already taken, please choose another")
                return render_template('register.html', form=form)

            else:
                c.execute("INSERT INTO users (username, password, email, confirmed, ngames, cum_score) VALUES (%s, %s, %s, %s, %s, %s)",
                          [username, password, email, 0, 0, 0])
                
                conn.commit()
                
                ts = URLSafeTimedSerializer(app.secret_key)
                token = ts.dumps(email)
                mail.send_message('Confirmation mail',
                    sender='chess.endings@gmail.com',
                    recipients=[email],
                    body="Thanks for registering on our website. Please, confirm your account by following the url: http://127.0.0.1:5000/confirm/{}".format(token)
                )
                
                c.close()
                conn.close()
                gc.collect()
                
                flash("Thanks for registering, please confirm your account!")

                session['logged_in'] = False
                session['username'] = username

                return redirect(url_for('login_page'))

        return render_template("register.html", form=form)

    except Exception as e:
        print(e)
        flash("Something went wrong. Please, try again. Make sure you enter a valid email address")
        return redirect(url_for('register_page'))
        
@app.route('/confirm/<token>',methods = ['POST','GET'])
def confirmation(token):
    print(token)
    ts = URLSafeTimedSerializer(app.secret_key)
    email = ts.loads(token,max_age=86400)
        
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
    try:
        c.execute("UPDATE users SET confirmed = 1 WHERE email = %s", [email])
        print("Confirmed successfully!")
        conn.commit()
        conn.close()
        return redirect(url_for('login_page'))
    except:
        print("Email address not in database")
        conn.close()
        flash("Email address not in database")
        return redirect(url_for('register_page'))
    
@app.route('/forgot-password', methods = ['POST','GET'])
def forgot_password_page():
    if request.method == 'POST':
        entered_email = request.form['email']           
        
        conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        c = conn.cursor()
        
        x = c.execute("SELECT * FROM users WHERE email = %s", [entered_email])
        
        if len(x.fetchall()) == 1:
            ts = URLSafeTimedSerializer(app.secret_key)
            token = ts.dumps(entered_email)
            mail.send_message('Password reset',
                sender='chess.endings@gmail.com',
                recipients=[entered_email],
                body="Password reset has been requested. Please reset your password by following the url: http://127.0.0.1:5000/reset/{} Link is valid for 1 hour.".format(token)
            )
            conn.close()
            flash("Password reset email sent")
            return redirect(url_for('login_page'))
        else:
            conn.close()
            flash("Email address not in database")
            return redirect(url_for('register_page'))
    else:
        return render_template('forgot-password.html')
    
@app.route('/reset/<token>',methods = ['POST','GET'])
def reset(token):
    ts = URLSafeTimedSerializer(app.secret_key)
    email = ts.loads(token)
    
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()

    x = c.execute("SELECT * FROM users WHERE email = %s", [email])
    
    if len(x.fetchall()) == 1:
        conn.commit()
        conn.close()
        return redirect(url_for('reset_page'))
    else:
        conn.close()
        flash("Email address not in database")
        return redirect(url_for('register_page'))
    
@app.route('/reset', methods=['POST','GET'])
def reset_page():
    if session['logged_in']:
        if request.method == 'POST':
            new_password = request.form['password']
            new_password = sha256_crypt.hash(str(new_password))
                    
            conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            c = conn.cursor()
            
            c.execute("UPDATE users SET password = %s", [new_password])
            conn.commit()
            conn.close()
            return redirect(url_for('login_page'))
        else:
            return render_template('reset.html')
    else:
        flash("Please log in")
        return redirect(url_for('login_page'))

@app.route('/play_mode', methods=['POST','GET'])
def play_mode_page():
    return render_template('play_mode.html')

@app.route('/play',methods = ['GET'])
def play_page():
    try:
        if request.method == 'GET':
            if session['logged_in']:
                return render_template("ethnoguessr.html")
            else:
                flash("Please log in")
                return redirect(url_for('login_page'))
    except:
        return redirect(url_for('login_page'))

@app.route('/choose_image',methods=['GET'])
def choose_image():
    if request.method == 'GET':
        conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        c = conn.cursor()
        
        c.execute("SELECT link,coordinates FROM pictures WHERE show_in_continuous = 1 ORDER BY RANDOM() LIMIT 1")
        
        url,coordinates = c.fetchall()[0]
        
        conn.close()
        
        return jsonify(url,coordinates)

@app.route('/save_results',methods = ['POST'])
def save_results():
    result = request.form['score']
    
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE username = %s", [session['username']])
    
    data = c.fetchall()
    
    if len(data) == 0:
        print("Error")
    else:
        _,_,_,_,_,n_games,cum_score = data[0]
        n_games = n_games + 1
        cum_score = cum_score + int(result)
                
        c.execute("UPDATE users SET ngames = %s, cum_score = %s WHERE username = %s", [n_games,cum_score,session['username']])
        
    conn.commit()
    conn.close()    
    return jsonify("success")

@app.route('/leaderboard',methods = ['GET'])
def leaderboard_page():
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
    c.execute("SELECT username,ngames,cum_score FROM users ORDER BY cum_score DESC")
    
    cum_users = c.fetchall()
            
    conn.close()
    
    cl = []
    al = []

    for i in range(len(cum_users)):
        cl.append([cum_users[i][0],cum_users[i][2],i+1])
        al.append([cum_users[i][0],float(cum_users[i][2])/cum_users[i][1],i+1])
        
    al = sorted(al,key=lambda x: x[1],reverse=True)

    return render_template("leaderboard.html",cl=cl,al=al)

@app.route('/rank', methods=['GET'])
def rank():
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
    c.execute("SELECT username,ngames,cum_score FROM users ORDER BY cum_score DESC")
    
    cum_users = c.fetchall()
    
    for i in range(len(cum_users)):
        cum_users[i] = list(cum_users[i])
        
    avg_users = copy.deepcopy(cum_users)
    
    for i in range(len(cum_users)):
        avg_users[i][2] = float(avg_users[i][2])/avg_users[i][1]
        
    avg_users = sorted(avg_users, key=lambda x: x[2], reverse=True)
    
    conn.close()
    
    for i in range(len(cum_users)):
        if cum_users[i][0] == session['username']:
            rank1 = i + 1
            cum_score = cum_users[i][2]
            
        if avg_users[i][0] == session['username']:
            rank2 = i + 1
            avg_score = avg_users[i][2]
            
    return jsonify(rank1,cum_score,rank2,avg_score)

@app.route('/challenge', methods=['GET'])
def challenge_page():
    if session['logged_in']:
    
        conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        c = conn.cursor()
        
        c.execute("SELECT * FROM challenges")
    
        challenges_list = c.fetchall()
        
        for i in range(len(challenges_list)):
            challenges_list[i] = list(challenges_list[i])
            
        challenges_list = list(reversed(challenges_list))
        
        conn.close()
    
        return render_template('challenges.html',challenges_list=challenges_list)
    else:
        flash("Please log in")
        return redirect(url_for('login_page'))

@app.route('/challenge/<chnum>', methods=['GET'])
def challenge(chnum):
    try:
        if session['logged_in']:

            conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            c = conn.cursor()
                        
            try:
                c.execute("SELECT user_challenge.finished_rounds FROM user_challenge INNER JOIN users ON user_challenge.userid=users.id WHERE users.username = %s AND challengeid = %s", [session['username'],chnum])
                data = c.fetchall()
                if len(data) == 0:
#                    c.execute("INSERT INTO challenge_states (chnum,username,current_round,finished,current_score) VALUES (%s, %s, %s, %, %s)", [chnum,session['username'],0,0,0])
#                    c.execute("SELECT pictures.link,pictures.coordinates FROM challenge%s INNER JOIN pictures ON challenge{0}.pictureID = pictures.ID WHERE round = %s", [chnum,0])
                    c.execute("SELECT id FROM users WHERE username = %s",[session['username']])
                    user_id = c.fetchall()[0][0]
                    c.execute("INSERT INTO user_challenge (finished_rounds,score,userid,challengeid) VALUES (%s, %s, %s, %s)",[0,0,user_id,chnum])
                    c.execute("SELECT pictures.link,pictures.coordinates FROM picture_challenge INNER JOIN pictures ON picture_challenge.pictureid = pictures.id WHERE picture_challenge.challengeid = %s AND picture_challenge.round = 1",[chnum])
                    link,coordinates = (c.fetchall())[0]
                    conn.commit()
                    conn.close()
                    return render_template('challenge.html',photo_url=link,photo_coord=coordinates)
                else:
                    current_round = data[0][0] + 1
                    c.execute("SELECT * FROM picture_challenge WHERE challengeid = %s",[chnum])
                    total_rounds = len(c.fetchall())
                    
                    if total_rounds + 1 == current_round:
                        return redirect(url_for('challenge_finished',chnum=chnum))
                    else:
                        c.execute("SELECT pictures.link,pictures.coordinates FROM picture_challenge INNER JOIN pictures ON picture_challenge.pictureid = pictures.id WHERE picture_challenge.challengeid = %s AND picture_challenge.round = %s",[chnum,current_round])
                        link,coordinates = (c.fetchall())[0]
                        conn.close()
                        return render_template('challenge.html',photo_url=link,photo_coord=coordinates)
                
            except Exception as e:
                print(e)
                return "Error"
        else:
            flash("Please log in")
            return redirect(url_for('login_page'))
    except:
        return redirect(url_for('login_page'))

@app.route('/challenge/<chnum>/photo', methods=['POST','GET'])
def next_challenge_photo(chnum):
    
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
    c.execute("SELECT user_challenge.finished_rounds,user_challenge.score FROM user_challenge INNER JOIN users ON user_challenge.userid=users.id WHERE users.username = %s AND challengeid = %s", [session['username'],chnum])
    data = c.fetchall()
    current_round = data[0][0]
    c.execute("SELECT pictures.link,pictures.coordinates FROM picture_challenge INNER JOIN pictures ON picture_challenge.pictureid = pictures.id WHERE picture_challenge.challengeid = %s AND picture_challenge.round = %s",[chnum,current_round])
    link,coordinates = (c.fetchall())[0]
    
    conn.commit()
    conn.close()
    return render_template('challenge.html',photo_url=link,photo_coord=coordinates)

@app.route('/challenge/<chnum>/save_challenge_results', methods=['POST'])
def save_challenge_results(chnum):
    result = request.form['score']
    guessed = request.form['guessed']
    correct = request.form['correct']
    
    conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = conn.cursor()
    
    c.execute("SELECT user_challenge.finished_rounds,user_challenge.score FROM user_challenge INNER JOIN users ON user_challenge.userid=users.id WHERE users.username = %s AND challengeid = %s", [session['username'],chnum])
    data = c.fetchall()
    current_round = data[0][0]
    cum_score = data[0][1]
    
    cum_score += int(result)
        

    c.execute("SELECT id FROM users WHERE username = %s",[session['username']])
    user_id = c.fetchall()[0][0]
    c.execute("UPDATE user_challenge SET score = %s, finished_rounds = %s WHERE challengeid = %s AND userid = %s", [cum_score,current_round + 1,chnum,user_id])
    conn.commit()
    conn.close()

    return jsonify('OK')

@app.route('/challenge/<chnum>/results', methods=['POST','GET'])
def challenge_finished(chnum):
    try:        
        conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        c = conn.cursor()
        
        c.execute("SELECT users.username,user_challenge.score FROM user_challenge INNER JOIN users ON user_challenge.userid = users.id WHERE challengeid = %s  ORDER BY score DESC", [chnum])
        
        cs = c.fetchall()
        
        conn.close()
        
        for i in range(len(cs)):
            cs[i] = list(cs[i])
            cs[i].insert(0,i+1)
            if cs[i][1] == session['username']:
                cs[i].append(1)
            else:
                cs[i].append(0)                

        return render_template("challenge_finished.html",cs=cs)
    except Exception as e:
        print(e)
        flash("Please log in")
        return redirect(url_for('login_page'))



if __name__ == '__main__':
    app.run()
