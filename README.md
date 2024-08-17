# Boardgames recommendation project
## Description of the product
A boardgames information library app with an AI recommendation system based upon user reviews (ALS model). As a visitor, you can search for games via the searchbar or visit various ranking pages (Top Ranked, Top Rated, Most Popular) to look for new games. if you register as a user, you can also start giving ratings to games you know and eventually get recommendations based on your ratings for new games in your profile!

### Source

The product was made using the data from this kaggle dataset:

https://www.kaggle.com/datasets/jvanelteren/boardgamegeek-reviews

## Architecture of the code:

![Boardgames-webapp drawio](https://github.com/user-attachments/assets/488d39a8-29d9-4e1b-afd2-097710d3e5fe)

### PostgreSQL Database:

Persistent Volume: Stores tables for Boardgames, users, ratings, and recommendations.

### Web Application Deployment:

HorizontalPodAutoscaler: Starts with 2 replicas and scales up to 5.
LoadBalancer: Distributes traffic among the web app replicas.

### Kafka Deployment:

Zookeeper Pod: Manages Kafka broker coordination.
Kafka Broker Pod: Receives information from the web app (acting as a producer).

### Web-App-Analytics:

Persistent Volume: Stores processed analytics data.
Interaction with Kafka: Consumes data from Kafka for processing.

### CronJob with Spark ALS Model:

Schedule: Runs every 12 hours.
Task: Generates new recommendations based on the ratings table and updates the PostgreSQL database.

### Interaction Flow:
The web app interacts with the database for user, game, and recommendation data.
User interactions or other events are sent to Kafka by the web app.
The web-app-analytics deployment processes the Kafka messages and stores the analytics data.
The Spark CronJob updates recommendations in the PostgreSQL database every 12 hours based on the latest ratings.
This setup allows for scalable web app deployment, real-time data streaming, and periodic updates to recommendations.
