import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

csv_file_path = 'reviews_15m.csv'
params_file_path = 'best_params.json'

if __name__ == "__main__":
    # Initialize SparkSession
    spark = SparkSession.builder.appName("Game Recommendation").getOrCreate()

    # Create the df using the reviews data
    df = spark.read.csv(csv_file_path, header=True, inferSchema=True)

    # Split data into training and test sets (80% train, 20% test)
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)

    # Load the best parameters from the file
    params_file_path = 'best_params.json'
    with open(params_file_path, 'r') as f:
        best_params = json.load(f)

    # Build the ALS model with the best parameters
    als = ALS(
        userCol="user_id",
        itemCol="ID",
        ratingCol="rating",
        rank=best_params["rank"],
        regParam=best_params["regParam"],
        maxIter=best_params["maxIter"],
        coldStartStrategy="drop"  # Drop NaN predictions
    )

    # Train the ALS model on the training data
    als_model = als.fit(train_data)

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
