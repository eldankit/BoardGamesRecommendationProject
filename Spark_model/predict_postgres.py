from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, count
from pyspark.ml.recommendation import ALSModel

# PostgreSQL configuration
db_url = "jdbc:postgresql://localhost:5432/postgres"
db_properties = {
    "user": "postgres",
    "password": "mypassword",
    "driver": "org.postgresql.Driver",
    "fetchsize": "1000"  # Adjust the fetch size as needed
}

model_save_path = "models/als_model"  # Path to load the model
desired_user_id = 8853  # Replace with the desired user_id

if __name__ == "__main__":
    # Initialize SparkSession
    spark = SparkSession.builder \
        .appName("Game Recommendation") \
        .config("spark.jars", "./java_jbdc/postgresql-42.7.3.jar") \
        .getOrCreate()

    # Load the saved ALS model
    als_model = ALSModel.load(model_save_path)

    # Partitioning properties
    partition_column = "user_id"
    lower_bound = 1
    upper_bound = 15000000
    num_partitions = 10  # Adjust based on your cluster size

    # Create the DataFrame using the reviews data from PostgreSQL
    df = spark.read.jdbc(
        url=db_url,
        table="reviews",
        properties=db_properties,
        column=partition_column,
        lowerBound=lower_bound,
        upperBound=upper_bound,
        numPartitions=num_partitions
    )

    # Calculate the number of reviews per game
    game_review_counts = df.groupBy("id").agg(count("rating").alias("review_count"))

    # Filter games with 100 or more reviews
    popular_games = game_review_counts.filter(col("review_count") >= 100).select("id")

    # Get top 50 recommendations for all users
    user_recommendations = als_model.recommendForAllUsers(50)

    # Filter recommendations for the desired user_id
    user_recommendations = user_recommendations.filter(col("user_id") == desired_user_id)

    # Explode the recommendations to get a flat table
    user_recommendations = user_recommendations.withColumn("recommendation", explode(col("recommendations"))) \
                                               .select("user_id", col("recommendation.id").alias("game_id"), col("recommendation.rating").alias("predicted_rating"))

    # Join the recommendations with popular games to filter out those with less than 100 reviews
    user_filtered_recommendations = user_recommendations.join(popular_games, user_recommendations.game_id == popular_games.id, "inner") \
                                                        .select("user_id", "game_id", "predicted_rating")

    # Get the top 5 recommendations based on predicted rating
    user_top_5_recommendations = user_filtered_recommendations.orderBy(col("predicted_rating").desc()).limit(5)

    # Show the top 5 recommendations for the given user_id
    user_top_5_recommendations.show()

    spark.stop()
