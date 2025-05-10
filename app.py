import sqlite3
from flask import jsonify
from datetime import datetime

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