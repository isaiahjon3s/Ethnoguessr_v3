import sqlite3
from flask import jsonify
from datetime import datetime

@app.route('/daily_challenge/start')
def start_daily_challenge():
    conn = sqlite3.connect('ethnoguessr.db')
    cursor = conn.cursor()
    
    # Create a new daily challenge
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('INSERT INTO daily_challenges (DATE) VALUES (?)', (today,))
    challenge_id = cursor.lastrowid
    
    # Get a random image for the first round
    cursor.execute('SELECT id, link FROM pictures ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    
    # Store the used image ID for this challenge
    cursor.execute('INSERT INTO daily_challenge_rounds (challenge_id, round_number, picture_id) VALUES (?, ?, ?)',
                  (challenge_id, 1, result[0]))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'challenge_id': challenge_id,
        'picture_id': result[0],
        'url': result[1]
    })

@app.route('/daily_challenge/next_image')
def next_daily_challenge_image():
    conn = sqlite3.connect('ethnoguessr.db')
    cursor = conn.cursor()
    
    # Get the current challenge ID
    cursor.execute('SELECT id FROM daily_challenges ORDER BY date DESC LIMIT 1')
    challenge_id = cursor.fetchone()[0]
    
    # Get the current round number
    cursor.execute('SELECT MAX(round_number) FROM daily_challenge_rounds WHERE challenge_id = ?', (challenge_id,))
    current_round = cursor.fetchone()[0]
    
    # Get a random image that hasn't been used in this challenge
    cursor.execute('''
        SELECT p.id, p.link 
        FROM pictures p 
        WHERE p.id NOT IN (
            SELECT picture_id 
            FROM daily_challenge_rounds 
            WHERE challenge_id = ?
        )
        ORDER BY RANDOM() 
        LIMIT 1
    ''', (challenge_id,))
    result = cursor.fetchone()
    
    if result:
        # Store the used image ID for this challenge
        cursor.execute('INSERT INTO daily_challenge_rounds (challenge_id, round_number, picture_id) VALUES (?, ?, ?)',
                      (challenge_id, current_round + 1, result[0]))
        conn.commit()
    
    conn.close()
    
    return jsonify({
        'picture_id': result[0],
        'url': result[1]
    })

@app.route('/choose_image',methods=['GET'])
def choose_image():
    if request.method == 'GET':
        conn = sqlite3.connect(auth.db)
        c = conn.cursor()
        
        # Get a random image that hasn't been used in this session
        c.execute("""
            SELECT p.link, p.id 
            FROM pictures p 
            WHERE p.show_in_continuous = 1 
            AND p.id NOT IN (
                SELECT picture_id 
                FROM session_images 
                WHERE session_id = (
                    SELECT MAX(session_id) 
                    FROM session_images
                )
            )
            ORDER BY RANDOM() 
            LIMIT 1
        """)
        
        result = c.fetchone()
        if not result:
            # If all images have been used, clear the session and start fresh
            c.execute("DELETE FROM session_images")
            c.execute("SELECT link, id FROM pictures WHERE show_in_continuous = 1 ORDER BY RANDOM() LIMIT 1")
            result = c.fetchone()
        
        url, pic_id = result
        
        # Store the used image in the session
        c.execute("INSERT INTO session_images (session_id, picture_id) VALUES (?, ?)", 
                 (datetime.now().strftime('%Y%m%d%H%M%S'), pic_id))
        
        conn.commit()
        conn.close()
        
        # Add headers to allow cross-origin requests
        response = jsonify(url, pic_id)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response 