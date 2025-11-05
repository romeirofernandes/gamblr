import pandas as pd
import numpy as np
import re

# Load both datasets
df_main = pd.read_csv('dataset.csv')
df_new = pd.read_csv('../2025-26.csv')

def has_score(row):
    score = str(row.get('Result', '') or row.get('FTHG', '') or row.get('FTAG', ''))
    if 'Result' in row and isinstance(row['Result'], str) and re.match(r'^\d+\s*-\s*\d+$', row['Result']):
        return True
    if 'FTHG' in row and 'FTAG' in row:
        try:
            return not (np.isnan(row['FTHG']) or np.isnan(row['FTAG']))
        except Exception:
            return False
    return False

existing_keys = set(zip(df_main['Date'], df_main['HomeTeam'], df_main['AwayTeam']))

def row_key(row):
    return (str(row['Date']), str(row['Home Team']), str(row['Away Team']))

# Filter only rows with a score and not already present
rows_to_add = []
for _, row in df_new.iterrows():
    # Check if score exists
    result = str(row.get('Result', ''))
    if re.match(r'^\d+\s*-\s*\d+$', result):
        key = (str(row['Date']), str(row['Home Team']), str(row['Away Team']))
        if key not in existing_keys:
            rows_to_add.append(row)

if rows_to_add:
    new_games = pd.DataFrame(rows_to_add)
    # Rename columns to match dataset.csv
    new_games = new_games.rename(columns={
        'Home Team': 'HomeTeam',
        'Away Team': 'AwayTeam',
        'Result': 'FTR'
    })
    # Parse FTHG/FTAG from FTR if needed
    def parse_scores(res):
        if isinstance(res, str) and re.match(r'^\d+\s*-\s*\d+$', res):
            h, a = res.split('-')
            return int(h.strip()), int(a.strip())
        return np.nan, np.nan
    new_games[['FTHG', 'FTAG']] = new_games['FTR'].apply(lambda x: pd.Series(parse_scores(x)))
    # Set FTR as H/A/D
    new_games['FTR'] = np.where(new_games['FTHG'] > new_games['FTAG'], 'H',
                        np.where(new_games['FTHG'] < new_games['FTAG'], 'A', 'D'))
    # Add missing columns with default values
    for col in df_main.columns:
        if col not in new_games.columns:
            new_games[col] = 0
    # Append to main dataframe
    df_main = pd.concat([df_main, new_games[df_main.columns]], ignore_index=True)

# --- Clean and update all rolling/stat columns for all games ---
df = df_main.copy()

# Fix date formats to DD/MM/YYYY
def fix_date(date_str):
    match = re.match(r'(\d{2})/(\d{2})/(\d{2,4})', str(date_str))
    if match:
        day, month, year = match.groups()
        if len(year) == 2:
            year = '20' + year if int(year) < 50 else '19' + year
        return f"{day}/{month}/{year}"
    else:
        return date_str 

df['Date'] = df['Date'].apply(fix_date)
df['Date_dt'] = pd.to_datetime(df['Date'], dayfirst=True)
df = df.sort_values('Date_dt').reset_index(drop=True)

# Helper functions (same as before)
def get_last_n_results(team, idx, n=5, home=True):
    if home:
        mask = (df['HomeTeam'] == team) & (df.index < idx)
        games = df.loc[mask].iloc[-n:]
        wins = (games['FTR'] == 'H').sum()
        goals_scored = games['FTHG'].sum()
        goals_conceded = games['FTAG'].sum()
    else:
        mask = (df['AwayTeam'] == team) & (df.index < idx)
        games = df.loc[mask].iloc[-n:]
        wins = (games['FTR'] == 'A').sum()
        goals_scored = games['FTAG'].sum()
        goals_conceded = games['FTHG'].sum()
    return wins, goals_scored, goals_conceded

def get_h2h_win_pct(home, away, idx):
    mask = ((df['HomeTeam'] == home) & (df['AwayTeam'] == away) | 
            (df['HomeTeam'] == away) & (df['AwayTeam'] == home)) & (df.index < idx)
    h2h_games = df.loc[mask]
    if len(h2h_games) == 0:
        return 0.00, 0.00
    home_wins = ((h2h_games['HomeTeam'] == home) & (h2h_games['FTR'] == 'H')).sum() + \
                ((h2h_games['AwayTeam'] == home) & (h2h_games['FTR'] == 'A')).sum()
    away_wins = ((h2h_games['HomeTeam'] == away) & (h2h_games['FTR'] == 'H')).sum() + \
                ((h2h_games['AwayTeam'] == away) & (h2h_games['FTR'] == 'A')).sum()
    total_games = len(h2h_games)
    return round(home_wins / total_games, 2), round(away_wins / total_games, 2)

def get_points_last_n(team, idx, n=5):
    mask = ((df['HomeTeam'] == team) | (df['AwayTeam'] == team)) & (df.index < idx)
    games = df.loc[mask].iloc[-n:]
    points = 0
    for _, game in games.iterrows():
        if game['HomeTeam'] == team:
            if game['FTR'] == 'H': points += 3
            elif game['FTR'] == 'D': points += 1
        else:
            if game['FTR'] == 'A': points += 3
            elif game['FTR'] == 'D': points += 1
    return points

def get_gd_last_n(team, idx, n=5):
    mask = ((df['HomeTeam'] == team) | (df['AwayTeam'] == team)) & (df.index < idx)
    games = df.loc[mask].iloc[-n:]
    gd = 0
    for _, game in games.iterrows():
        if game['HomeTeam'] == team:
            gd += game['FTHG'] - game['FTAG']
        else:
            gd += game['FTAG'] - game['FTHG']
    return gd

def get_rolling_avg(team, idx, col, n=5):
    mask = ((df['HomeTeam'] == team) | (df['AwayTeam'] == team)) & (df.index < idx)
    games = df.loc[mask].iloc[-n:]
    if len(games) == 0:
        return 0.0
    if col == 'goals_scored':
        val = ((games['HomeTeam'] == team) * games['FTHG']).sum() + \
              ((games['AwayTeam'] == team) * games['FTAG']).sum()
    elif col == 'goals_conceded':
        val = ((games['HomeTeam'] == team) * games['FTAG']).sum() + \
              ((games['AwayTeam'] == team) * games['FTHG']).sum()
    elif col == 'gd':
        val = 0
        for _, game in games.iterrows():
            if game['HomeTeam'] == team:
                val += game['FTHG'] - game['FTAG']
            else:
                val += game['FTAG'] - game['FTHG']
    else:
        val = 0
    return round(val / n, 2)

# Drop helper date column
df = df.drop(columns=['Date_dt'])

# Only update rolling stats for new rows
new_start_idx = len(df) - len(new_games)
for idx in range(new_start_idx, len(df)):
    row = df.iloc[idx]
    home = row['HomeTeam']
    away = row['AwayTeam']
    h_wins, h_gs, h_gc = get_last_n_results(home, idx, n=5, home=True)
    a_wins, a_gs, a_gc = get_last_n_results(away, idx, n=5, home=False)
    h2h_home_pct, h2h_away_pct = get_h2h_win_pct(home, away, idx)
    df.at[idx, 'HomeTeam_Wins_Last5'] = h_wins
    df.at[idx, 'AwayTeam_Wins_Last5'] = a_wins
    df.at[idx, 'HomeTeam_GoalsScored_Last5'] = h_gs
    df.at[idx, 'HomeTeam_GoalsConceded_Last5'] = h_gc
    df.at[idx, 'AwayTeam_GoalsScored_Last5'] = a_gs
    df.at[idx, 'AwayTeam_GoalsConceded_Last5'] = a_gc
    df.at[idx, 'HomeTeam_H2H_WinPct'] = h2h_home_pct
    df.at[idx, 'AwayTeam_H2H_WinPct'] = h2h_away_pct
    df.at[idx, 'HomeTeam_Points_Last5'] = get_points_last_n(home, idx)
    df.at[idx, 'AwayTeam_Points_Last5'] = get_points_last_n(away, idx)
    df.at[idx, 'HomeTeam_GD_Last5'] = get_gd_last_n(home, idx)
    df.at[idx, 'AwayTeam_GD_Last5'] = get_gd_last_n(away, idx)
    df.at[idx, 'HomeTeam_GoalsScored_Last5_avg'] = get_rolling_avg(home, idx, 'goals_scored')
    df.at[idx, 'HomeTeam_GoalsConceded_Last5_avg'] = get_rolling_avg(home, idx, 'goals_conceded')
    df.at[idx, 'AwayTeam_GoalsScored_Last5_avg'] = get_rolling_avg(away, idx, 'goals_scored')
    df.at[idx, 'AwayTeam_GoalsConceded_Last5_avg'] = get_rolling_avg(away, idx, 'goals_conceded')
    df.at[idx, 'HomeTeam_GD_Last5_avg'] = get_rolling_avg(home, idx, 'gd')
    df.at[idx, 'AwayTeam_GD_Last5_avg'] = get_rolling_avg(away, idx, 'gd')

# Save updated dataset
df.to_csv('dataset.csv', index=False)