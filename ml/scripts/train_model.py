import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score, precision_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from xgboost import XGBRegressor

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

# Neural Network for Win/Loss
X_nn = df[nn_features]
y = df['Win']
X_train_nn, X_test_nn, y_train_nn, y_test_nn = train_test_split(X_nn, y, test_size=0.2, random_state=42)

model = Sequential([
    Dense(128, activation='tanh', input_shape=(len(nn_features),)),
    Dropout(0.3),
    Dense(64, activation='tanh'),
    Dropout(0.3),
    Dense(32, activation='tanh'),
    Dropout(0.3),
    Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(X_train_nn, y_train_nn, epochs=75, batch_size=16, validation_split=0.2, verbose=0)

nn_pred_prob = model.predict(X_test_nn)
nn_pred = (nn_pred_prob > 0.5).astype(int).flatten()
nn_accuracy = accuracy_score(y_test_nn, nn_pred)
nn_precision = precision_score(y_test_nn, nn_pred, average='binary')

print(f"NN Win/Loss Accuracy: {nn_accuracy:.3f}")
print(f"NN Win/Loss Precision: {nn_precision:.3f}")

# Score prediction only for matches predicted as wins by NN
X_rf = df[rolling_features]
y_home = df['FTHG']
y_away = df['FTAG']
_, X_test_rf, _, y_test_rf_idx = train_test_split(X_rf, df.index, test_size=0.2, random_state=42)

win_indices = np.array(y_test_rf_idx)[nn_pred == 1]
score_X_win = df.loc[win_indices, rolling_features]
score_y_home_win = df.loc[win_indices, 'FTHG']
score_y_away_win = df.loc[win_indices, 'FTAG']

param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [5, 10],
    'min_samples_split': [2, 5]
}
# Score prediction for all test matches
score_X = df.loc[X_test_rf.index, rolling_features]
score_y_home = df.loc[X_test_rf.index, 'FTHG']
score_y_away = df.loc[X_test_rf.index, 'FTAG']

# Manual tuning for XGBoost
best_r2 = -np.inf
best_params = None
for n_estimators in [100, 200]:
    for max_depth in [3, 5, 7]:
        for learning_rate in [0.05, 0.1, 0.2]:
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

# Repeat for away goals
best_r2 = -np.inf
best_params = None
for n_estimators in [100, 200]:
    for max_depth in [3, 5, 7]:
        for learning_rate in [0.05, 0.1, 0.2]:
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