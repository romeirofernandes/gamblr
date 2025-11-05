import pandas as pd

# Load data
df = pd.read_csv('dataset.csv')

# Standardize team names (example)
df['HomeTeam'] = df['HomeTeam'].replace({'Man United': 'Man Utd', "Nott'm Forest": 'Nottingham Forest', 'Spurs': 'Tottenham'})
df['AwayTeam'] = df['AwayTeam'].replace({'Man United': 'Man Utd', "Nott'm Forest": 'Nottingham Forest', 'Spurs': 'Tottenham'})

# Remove duplicates
df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'])

# Drop unnecessary columns (keep only useful features)
columns_to_keep = [
    'Date', 'HomeTeam', 'AwayTeam', # identifiers
    # add feature columns you want to use for prediction
    'HomeTeam_Wins_Last5', 'AwayTeam_Wins_Last5',
    'HomeTeam_GoalsScored_Last5', 'HomeTeam_GoalsConceded_Last5',
    'AwayTeam_GoalsScored_Last5', 'AwayTeam_GoalsConceded_Last5',
    'HomeTeam_H2H_WinPct', 'AwayTeam_H2H_WinPct',
    'HomeTeam_Points_Last5', 'AwayTeam_Points_Last5',
    # targets
    'FTR', 'FTHG', 'FTAG'
]
df = df[columns_to_keep]

# Remove rows with missing values
df = df.dropna()

# Save cleaned data
df.to_csv('cleaned_dataset.csv', index=False)