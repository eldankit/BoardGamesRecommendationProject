from confluent_kafka import Consumer, KafkaError
import json
from datetime import datetime
from collections import defaultdict
import signal
import sys

# Kafka consumer configuration
conf = {
    'bootstrap.servers': 'kafka:9092',  # Use the Kubernetes service name
    'group.id': 'analytics',
    'auto.offset.reset': 'earliest'
}

# Initialize Kafka consumer
consumer = Consumer(conf)
consumer.subscribe(['user-events'])

# Dictionary to hold counts
user_counts = defaultdict(int)
game_views = defaultdict(int)
current_date = datetime.now().date()

def reset_counts():
    global user_counts, game_views
    user_counts = defaultdict(int)
    game_views = defaultdict(int)

def save_daily_analytics():
    analytics_data = {
        "date": str(current_date),
        "user_counts": dict(user_counts),
        "game_views": dict(game_views)
    }
    filename = f"analytics_{current_date}.json"
    with open(filename, 'w') as json_file:
        json.dump(analytics_data, json_file, indent=4)
    print(f"Saved daily analytics to {filename}")

def handle_termination(signal, frame):
    print("Termination signal received. Closing consumer...")
    consumer.close()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_termination)
signal.signal(signal.SIGTERM, handle_termination)

while True:
    msg = consumer.poll(timeout=1.0)
    if msg is None:
        continue
    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            continue
        else:
            print(msg.error())
            break

    event = json.loads(msg.value().decode('utf-8'))
    event_type = event['event']

    # Reset counts if the day has changed
    if datetime.now().date() != current_date:
        save_daily_analytics()
        current_date = datetime.now().date()
        reset_counts()

    if event_type == 'user_created':
        user_counts[current_date] += 1
    elif event_type == 'game_viewed':
        game_views[event['game_id']] += 1

    print(f"User counts: {dict(user_counts)}")
    print(f"Game views: {dict(game_views)}")

consumer.close()
