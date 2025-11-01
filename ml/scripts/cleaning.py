import pandas as pd
import re
import numpy as np

df = pd.read_csv('../dataset.csv')

# Fixing date formats to DD/MM/YYYY
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

# Replacing 'NH' with 'A' in the FTR column for old records
df['FTR'] = df['FTR'].replace('NH', 'A')

#Setting FTR based on FTHG and FTAG values
df.loc[df['FTHG'] > df['FTAG'], 'FTR'] = 'H'
df.loc[df['FTHG'] < df['FTAG'], 'FTR'] = 'A'
df.loc[df['FTHG'] == df['FTAG'], 'FTR'] = 'D'

# Replacing 'Middlesboro' with 'Middlesbrough'
df['HomeTeam'] = df['HomeTeam'].replace('Middlesboro', 'Middlesbrough')
df['AwayTeam'] = df['AwayTeam'].replace('Middlesboro', 'Middlesbrough')

teams = pd.unique(df[['HomeTeam', 'AwayTeam']].values.ravel())

for team in sorted(teams):
    print(team)

# Ensure matches are sorted by date for correct rolling calculations
df['Date_dt'] = pd.to_datetime(df['Date'], dayfirst=True)
df = df.sort_values('Date_dt').reset_index(drop=True)

# Helper functions
def get_last_n_results(team, idx, n=5, home=True):
    """Get last n results for a team before idx. If home=True, only home games, else only away games."""
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
    """Get head-to-head win percentage for home and away teams before idx."""
    mask = ((df['HomeTeam'] == home) & (df['AwayTeam'] == away) | 
            (df['HomeTeam'] == away) & (df['AwayTeam'] == home)) & (df.index < idx)
    h2h_games = df.loc[mask]
    if len(h2h_games) == 0:
        return np.nan, np.nan
    home_wins = ((h2h_games['HomeTeam'] == home) & (h2h_games['FTR'] == 'H')).sum() + \
                ((h2h_games['AwayTeam'] == home) & (h2h_games['FTR'] == 'A')).sum()
    away_wins = ((h2h_games['HomeTeam'] == away) & (h2h_games['FTR'] == 'H')).sum() + \
                ((h2h_games['AwayTeam'] == away) & (h2h_games['FTR'] == 'A')).sum()
    total_games = len(h2h_games)
    return home_wins / total_games, away_wins / total_games

# Initialize new columns
df['HomeTeam_Wins_Last5'] = 0
df['AwayTeam_Wins_Last5'] = 0
df['HomeTeam_GoalsScored_Last5'] = 0
df['HomeTeam_GoalsConceded_Last5'] = 0
df['AwayTeam_GoalsScored_Last5'] = 0
df['AwayTeam_GoalsConceded_Last5'] = 0
df['HomeTeam_H2H_WinPct'] = np.nan
df['AwayTeam_H2H_WinPct'] = np.nan

for idx, row in df.iterrows():
    home = row['HomeTeam']
    away = row['AwayTeam']
    # Last 5 home games for HomeTeam
    h_wins, h_gs, h_gc = get_last_n_results(home, idx, n=5, home=True)
    # Last 5 away games for AwayTeam
    a_wins, a_gs, a_gc = get_last_n_results(away, idx, n=5, home=False)
    # H2H win percentages
    h2h_home_pct, h2h_away_pct = get_h2h_win_pct(home, away, idx)
    # Round win percentages to 2 decimals, set to 0.00 if NaN
    h2h_home_pct = round(h2h_home_pct, 2) if not np.isnan(h2h_home_pct) else 0.00
    h2h_away_pct = round(h2h_away_pct, 2) if not np.isnan(h2h_away_pct) else 0.00
    # Last 5 overall games for HomeTeam (home+away)
    mask_home = ((df['HomeTeam'] == home) | (df['AwayTeam'] == home)) & (df.index < idx)
    games_home = df.loc[mask_home].iloc[-5:]
    home_goals_scored = ((games_home['HomeTeam'] == home) * games_home['FTHG']).sum() + \
                        ((games_home['AwayTeam'] == home) * games_home['FTAG']).sum()
    home_goals_conceded = ((games_home['HomeTeam'] == home) * games_home['FTAG']).sum() + \
                          ((games_home['AwayTeam'] == home) * games_home['FTHG']).sum()
    # Last 5 overall games for AwayTeam (home+away)
    mask_away = ((df['HomeTeam'] == away) | (df['AwayTeam'] == away)) & (df.index < idx)
    games_away = df.loc[mask_away].iloc[-5:]
    away_goals_scored = ((games_away['HomeTeam'] == away) * games_away['FTHG']).sum() + \
                        ((games_away['AwayTeam'] == away) * games_away['FTAG']).sum()
    away_goals_conceded = ((games_away['HomeTeam'] == away) * games_away['FTAG']).sum() + \
                          ((games_away['AwayTeam'] == away) * games_away['FTHG']).sum()
    # Assign
    df.at[idx, 'HomeTeam_Wins_Last5'] = h_wins
    df.at[idx, 'AwayTeam_Wins_Last5'] = a_wins
    df.at[idx, 'HomeTeam_GoalsScored_Last5'] = home_goals_scored
    df.at[idx, 'HomeTeam_GoalsConceded_Last5'] = home_goals_conceded
    df.at[idx, 'AwayTeam_GoalsScored_Last5'] = away_goals_scored
    df.at[idx, 'AwayTeam_GoalsConceded_Last5'] = away_goals_conceded
    df.at[idx, 'HomeTeam_H2H_WinPct'] = h2h_home_pct
    df.at[idx, 'AwayTeam_H2H_WinPct'] = h2h_away_pct

# Add points in last 5 matches
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

# Add goal difference in last 5
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

# Initialize new columns
df['HomeTeam_Points_Last5'] = 0
df['AwayTeam_Points_Last5'] = 0
df['HomeTeam_GD_Last5'] = 0
df['AwayTeam_GD_Last5'] = 0

for idx, row in df.iterrows():
    home = row['HomeTeam']
    away = row['AwayTeam']
    df.at[idx, 'HomeTeam_Points_Last5'] = get_points_last_n(home, idx)
    df.at[idx, 'AwayTeam_Points_Last5'] = get_points_last_n(away, idx)
    df.at[idx, 'HomeTeam_GD_Last5'] = get_gd_last_n(home, idx)
    df.at[idx, 'AwayTeam_GD_Last5'] = get_gd_last_n(away, idx)

# Add rolling averages for last 5 games (home+away) for each team
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

df['HomeTeam_GoalsScored_Last5_avg'] = 0.0
df['HomeTeam_GoalsConceded_Last5_avg'] = 0.0
df['AwayTeam_GoalsScored_Last5_avg'] = 0.0
df['AwayTeam_GoalsConceded_Last5_avg'] = 0.0
df['HomeTeam_GD_Last5_avg'] = 0.0
df['AwayTeam_GD_Last5_avg'] = 0.0

for idx, row in df.iterrows():
    home = row['HomeTeam']
    away = row['AwayTeam']
    df.at[idx, 'HomeTeam_GoalsScored_Last5_avg'] = get_rolling_avg(home, idx, 'goals_scored')
    df.at[idx, 'HomeTeam_GoalsConceded_Last5_avg'] = get_rolling_avg(home, idx, 'goals_conceded')
    df.at[idx, 'AwayTeam_GoalsScored_Last5_avg'] = get_rolling_avg(away, idx, 'goals_scored')
    df.at[idx, 'AwayTeam_GoalsConceded_Last5_avg'] = get_rolling_avg(away, idx, 'goals_conceded')
    df.at[idx, 'HomeTeam_GD_Last5_avg'] = get_rolling_avg(home, idx, 'gd')
    df.at[idx, 'AwayTeam_GD_Last5_avg'] = get_rolling_avg(away, idx, 'gd')

# Drop helper date column
df = df.drop(columns=['Date_dt'])

df.to_csv('dataset.csv', index=False)