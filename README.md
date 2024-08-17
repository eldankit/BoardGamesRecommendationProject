# Boardgames recommendation project
## Description of the product
A boardgames information library app with an AI recommendation system based upon user reviews (ALS model). As a visitor, you can search for games via the searchbar or visit various ranking pages (Top Ranked, Top Rated, Most Popular) to look for new games. if you register as a user, you can also start giving ratings to games you know and eventually get recommendations based on your ratings for new games in your profile!

### Source

The product was made using the data from this kaggle dataset:

https://www.kaggle.com/datasets/jvanelteren/boardgamegeek-reviews

## Architecture of the code:

![Boardgames-webapp drawio](https://github.com/user-attachments/assets/488d39a8-29d9-4e1b-afd2-097710d3e5fe)

### PostgreSQL Database:

- **Persistent Volume**: Stores tables for Boardgames, users, ratings, and recommendations.
- **Database Pod**: A PostgreSQL pod that handles the database

### Web Application Deployment:

- **HorizontalPodAutoscaler**: Starts with 2 replicas and scales up to 5.
- **LoadBalancer**: Distributes traffic among the web app replicas.

### Kafka Deployment:

- **Zookeeper Pod**: Manages Kafka broker coordination.
- **Kafka Broker Pod**: Receives information from the web app (acting as a producer).

### Web-App-Analytics:

- **Persistent Volume**: Stores processed analytics data.
- **Analytics pod**: Consumes data from Kafka for processing daily analytics.

### CronJob with Spark ALS Model:

- **Schedule**: Runs every 12 hours.
- **Task**: Generates new recommendations based on the ratings table and updates the PostgreSQL database.

### Interaction Flow:
- The web app interacts with the database for user, game, and recommendation data.
- User interactions or other events are sent to Kafka by the web app.
- The web-app-analytics deployment processes the Kafka messages and stores the analytics data.
- The Spark CronJob updates recommendations in the PostgreSQL database every 12 hours based on the latest ratings.
- This setup allows for scalable web app deployment, real-time data streaming, and periodic updates to recommendations.

## Data Processing and CSV Creation

Before populating the database tables, the original data was processed and transformed into CSV files suitable for importing. This process involved cleaning and formatting data from various sources to match the schema of our database tables.

### 1. **Games Data Processing**
- **Source**: The original game data was loaded from a CSV file named `games_detailed_info.csv`.
- **Steps**:
  1. **Dropping Unnecessary Columns**: Columns that were not needed were removed from the DataFrame.
  2. **Handling Data Types**: The `Board Game Rank` column was converted to a numeric type, with any errors coerced to `NaN`.
  3. **Selecting and Renaming Columns**: Only relevant columns were kept, and they were renamed to match the database schema (e.g., `primary` to `name`, `id` to `ID`).
  4. **Converting Categories**: The `category` column, which contained lists of categories as strings, was transformed into a PostgreSQL array format.
  5. **Merging Additional Data**: Any games that were missing from the initial DataFrame were added from another CSV file (`2020-08-19.csv`).
  6. **Saving the Processed Data**: The cleaned and formatted data was saved to a new CSV file named `game_info.csv`.

### 2. **Users and Reviews Data Processing**
- **Source**: The original reviews data was loaded from two CSV files: `bgg-19m-reviews.csv` and `bgg-15m-reviews.csv`.
- **Steps**:
  1. **Dropping Unnecessary Columns**: Columns such as `comment`, `name`, and any unnamed columns were removed from the DataFrame.
  2. **Handling Missing Data**: Rows with missing values were dropped to ensure clean data.
  3. **Mapping Users to IDs**: Unique usernames were mapped to numerical user IDs to create a `user_id` column.
  4. **Creating the Users Table**: A new DataFrame containing `user_id` and `username` columns was created. Placeholder columns for `email` and `password` were added, with `NaN` values (or placeholders) since this data was not available in the original file.
  5. **Saving the Processed Data**: The processed reviews data was saved to `reviews_19m.csv` and `reviews_15m.csv`, while the user data was saved to `users_19m.csv` and `users_15m.csv`.

This ETL (Extract, Transform, Load) process ensured that the data was clean, properly formatted, and ready to be imported into the PostgreSQL database tables.


## Database Tables Structure

The following is a description of the database tables used in this web application. These tables are created and populated during the initialization process.

### 1. `users` Table
- **Purpose**: Stores user information.
- **Columns**:
  - `user_id`: An auto-incrementing integer that uniquely identifies each user (Primary Key).
  - `username`: A string representing the username of the user.
  - `email`: A string representing the user's email address (must be unique).
  - `password`: A string representing the hashed password of the user.

### 2. `games` Table
- **Purpose**: Stores information about the board games.
- **Columns**:
  - `ID`: An integer that uniquely identifies each game (Primary Key).
  - `name`: A string representing the name of the game.
  - `thumbnail`: A text field containing a URL or path to the game's thumbnail image.
  - `image`: A text field containing a URL or path to the game's full-size image.
  - `description`: A text field with a description of the game.
  - `yearpublished`: A floating-point number indicating the year the game was published.
  - `minplayers`: A floating-point number representing the minimum number of players required for the game.
  - `maxplayers`: A floating-point number representing the maximum number of players that can play the game.
  - `playingtime`: A floating-point number indicating the average playing time of the game in minutes.
  - `minage`: A floating-point number representing the minimum recommended age to play the game.
  - `category`: An array of strings representing the categories the game belongs to.
  - `usersrated`: A floating-point number representing the total number of users who have rated the game.
  - `average`: A floating-point number representing the average rating of the game.
  - `bayesaverage`: A floating-point number representing the Bayesian average rating of the game.
  - `board_game_rank`: A floating-point number representing the overall rank of the game.

### 3. `reviews` Table
- **Purpose**: Stores user reviews and ratings for games.
- **Columns**:
  - `rating`: A floating-point number representing the rating a user has given to a game.
  - `ID`: An integer representing the game being rated (Foreign Key referencing `games(ID)`).
  - `user_id`: An integer representing the user who provided the rating (Foreign Key referencing `users(user_id)`).
- **Primary Key**: The combination of `ID` and `user_id` ensures that each user can only rate a game once.

### 4. `recommendations` Table
- **Purpose**: Stores personalized game recommendations for each user.
- **Columns**:
  - `user_id`: An integer that uniquely identifies each user (Primary Key, Foreign Key referencing `users(user_id)`).
  - `recommendation_list`: An array of integers representing the IDs of recommended games for the user (Foreign Key referencing `games(ID)`).

### Data Import
- **CSV Imports**: 
  - User data is imported from `users_15m.csv` into the `users` table.
  - Game data is imported from `game_info.csv` into the `games` table.
  - Review data is imported from `reviews_15m.csv` into the `reviews` table.

- **Sequence Adjustment**: 
  - After importing data into the `users` table, the sequence for `user_id` is adjusted to start at the next available ID to ensure proper auto-incrementation.

This table structure provides a robust foundation for managing users, games, reviews, and recommendations within the application.


## Web Application Pages and Features

### 1. Home Page (`/`)
- **Description**: This is the welcome page of your web application. It serves as the landing page for users when they first visit the site.
- **Features**: The page has a simple design and likely includes a welcome message and navigation options to explore other parts of the site.

### 2. Search Page (`/search`)
- **Description**: This page allows users to search for board games by name.
- **Features**: Users can enter a query in the search bar, and the page returns a list of games that match the search term. If no search term is entered, an empty result set is shown.

### 3. Top Ranked Games Page (`/top-ranked-games`)
- **Description**: Displays a list of the top-ranked board games, ordered by their `board_game_rank`.
- **Features**: The page includes pagination, showing 10 games per page. Users can navigate through the pages using "Next" and "Previous" buttons.

### 4. Top Rated Games Page (`/top-rated-games`)
- **Description**: Shows the top-rated games based on user ratings.
- **Features**: Similar to the top-ranked games page, it includes pagination, with 10 games per page, ordered by average rating in descending order.

### 5. Most Popular Games Page (`/most-popular-games`)
- **Description**: Displays the most popular games, ordered by the number of users who rated them (`usersrated`).
- **Features**: This page also includes pagination, showing 10 games per page, with the ability to navigate to other pages.

### 6. Game Detail Page (`/game/<int:id>`)
- **Description**: This page provides detailed information about a specific game, identified by its ID.
- **Features**: Users can view the game's details, such as its name, description, image, and user ratings. If the user is logged in, they can see their rating for the game. A Kafka event is sent every time this page is viewed, recording the event in the analytics pipeline.

### 7. User Registration Page (`/register`)
- **Description**: Allows new users to create an account on the site.
- **Features**: Users can register by providing a username, email, and password. Upon successful registration, a Kafka event is sent, and the user is logged in and redirected to the home page.

### 8. User Login Page (`/login`)
- **Description**: Enables existing users to log into their accounts.
- **Features**: Users enter their email and password to log in. If the credentials are incorrect, an error message is shown. Successful login redirects the user to the home page.

### 9. User Logout (`/logout`)
- **Description**: Logs the user out of their account.
- **Features**: This route is protected and requires the user to be logged in. After logging out, the user is redirected to the home page.

### 10. User Profile Page (`/profile`)
- **Description**: Displays the user's profile information, including their rated games and personalized game recommendations.
- **Features**: The page shows the user's username and email, followed by a list of games they've rated, with pagination for navigating through the ratings. It also displays up to 5 recommended games based on the latest recommendation model.

### 11. Rate Game (`/rate_game/<int:game_id>`)
- **Description**: Allows logged-in users to rate a specific game.
- **Features**: Users can submit a rating for a game, which updates the game's average rating and the number of users who rated it. The rating is stored in the `reviews` table, and the user is redirected back to the game detail page with a success message.

## Spark CronJob: Recommendation Model Update

### Overview
Every 12 hours, a Spark CronJob is triggered to update the game recommendations for each user based on their ratings. This process involves training a machine learning model using the Alternating Least Squares (ALS) algorithm and generating a list of recommended games for each user. The recommendations are then stored in the `recommendations` table in the PostgreSQL database.

### Detailed Process

1. **SparkSession Initialization**:
   - A SparkSession is created to handle the distributed data processing tasks.

2. **Data Loading from PostgreSQL**:
   - The job connects to the PostgreSQL database and loads the `reviews` data into a Spark DataFrame. The reviews data includes user ratings for various games.

3. **Data Partitioning**:
   - The data is partitioned based on the `user_id` column to optimize performance, particularly when working with large datasets.

4. **Data Splitting**:
   - The reviews data is split into training (80%) and test (20%) datasets to train and evaluate the model.

5. **Model Training**:
   - An ALS model is trained on the training data using predefined parameters (`rank`, `regParam`, `maxIter`). ALS is a popular collaborative filtering algorithm used for building recommendation systems.

6. **Model Evaluation**:
   - The trained model is evaluated using the test data, and the Root Mean Square Error (RMSE) is calculated to assess the accuracy of the predictions.

7. **Generating Recommendations**:
   - The model generates the top 50 game recommendations for each user.
   - A filter is applied to consider only games with more than 100 reviews to ensure the recommendations are based on well-reviewed games.

8. **Exploding and Filtering Recommendations**:
   - The recommendations are exploded into individual entries, and each recommendation is filtered by joining with the list of popular games.

9. **Selecting Top 5 Recommendations**:
   - From the filtered recommendations, the top 5 games are selected for each user.

10. **Storing Recommendations in PostgreSQL**:
    - The final list of top 5 recommendations for each user is written back to the `recommendations` table in PostgreSQL, overwriting any existing data.

11. **Completion**:
    - The SparkSession is stopped, and the process ends with a confirmation message indicating that the recommendations have been successfully updated.

### Purpose
This automated process ensures that each user receives personalized game recommendations based on the latest ratings. By running every 12 hours, the system adapts to new user ratings and updates the recommendations accordingly, providing users with up-to-date and relevant suggestions.

## Analytics Processing and Documentation

### Overview
The analytics code is responsible for collecting and processing events generated by the web application, such as user registrations and game views. This data is consumed from a Kafka topic and used to generate daily analytics, which are saved as JSON files.

### Detailed Process

1. **Kafka Consumer Initialization**:
   - The analytics system uses a Kafka consumer to subscribe to the `user-events` topic, which receives events generated by the web application.
   - The consumer is configured to start reading from the earliest available message, ensuring that all events are processed, even if the system is restarted.

2. **Event Processing**:
   - The code enters a loop where it continuously polls the Kafka topic for new messages.
   - When a message is received, it is parsed from JSON format into a Python dictionary.
   - The type of event is determined by the `event` field, which can be either `user_created` (indicating a new user registration) or `game_viewed` (indicating that a user has viewed a game).

3. **Counting Events**:
   - **User Registrations**: The system maintains a daily count of new user registrations. Each time a `user_created` event is received, the count for the current date is incremented.
   - **Game Views**: Similarly, the system tracks how many times each game is viewed on a daily basis. When a `game_viewed` event is received, the view count for the specific game is incremented.

4. **Daily Analytics and Data Reset**:
   - The system checks if the date has changed with each loop iteration. If a new day has started, the current counts (for user registrations and game views) are saved to a JSON file named `analytics_<date>.json`.
   - After saving the daily analytics, the counts are reset to start collecting data for the new day.

5. **Signal Handling**:
   - The system is designed to handle termination signals (such as SIGINT or SIGTERM) gracefully. When such a signal is received, the consumer is closed properly, ensuring that no data is lost.

6. **Output and Documentation**:
   - The daily analytics data is saved in JSON format, with each file containing:
     - The date the data was collected.
     - A dictionary of user registration counts, keyed by date.
     - A dictionary of game view counts, keyed by game ID.
   - These JSON files serve as a record of user activity on the site and can be used for further analysis or reporting.

### Purpose
This analytics system provides an automated way to track user engagement with the web application. By documenting daily user registrations and game views, the system enables the analysis of user behavior over time, which can be valuable for understanding trends, improving user experience, and making data-driven decisions.



