import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import accuracy_score, r2_score
import json
import os

# Load and train models (same as train_model.py)
df = pd.read_csv('dataset.csv')

nn_features = [
    'HomeTeam_Wins_Last5',
    'AwayTeam_Wins_Last5',
    'HomeTeam_Points_Last5',
    'AwayTeam_Points_Last5',
    'HomeTeam_GoalsScored_Last5',
    'HomeTeam_GoalsConceded_Last5',
    'AwayTeam_GoalsScored_Last5',
    'AwayTeam_GoalsConceded_Last5',
    'HomeTeam_GD_Last5',
    'AwayTeam_GD_Last5',
    'HomeTeam_H2H_WinPct',
    'AwayTeam_H2H_WinPct'
]

rolling_features = [
    'HomeTeam_GoalsScored_Last5_avg',
    'HomeTeam_GoalsConceded_Last5_avg',
    'AwayTeam_GoalsScored_Last5_avg',
    'AwayTeam_GoalsConceded_Last5_avg',
    'HomeTeam_GD_Last5_avg',
    'AwayTeam_GD_Last5_avg'
]

df['Win'] = (df['FTR'] == 'H').astype(int)

# Train Win/Loss Classifier
X = df[nn_features]
y = df['Win']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

n_estimators_list = [100, 200]
max_depth_list = [3, 5, 7]
learning_rate_list = [0.05, 0.1, 0.2]

best_acc = -np.inf
best_params = None
for n_estimators in n_estimators_list:
    for max_depth in max_depth_list:
        for learning_rate in learning_rate_list:
            clf = XGBClassifier(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate,
                                use_label_encoder=False, eval_metric='logloss', random_state=42)
            clf.fit(X_train, y_train)
            pred = clf.predict(X_test)
            acc = accuracy_score(y_test, pred)
            if acc > best_acc:
                best_acc = acc
                best_params = (n_estimators, max_depth, learning_rate)

clf = XGBClassifier(n_estimators=best_params[0], max_depth=best_params[1], learning_rate=best_params[2],
                    use_label_encoder=False, eval_metric='logloss', random_state=42)
clf.fit(X_train, y_train)

print(f"Trained Win/Loss Model: n_estimators={best_params[0]}, max_depth={best_params[1]}, learning_rate={best_params[2]}")

# Train Score Regressors
X_rf = df[rolling_features]
_, X_test_rf, _, y_test_rf_idx = train_test_split(X_rf, df.index, test_size=0.2, random_state=42)
score_X = df.loc[X_test_rf.index, rolling_features]
score_y_home = df.loc[X_test_rf.index, 'FTHG']
score_y_away = df.loc[X_test_rf.index, 'FTAG']

# Home goals
best_r2 = -np.inf
best_params_home = None
for n_estimators in n_estimators_list:
    for max_depth in max_depth_list:
        for learning_rate in learning_rate_list:
            home_xgb = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42)
            home_xgb.fit(score_X, score_y_home)
            home_pred = home_xgb.predict(score_X)
            r2 = r2_score(score_y_home, home_pred)
            if r2 > best_r2:
                best_r2 = r2
                best_params_home = (n_estimators, max_depth, learning_rate)

home_xgb = XGBRegressor(n_estimators=best_params_home[0], max_depth=best_params_home[1], learning_rate=best_params_home[2], random_state=42)
home_xgb.fit(score_X, score_y_home)

print(f"Trained Home Goals Model: n_estimators={best_params_home[0]}, max_depth={best_params_home[1]}, learning_rate={best_params_home[2]}")

# Away goals
best_r2 = -np.inf
best_params_away = None
for n_estimators in n_estimators_list:
    for max_depth in max_depth_list:
        for learning_rate in learning_rate_list:
            away_xgb = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42)
            away_xgb.fit(score_X, score_y_away)
            away_pred = away_xgb.predict(score_X)
            r2 = r2_score(score_y_away, away_pred)
            if r2 > best_r2:
                best_r2 = r2
                best_params_away = (n_estimators, max_depth, learning_rate)

away_xgb = XGBRegressor(n_estimators=best_params_away[0], max_depth=best_params_away[1], learning_rate=best_params_away[2], random_state=42)
away_xgb.fit(score_X, score_y_away)

print(f"Trained Away Goals Model: n_estimators={best_params_away[0]}, max_depth={best_params_away[1]}, learning_rate={best_params_away[2]}")

# Load 2025-26 season data
season_df = pd.read_csv('../2025-26.csv')

# Helper functions to calculate features from completed matches
def calculate_team_stats(matches_df, team_name):
    """Calculate last 5 matches stats for a team"""
    team_matches = matches_df[
        ((matches_df['Home Team'] == team_name) | (matches_df['Away Team'] == team_name)) &
        (matches_df['Result'].notna())
    ].tail(5)
    
    if len(team_matches) == 0:
        return {
            'wins': 0, 'points': 0, 'goals_scored': 0, 'goals_conceded': 0,
            'gd': 0, 'avg_goals_scored': 0.0, 'avg_goals_conceded': 0.0, 'avg_gd': 0.0
        }
    
    wins = 0
    points = 0
    goals_scored = 0
    goals_conceded = 0
    
    for _, match in team_matches.iterrows():
        result = match['Result'].strip().split(' - ')
        home_goals = int(result[0])
        away_goals = int(result[1])
        
        if match['Home Team'] == team_name:
            goals_scored += home_goals
            goals_conceded += away_goals
            if home_goals > away_goals:
                wins += 1
                points += 3
            elif home_goals == away_goals:
                points += 1
        else:
            goals_scored += away_goals
            goals_conceded += home_goals
            if away_goals > home_goals:
                wins += 1
                points += 3
            elif home_goals == away_goals:
                points += 1
    
    num_matches = len(team_matches)
    return {
        'wins': wins,
        'points': points,
        'goals_scored': goals_scored,
        'goals_conceded': goals_conceded,
        'gd': goals_scored - goals_conceded,
        'avg_goals_scored': goals_scored / num_matches,
        'avg_goals_conceded': goals_conceded / num_matches,
        'avg_gd': (goals_scored - goals_conceded) / num_matches
    }

def calculate_h2h(matches_df, home_team, away_team):
    """Calculate head-to-head stats"""
    h2h_matches = matches_df[
        (((matches_df['Home Team'] == home_team) & (matches_df['Away Team'] == away_team)) |
         ((matches_df['Home Team'] == away_team) & (matches_df['Away Team'] == home_team))) &
        (matches_df['Result'].notna())
    ].tail(5)
    
    if len(h2h_matches) == 0:
        return 0.5, 0.5
    
    home_wins = 0
    away_wins = 0
    
    for _, match in h2h_matches.iterrows():
        result = match['Result'].strip().split(' - ')
        home_goals = int(result[0])
        away_goals = int(result[1])
        
        if match['Home Team'] == home_team:
            if home_goals > away_goals:
                home_wins += 1
            elif away_goals > home_goals:
                away_wins += 1
        else:
            if away_goals > home_goals:
                home_wins += 1
            elif home_goals > away_goals:
                away_wins += 1
    
    total = len(h2h_matches)
    return home_wins / total, away_wins / total

# Find the current gameweek (first round with at least one match without result)
current_gw = None
for gw in sorted(season_df['Round Number'].unique()):
    gw_matches = season_df[season_df['Round Number'] == gw]
    if gw_matches['Result'].isna().any():
        current_gw = gw
        break

if current_gw is None:
    print("No upcoming gameweek found - all matches completed!")
    predictions = []
else:
    print(f"\nGenerating predictions for Gameweek {current_gw}...")
    
    upcoming_matches = season_df[
        (season_df['Round Number'] == current_gw) & 
        (season_df['Result'].isna())
    ]
    
    predictions = []
    
    for _, match in upcoming_matches.iterrows():
        home_team = match['Home Team']
        away_team = match['Away Team']
        
        home_stats = calculate_team_stats(season_df, home_team)
        away_stats = calculate_team_stats(season_df, away_team)
        home_h2h, away_h2h = calculate_h2h(season_df, home_team, away_team)
        
        win_features = pd.DataFrame([{
            'HomeTeam_Wins_Last5': home_stats['wins'],
            'AwayTeam_Wins_Last5': away_stats['wins'],
            'HomeTeam_Points_Last5': home_stats['points'],
            'AwayTeam_Points_Last5': away_stats['points'],
            'HomeTeam_GoalsScored_Last5': home_stats['goals_scored'],
            'HomeTeam_GoalsConceded_Last5': home_stats['goals_conceded'],
            'AwayTeam_GoalsScored_Last5': away_stats['goals_scored'],
            'AwayTeam_GoalsConceded_Last5': away_stats['goals_conceded'],
            'HomeTeam_GD_Last5': home_stats['gd'],
            'AwayTeam_GD_Last5': away_stats['gd'],
            'HomeTeam_H2H_WinPct': home_h2h,
            'AwayTeam_H2H_WinPct': away_h2h
        }])
        
        score_features = pd.DataFrame([{
            'HomeTeam_GoalsScored_Last5_avg': home_stats['avg_goals_scored'],
            'HomeTeam_GoalsConceded_Last5_avg': home_stats['avg_goals_conceded'],
            'AwayTeam_GoalsScored_Last5_avg': away_stats['avg_goals_scored'],
            'AwayTeam_GoalsConceded_Last5_avg': away_stats['avg_goals_conceded'],
            'HomeTeam_GD_Last5_avg': home_stats['avg_gd'],
            'AwayTeam_GD_Last5_avg': away_stats['avg_gd']
        }])
        
        home_score = max(0, round(home_xgb.predict(score_features)[0]))
        away_score = max(0, round(away_xgb.predict(score_features)[0]))
        
        margin = home_score - away_score
        exp_home = np.exp(margin)
        exp_away = np.exp(-margin)
        exp_draw = np.exp(-abs(margin))
        total = exp_home + exp_away + exp_draw
        home_win_probability = exp_home / total
        draw_probability = exp_draw / total
        away_win_probability = exp_away / total
        
        predictions.append({
            'match_number': int(match['Match Number']),
            'round_number': int(match['Round Number']),
            'date': match['Date'],
            'location': match['Location'],
            'home_team': home_team,
            'away_team': away_team,
            'predicted_score': f"{home_score} - {away_score}",
            'home_win_probability': float(round(home_win_probability, 3)),
            'draw_probability': float(round(draw_probability, 3)),
            'away_win_probability': float(round(away_win_probability, 3))
        })
        
        # print(f"  ✓ {home_team} vs {away_team}: {home_score}-{away_score} (Home win: {win_prob*100:.1f}%)")

# Read previous predictions if file exists
if os.path.exists('predictions.json'):
    with open('predictions.json', 'r') as f:
        try:
            previous_predictions = json.load(f)
        except json.JSONDecodeError:
            previous_predictions = []
else:
    previous_predictions = []

# Append new predictions
all_predictions = previous_predictions + predictions

# Write back to file
with open('predictions.json', 'w') as f:
    json.dump(all_predictions, f, indent=2)

print(f"\n✅ Generated {len(predictions)} predictions for Gameweek {current_gw}")
print(f"💾 Appended to predictions.json")