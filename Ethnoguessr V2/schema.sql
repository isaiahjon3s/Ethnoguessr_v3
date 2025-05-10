-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    confirmed BOOLEAN DEFAULT FALSE,
    ngames INTEGER DEFAULT 0,
    cum_score INTEGER DEFAULT 0
);

-- Create pictures table
CREATE TABLE pictures (
    id SERIAL PRIMARY KEY,
    link VARCHAR(255) NOT NULL,
    coordinates POINT NOT NULL,
    show_in_continuous BOOLEAN DEFAULT TRUE
);

-- Create challenges table
CREATE TABLE challenges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create picture_challenge table (for linking pictures to challenges)
CREATE TABLE picture_challenge (
    id SERIAL PRIMARY KEY,
    challengeid INTEGER REFERENCES challenges(id),
    pictureid INTEGER REFERENCES pictures(id),
    round INTEGER NOT NULL
);

-- Create user_challenge table (for tracking user progress in challenges)
CREATE TABLE user_challenge (
    id SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(id),
    challengeid INTEGER REFERENCES challenges(id),
    finished_rounds INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0
); 