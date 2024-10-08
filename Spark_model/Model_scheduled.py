import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, count, collect_list, slice
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from apscheduler.schedulers.blocking import BlockingScheduler

# PostgreSQL configuration
db_url = "jdbc:postgresql://postgresql:5432/postgres"
db_properties = {
    "user": "postgres",
    "password": "mypassword",
    "driver": "org.postgresql.Driver",
    "fetchsize": "1000"  # Adjust the fetch size as needed
}

# URL of the PostgreSQL JDBC .jar file
jdbc_jar_url = "https://jdbc.postgresql.org/download/postgresql-42.7.3.jar"

# Function to perform the recommendation update
def update_recommendations():
    # Initialize SparkSession
    spark = SparkSession.builder \
        .appName("Game Recommendation") \
        .config("spark.jars", jdbc_jar_url) \
        .getOrCreate()

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

    # Print the first 5 rows of the DataFrame
    df.show(5)

    # Split data into training and test sets (80% train, 20% test)
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)

    best_params = {"rank": 10, "regParam": 0.1, "maxIter": 30}

    # Build the ALS model with the best parameters
    als = ALS(
        userCol="user_id",
        itemCol="id",
        ratingCol="rating",
        rank=best_params["rank"],
        regParam=best_params["regParam"],
        maxIter=best_params["maxIter"],
        coldStartStrategy="drop"  # Drop NaN predictions
    )

    # Train the ALS model on the training data
    als_model = als.fit(train_data)

    # Save the model
    # als_model.save(model_save_path)

    # Make predictions on the test data
    predictions = als_model.transform(test_data)

    # Evaluate the model by computing RMSE
    evaluator = RegressionEvaluator(
        metricName="rmse",
        labelCol="rating",
        predictionCol="prediction"
    )

    rmse = evaluator.evaluate(predictions)
    print(f"Root-mean-square error = {rmse}")
    
    # Get top 50 recommendations for all users
    user_recommendations = als_model.recommendForAllUsers(50)
    
    # Count the number of reviews for each game
    game_review_counts = df.groupBy("id").agg(count("rating").alias("review_count"))
    
    # Filter games with more than 100 reviews
    popular_games = game_review_counts.filter(col("review_count") > 100)
    
    # Explode the recommendations array
    exploded_recommendations = user_recommendations \
        .withColumn("recommendation", explode("recommendations")) \
        .select("user_id", col("recommendation.id").alias("game_id"))

    # Join exploded recommendations with popular games
    filtered_recommendations = exploded_recommendations \
        .join(popular_games, exploded_recommendations.game_id == popular_games.id) \
        .groupBy("user_id") \
        .agg(collect_list("game_id").alias("recommendation_list"))
    
    # Select only the top 5 recommendations for each user
    top_5_recommendations = filtered_recommendations \
        .withColumn("recommendation_list", slice(col("recommendation_list"), 1, 5)) \
        .select("user_id", "recommendation_list") \
        .orderBy("user_id")

    # Display the final DataFrame
    top_5_recommendations.show(truncate=False)

    # Write the final DataFrame to PostgreSQL table 'recommendations'
    top_5_recommendations.write.jdbc(
        url=db_url,
        table="recommendations",
        mode="overwrite",  # Overwrite the table if it exists
        properties=db_properties
    )

    spark.stop()

# Schedule the update function to run every 4 hours
scheduler = BlockingScheduler()
scheduler.add_job(update_recommendations, 'interval', hours=4)
scheduler.start()
