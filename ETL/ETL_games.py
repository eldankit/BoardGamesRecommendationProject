import pandas as pd

# Load the CSV file
df = pd.read_csv('games_detailed_info.csv')

# Drop unnecessary columns
df.drop(['Unnamed: 0'], axis=1, inplace=True)

# Convert 'Board Game Rank' to numeric, coercing errors to NaN
df['Board Game Rank'] = pd.to_numeric(df['Board Game Rank'], errors='coerce')

# List of columns to include in the new DataFrame
columns_list = ['thumbnail', 'image', 'description', 'yearpublished', 'minplayers',
                'maxplayers', 'playingtime', 'minage', 'boardgamecategory', 'usersrated',
                'average', 'bayesaverage', 'Board Game Rank']

# Create a new DataFrame with selected columns
game_df = df[['id', 'primary']].copy()
game_df = pd.concat([game_df, df[columns_list]], axis=1)

# Rename columns to match the desired schema
game_df.rename(columns={'primary': 'name', 'id': 'ID', 'boardgamecategory': 'category'}, inplace=True)

# Function to convert category strings to PostgreSQL array format
def row_to_list(row, column_name):
    if isinstance(row[column_name], str):
        # Strip brackets, split by comma, and format as PostgreSQL array
        categories = row[column_name].strip('[]').replace("'", "").split(', ')
        return '{' + ','.join(categories) + '}'
    return '{}'

# Apply the function to the 'category' column
game_df['category'] = game_df.apply(row_to_list, axis=1, args=('category',))


games_file_path = '2020-08-19.csv'
games = pd.read_csv(games_file_path)
games.rename(index=str, columns={'Rank':'Board Game Rank','Average':'average',"Bayes average": "bayesaverage",'Name':'name','Year':'yearpublished','URL':'image','Thumbnail':'thumbnail', 'Users rated':'usersrated'}, inplace=True)
games.drop(columns=['Unnamed: 0'], inplace=True)

# Get IDs that are in 'games' but not in 'game_df'
missing_ids = set(games['ID']) - set(game_df['ID'])

# Filter 'games' to get rows with missing IDs
games_to_add = games[games['ID'].isin(missing_ids)]

# Concatenate the two DataFrames
game_df = pd.concat([game_df, games_to_add], ignore_index=True)

# Save the formatted DataFrame to a new CSV file
game_df.to_csv('game_info.csv', index=False)

