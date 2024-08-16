# Use the official Bitnami Spark PySpark image as the base image
FROM bitnami/spark:3.4.1

# Switch to root user to install dependencies
USER root

# Install Java (required for Spark) and other necessary dependencies
RUN apt-get update && apt-get install -y \
    openjdk-11-jre-headless \
    curl \
    build-essential \
    python3-dev \
    && apt-get clean

# Install PySpark
#RUN pip install pyspark==3.4.1

# Copy the requirements.txt file and install additional Python dependencies (if any)
COPY requirements.txt /opt/spark/app/requirements.txt
RUN pip install --no-cache-dir -r /opt/spark/app/requirements.txt

# Copy the pre-downloaded PostgreSQL JDBC driver into the Spark jars directory
COPY postgresql-42.7.3.jar /opt/bitnami/spark/jars/postgresql-42.7.3.jar

# Copy the PySpark script to the container
COPY update_recommendations.py /opt/bitnami/spark/app/update_recommendations.py

# Set the working directory
WORKDIR /opt/bitnami/spark/app

# Run the PySpark script using Spark's own Python interpreter
CMD ["spark-submit", "/opt/bitnami/spark/app/update_recommendations.py"]
