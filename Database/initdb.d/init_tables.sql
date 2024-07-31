-- Create the users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    password VARCHAR(255)
);


-- Create the games table
CREATE TABLE IF NOT EXISTS games (
    ID INT PRIMARY KEY,
    name VARCHAR(255),
    thumbnail TEXT,
    image TEXT,
    description TEXT,
    yearpublished FLOAT,
    minplayers FLOAT,
    maxplayers FLOAT,
    playingtime FLOAT,
    minage FLOAT,
    category TEXT[], -- Array of categories
    usersrated FLOAT,
    average FLOAT,
    bayesaverage FLOAT,
    board_game_rank FLOAT
);

-- Create the reviews table
CREATE TABLE IF NOT EXISTS reviews (
    rating FLOAT,
    ID INT,
    user_id INT,
    PRIMARY KEY (ID, user_id),
    FOREIGN KEY (ID) REFERENCES games(ID),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create the recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    user_id INT PRIMARY KEY,
    recommendation_list INT[], -- Array of game IDs
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Copy data from users_15m.csv into the users table
COPY users(user_id, username, email, password)
FROM '/docker-entrypoint-initdb.d/users_15m.csv'
DELIMITER ','
CSV HEADER;

-- Set the sequence to the next available user_id
SELECT setval('users_user_id_seq', (SELECT MAX(user_id) FROM users) + 1);

-- Copy data from game_info.csv into the games table
COPY games(ID, name, thumbnail, image, description, yearpublished, minplayers, maxplayers, playingtime, minage, category, usersrated, average, bayesaverage, board_game_rank)
FROM '/docker-entrypoint-initdb.d/game_info.csv'
DELIMITER ','
CSV HEADER;

-- Copy data from reviews_15m.csv into the reviews table
COPY reviews(rating, ID, user_id)
FROM '/docker-entrypoint-initdb.d/reviews_15m.csv'
DELIMITER ','
CSV HEADER;
