import numpy as np
import pandas as pd


#ETL for 19m reviews csv

reviews_19m = pd.read_csv('bgg-19m-reviews.csv')
reviews_19m.drop(columns=['Unnamed: 0'], inplace=True)
reviews_19m.drop(columns=['comment', 'name'], inplace=True)
reviews_19m.dropna(inplace=True)

unique_users = reviews_19m['user'].unique()
user_to_id = {user: i for i, user in enumerate(unique_users)}
reviews_19m['user_id'] = reviews_19m['user'].map(user_to_id)
users_df = reviews_19m[['user_id', 'user']].drop_duplicates().reset_index(drop=True)
users_df.rename(columns={'user': 'username'}, inplace=True)
# Adding email and password columns
users_df['email'] = np.nan  # or you can use placeholder values
users_df['password'] = np.nan  # or you can use placeholder values
reviews_19m.drop(columns=['user'], inplace=True)
reviews_19m.to_csv('reviews_19m.csv', index=False)
users_df.to_csv('users_19m.csv', index=False)

#ETL for 15m reviews csv

reviews_15m = pd.read_csv('bgg-15m-reviews.csv')
reviews_15m.drop(columns=['Unnamed: 0'], inplace=True)
reviews_15m.drop(columns=['comment', 'name'], inplace=True)
reviews_15m.dropna(inplace=True)

unique_users = reviews_15m['user'].unique()
user_to_id = {user: i for i, user in enumerate(unique_users)}
reviews_15m['user_id'] = reviews_15m['user'].map(user_to_id)
users_df = reviews_15m[['user_id', 'user']].drop_duplicates().reset_index(drop=True)
users_df.rename(columns={'user': 'username'}, inplace=True)
# Adding email and password columns
users_df['email'] = np.nan  # or you can use placeholder values
users_df['password'] = np.nan  # or you can use placeholder values
reviews_15m.drop(columns=['user'], inplace=True)
reviews_15m.to_csv('reviews_15m.csv', index=False)
users_df.to_csv('users_15m.csv', index=False)
