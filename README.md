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


