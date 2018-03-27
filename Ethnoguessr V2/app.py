from flask import Flask, render_template, request, jsonify, flash, url_for, redirect, session
from flask_mail import Mail, Message
import requests
import json
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from helper_functions import RegistrationForm, coordinates_f, create_challenge, challenge_validator
import random
import numpy as np
import os
import sqlite3
import gc
import re
from itsdangerous import URLSafeTimedSerializer
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.secret_key = '314159265358979323846'
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = 'example@gmail.com',
    MAIL_PASSWORD = 'password'
)
mail = Mail(app)

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/', methods=['POST','GET'])
def index_page():
    try:
        session['logged_in']
#        message = request.args['message']
#        print("This is the fucking message: ",message,type(message))
#        print(render_template('index.html',message=message))
        return render_template('index.html')
    except:
        session['logged_in'] = False
#        print("Fugggg")
        return render_template('index.html')
    
#    try:
#        print("Checkpoint 1")
#        message = request.args['message']
#        print("Checkpoint 2")
#    except:
#        print("Checkpoint 3")
#        message = "Other message"
#        
#    print("Checkpoint 4",message)
#    print("Checkpoint 5",render_template('index.html',message=message))
#    return render_template('index.html',message=message)
    
@app.route('/logout',methods=['POST'])
def logout():
    session['logged_in'] = False
    flash("You have successfully logged out")
    return redirect(url_for('index_page'))

@app.route('/login',methods = ['POST','GET'])
def login_page():
    try:
        if request.method == 'POST':
            dir = os.path.dirname(__file__)
            
            conn = sqlite3.connect(os.path.join(dir, 'database.db'))
            c = conn.cursor()
    
            c.execute("SELECT * FROM users WHERE username = '{}'".format(request.form['username']))
            
            data = c.fetchall()
            
            conn.close()
            
            print(data)
            
            real_password = str(data[0][2])
            confirmed = data[0][4]

            entered_password = request.form['password']

            if sha256_crypt.verify(entered_password,real_password) and confirmed:
                session['logged_in'] = True
                session['username'] = request.form['username']
                return redirect(url_for('play_mode_page'))
            else:
                print('Wrong password. Please try again.')
                error = "Wrong username or password. Please try again."
                return render_template('login.html',error=error)
        else:
            return render_template('login.html')
    except:
        error = "Wrong username or password. Please try again."
        return render_template('login.html',error=error)


@app.route('/register',methods = ['POST','GET'])
def register_page():
    try:
        form = RegistrationForm(request.form)
        
        dir = os.path.dirname(__file__)
        
        if request.method == "POST" and form.validate():
            username  = form.username.data
            email = form.email.data
            password = sha256_crypt.hash((str(form.password.data)))
            
            conn = sqlite3.connect(os.path.join(dir, 'database.db'))
            c = conn.cursor()

            x = c.execute("SELECT * FROM users WHERE username = '{0}'".format(username))
            y = c.execute("SELECT * FROM users WHERE email = '{0}'".format(email))

            if int(len(x.fetchall())) == 1 or int(len(y.fetchall())) == 1:
                flash("That username or email is already taken, please choose another")
                return render_template('register.html', form=form)

            else:
                c.execute("INSERT INTO users (username, password, email, confirmed) VALUES ('{0}', '{1}', '{2}', {3})"
                          .format(username, password, email, 0))
                
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

    except:
        flash("Something went wrong. Please, try again. Make sure you enter a valid email address")
        return redirect(url_for('register_page'))
        
@app.route('/confirm/<token>',methods = ['POST','GET'])
def confirmation(token):
    print(token)
    ts = URLSafeTimedSerializer(app.secret_key)
    email = ts.loads(token,max_age=86400)
    
    dir = os.path.dirname(__file__)
    
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    try:
        c.execute("UPDATE users SET confirmed = 1 WHERE email = '{}'".format(email))
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
        dir = os.path.dirname(__file__)
        
        conn = sqlite3.connect(os.path.join(dir, 'database.db'))
        c = conn.cursor()
        
        x = c.execute("SELECT * FROM users WHERE email = '{0}'".format(entered_email))
        
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

    dir = os.path.dirname(__file__)
    
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()

    x = c.execute("SELECT * FROM users WHERE email = '{0}'".format(email))
    
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
            
            dir = os.path.dirname(__file__)
        
            conn = sqlite3.connect(os.path.join(dir, 'database.db'))
            c = conn.cursor()
            
            c.execute("UPDATE users SET password = '{}'".format(new_password))
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
        dir = os.path.dirname(__file__)

        conn = sqlite3.connect(os.path.join(dir, 'database.db'))
        c = conn.cursor()
        
        c.execute("SELECT link,coordinates FROM pictures  WHERE show_in_continuous = 1 ORDER BY RANDOM() LIMIT 1")
        
        url,coordinates = c.fetchall()[0]
        
        conn.close()
        
        return jsonify(url,coordinates)

@app.route('/save_results',methods = ['POST'])
def save_results():
    result = request.form['score']
    dir = os.path.dirname(__file__)
    
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.execute("SELECT * FROM leaderboard WHERE username = '{}'".format(session['username']))
    
    data = c.fetchall()
    
    if len(data) == 0:
        c.execute("INSERT INTO leaderboard (username,n_games,cum_score,avg_score) VALUES ('{0}',{1},{2},{3})".format(session['username'],1,result,result))
    else:
        _,n_games,cum_score,avg_score = data[0]
        n_games = n_games + 1
        cum_score = cum_score + int(result)
        avg_score = round(float(cum_score)/n_games , 1)
                
        c.execute("UPDATE leaderboard SET n_games = {0}, cum_score = {1}, avg_score = {2} WHERE username = '{3}'".format(n_games,cum_score,avg_score,session['username']))
        
    conn.commit()
    conn.close()    
    return jsonify("success")

@app.route('/leaderboard',methods = ['GET'])
def leaderboard_page():
    dir = os.path.dirname(__file__)

    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.execute("SELECT * FROM leaderboard ORDER BY cum_score DESC")
    
    cum_users = c.fetchall()
    
    c.execute("SELECT * FROM leaderboard ORDER BY avg_score DESC")
    
    avg_users = c.fetchall()
    
    conn.close()
    
    cl = []
    al = []

    for i in range(len(cum_users)):
        cl.append([cum_users[i][0],cum_users[i][2],i+1])
        al.append([avg_users[i][0],avg_users[i][3],i+1])

    return render_template("leaderboard.html",cl=cl,al=al)

@app.route('/rank', methods=['GET'])
def rank():
    dir = os.path.dirname(__file__)

    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.execute("SELECT * FROM leaderboard ORDER BY cum_score DESC")
    
    cum_users = c.fetchall()
    
    c.execute("SELECT * FROM leaderboard ORDER BY avg_score DESC")
    
    avg_users = c.fetchall()
    
    conn.close()
    
    for i in range(len(cum_users)):
        if cum_users[i][0] == session['username']:
            rank1 = i + 1
            cum_score = cum_users[i][2]
            
        if avg_users[i][0] == session['username']:
            rank2 = i + 1
            avg_score = avg_users[i][3]
            
    return jsonify(rank1,cum_score,rank2,avg_score)

#    return jsonify(str(rank1),str(cum_score),str(rank2),str(avg_score))

@app.route('/challenge', methods=['GET'])
def challenge_page():
    if session['logged_in']:
        dir = os.path.dirname(__file__)
    
        conn = sqlite3.connect(os.path.join(dir, 'database.db'))
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
            dir = os.path.dirname(__file__)

            conn = sqlite3.connect(os.path.join(dir, 'database.db'))
            c = conn.cursor()
                        
            try:
                c.execute("SELECT current_round,finished FROM challenge_states WHERE chnum = '{0}' AND username = '{1}'".format(chnum, session['username']))
                data = c.fetchall()
                if len(data) == 0:
                    c.execute("INSERT INTO challenge_states (chnum,username,current_round,finished,current_score) VALUES ('{0}','{1}',{2},{3},{4})".format(chnum,session['username'],0,0,0))
                    c.execute("SELECT pictures.link,pictures.coordinates FROM challenge{0} INNER JOIN pictures ON challenge{0}.pictureID = pictures.ID WHERE round = {1}".format(chnum,0))
                    link,coordinates = (c.fetchall())[0]
                    conn.commit()
                    conn.close()
                    return render_template('challenge.html',photo_url=link,photo_coord=coordinates)
                else:
                    current_round,finished = data[0]
                    
                    if finished:
                        return redirect(url_for('challenge_finished',chnum=chnum))
                    else:
                        c.execute("SELECT pictures.link,pictures.coordinates FROM challenge{0} INNER JOIN pictures ON challenge{0}.pictureID = pictures.ID WHERE round = {1}".format(chnum,current_round))
                        link,coordinates = (c.fetchall())[0]
                        conn.close()
                        return render_template('challenge.html',photo_url=link,photo_coord=coordinates)
                
            except:
                return "Error"
        else:
            flash("Please log in")
            return redirect(url_for('login_page'))
    except:
        return redirect(url_for('login_page'))

@app.route('/challenge/<chnum>/photo', methods=['POST','GET'])
def next_challenge_photo(chnum):
    dir = os.path.dirname(__file__)
    
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.execute("SELECT * FROM challenge_states WHERE chnum = '{0}' AND username='{1}'".format(chnum,session['username']))
    
    challenge_data = c.fetchall()
        
    if challenge_data[0][3]:
        return redirect(url_for('challenge_finished',chnum=chnum))
        
    next_round = challenge_data[0][2] + 1
    
    c.execute("UPDATE challenge_states SET current_round = {0} WHERE chnum = '{1}' AND username='{2}'".format(next_round,chnum,session['username']))
    c.execute("SELECT pictures.link,pictures.coordinates FROM challenge{0} INNER JOIN pictures ON challenge{0}.pictureID = pictures.ID WHERE round = {1}".format(chnum,next_round))
    
    link,coordinates = (c.fetchall())[0]
    
    conn.commit()
    conn.close()
    return render_template('challenge.html',photo_url=link,photo_coord=coordinates)

@app.route('/challenge/<chnum>/save_challenge_results', methods=['POST'])
def save_challenge_results(chnum):
    result = request.form['score']
    guessed = request.form['guessed']
    correct = request.form['correct']
    
    print(guessed,correct)
    print(result)

    dir = os.path.dirname(__file__)
    
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.execute("SELECT current_round FROM challenge_states WHERE chnum = '{0}' AND username = '{1}'".format(chnum,session['username']))
    current_round = c.fetchall()[0][0]
    
    c.execute("SELECT rounds FROM challenges WHERE chnum = '{}'".format(chnum))
    no_rounds = c.fetchall()[0][0]
            
    c.execute("SELECT current_score FROM challenge_states WHERE chnum = '{0}' AND username = '{1}'".format(chnum,session['username']))
    cum_score = c.fetchall()[0][0]
    print("INB4 VISITING GANDY",cum_score,result)
    cum_score += int(result)
    
    print(current_round,no_rounds)
    
    if current_round + 1 == no_rounds:
        c.execute("UPDATE challenge_states SET finished = 1 WHERE chnum = '{0}' AND username = '{1}'".format(chnum,session['username']))
        c.execute("INSERT INTO challenge{0}_leaderboard (username,cum_score) VALUES ('{1}',{2})".format(chnum,session['username'],cum_score))
    
    c.execute("UPDATE challenge_states SET current_score = {0} WHERE chnum = '{1}' AND username = '{2}'".format(cum_score,chnum,session['username']))
    print('INSERT INTO challenge{0}_results (username,round,score,guessed,correct) VALUES ("{1}",{2},{3},"{4}","{5}")'.format(chnum,session['username'],current_round,result,guessed,correct))
    c.execute('INSERT INTO challenge{0}_results (username,round,score,guessed,correct) VALUES ("{1}",{2},{3},"{4}","{5}")'.format(chnum,session['username'],current_round,result,guessed,correct))
    conn.commit()
    conn.close()

    return jsonify('kek')

@app.route('/challenge/<chnum>/results', methods=['POST','GET'])
def challenge_finished(chnum):
    try:
        dir = os.path.dirname(__file__)
        
        conn = sqlite3.connect(os.path.join(dir, 'database.db'))
        c = conn.cursor()
        
        c.execute("SELECT * FROM challenge{0}_leaderboard ORDER BY cum_score DESC".format(chnum))
        
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
    except:
        flash("Please log in")
        return redirect(url_for('login_page'))
    
@app.route('/add_challenge', methods=['POST','GET'])
def add_challenge_page(): 
    if session['logged_in']:   
        return render_template('add_challenge.html')
    else:
        flash("Please log in")
        return redirect(url_for('login_page'))

@app.route('/add_challenge/submit',methods=['POST'])
def submit_challenge():
    if request.method == 'POST':
        try:        
            n_rounds = request.form['rounds']
            title = request.form['title']
                    
            data = []
                    
            for i in range(int(n_rounds)):
                link = request.form['link0']
                print(link)
                link = request.form['link{}'.format(i)]
                xcoordinate = request.form['xcoordinate{}'.format(i)]
                ycoordinate = request.form['ycoordinate{}'.format(i)]
                
                print("b",i)
                
                coordinates = coordinates_f(float(xcoordinate),float(ycoordinate))
    
                data.append([link,coordinates])
                
            dir = os.path.dirname(__file__)    
            
            
            with open(os.path.join(dir,'challenge{}.txt'.format(title)),'w') as f:
                for i in range(int(n_rounds)):
                    f.writelines(data[i][0] + '\n')
                    f.writelines(data[i][1] + '\n')     
            
            err,err_i = challenge_validator(data)
                        
            if err:            
                if err == 1:
                    flash("There was one or more invalid links.")
                    return render_template('add_challenge.html')
                elif err == 2:
                    flash("There were one or more invalid coordinates.")
                    return render_template('add_challenge.html')
                else:
                    flash("There was a problem with the challenge.")
                    return render_template('add_challenge.html')
                            
            create_challenge(title,os.path.join(dir,'challenge{}.txt'.format(title)))
            
            return redirect(url_for('challenge_page'))
        
        except:
            flash("There was a problem with the challenge.")
            return render_template('add_challenge.html')
    
@app.route('/challenge/<chnum>/results/individual/',methods=['POST','GET'])
def individual_results_page(chnum):
    username = request.args.get('username')
    
    dir = os.path.dirname(__file__)
    
    conn = sqlite3.connect(os.path.join(dir, 'database.db'))
    c = conn.cursor()
    
    c.execute("SELECT round,score,guessed,correct FROM challenge{0}_results WHERE username='{1}'".format(chnum,username))
    
    data = c.fetchall()
    
    for i in range(len(data)):
        data[i] = list(data[i])
        data[i][0] = data[i][0] + 1  
    
    return render_template('individual_results.html',data=data)


if __name__ == '__main__':
    app.run()
