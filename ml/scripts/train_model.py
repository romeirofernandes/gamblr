import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score, precision_score
from xgboost import XGBClassifier, XGBRegressor

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

X = df[nn_features]
y = df['Win']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Manual tuning: change these lists to try different values
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
xgb_pred = clf.predict(X_test)
xgb_accuracy = accuracy_score(y_test, xgb_pred)
xgb_precision = precision_score(y_test, xgb_pred, average='binary')

print(f"Best XGBClassifier params: n_estimators={best_params[0]}, max_depth={best_params[1]}, learning_rate={best_params[2]}")
print(f"XGB Win/Loss Accuracy: {xgb_accuracy:.3f}")
print(f"XGB Win/Loss Precision: {xgb_precision:.3f}")

# --- XGBoost for Score Prediction (regression) ---
X_rf = df[rolling_features]
_, X_test_rf, _, y_test_rf_idx = train_test_split(X_rf, df.index, test_size=0.2, random_state=42)
score_X = df.loc[X_test_rf.index, rolling_features]
score_y_home = df.loc[X_test_rf.index, 'FTHG']
score_y_away = df.loc[X_test_rf.index, 'FTAG']

# Manual tuning: change these lists to try different values
n_estimators_list = [100, 200]
max_depth_list = [3, 5, 7]
learning_rate_list = [0.05, 0.1, 0.2]

# Home goals
best_r2 = -np.inf
best_params = None
for n_estimators in n_estimators_list:
    for max_depth in max_depth_list:
        for learning_rate in learning_rate_list:
            home_xgb = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42)
            home_xgb.fit(score_X, score_y_home)
            home_pred = home_xgb.predict(score_X)
            r2 = r2_score(score_y_home, home_pred)
            if r2 > best_r2:
                best_r2 = r2
                best_params = (n_estimators, max_depth, learning_rate)
home_xgb = XGBRegressor(n_estimators=best_params[0], max_depth=best_params[1], learning_rate=best_params[2], random_state=42)
home_xgb.fit(score_X, score_y_home)
home_pred = home_xgb.predict(score_X)

print(f"Best Home XGB params: n_estimators={best_params[0]}, max_depth={best_params[1]}, learning_rate={best_params[2]}")
print(f"Home Goals MAE: {mean_absolute_error(score_y_home, home_pred):.3f}")
print(f"Home Goals RMSE: {np.sqrt(mean_squared_error(score_y_home, home_pred)):.3f}")
print(f"Home Goals R2: {r2_score(score_y_home, home_pred):.3f}")

# Away goals
best_r2 = -np.inf
best_params = None
for n_estimators in n_estimators_list:
    for max_depth in max_depth_list:
        for learning_rate in learning_rate_list:
            away_xgb = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42)
            away_xgb.fit(score_X, score_y_away)
            away_pred = away_xgb.predict(score_X)
            r2 = r2_score(score_y_away, away_pred)
            if r2 > best_r2:
                best_r2 = r2
                best_params = (n_estimators, max_depth, learning_rate)
away_xgb = XGBRegressor(n_estimators=best_params[0], max_depth=best_params[1], learning_rate=best_params[2], random_state=42)
away_xgb.fit(score_X, score_y_away)
away_pred = away_xgb.predict(score_X)

print(f"Best Away XGB params: n_estimators={best_params[0]}, max_depth={best_params[1]}, learning_rate={best_params[2]}")
print(f"Away Goals MAE: {mean_absolute_error(score_y_away, away_pred):.3f}")
print(f"Away Goals RMSE: {np.sqrt(mean_squared_error(score_y_away, away_pred)):.3f}")
print(f"Away Goals R2: {r2_score(score_y_away, away_pred):.3f}")