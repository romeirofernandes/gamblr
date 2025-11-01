import pandas as pd

# List your files in order
files = [
    '../data/final_dataset.csv',      # 2000–2018
    '../data/2018-19.csv',
    '../data/2019-20.csv',
    '../data/2020-2021.csv',
    '../data/2021-2022.csv'
]

# Columns to keep
cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']

dfs = []
for f in files:
    df = pd.read_csv(f)
    # Select only the required columns (ignore missing columns)
    df = df.loc[:, [col for col in cols if col in df.columns]]
    dfs.append(df)

# Concatenate all
final_df = pd.concat(dfs, ignore_index=True)

# Save merged dataset
final_df.to_csv('dataset.csv', index=False)