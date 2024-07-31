import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

# PostgreSQL configuration
db_url = "jdbc:postgresql://localhost:5432/postgres"
db_properties = {
    "user": "postgres",
    "password": "mypassword",
    "driver": "org.postgresql.Driver",
    "fetchsize": "1000"  # Adjust the fetch size as needed
}

# URL of the PostgreSQL JDBC .jar file
jdbc_jar_url = "https://jdbc.postgresql.org/download/postgresql-42.7.3.jar"


model_save_path = "models/als_model"  # Path to save the model

if __name__ == "__main__":
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
    als_model.save(model_save_path)

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

    spark.stop()
