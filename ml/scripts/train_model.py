import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score, precision_score
from sklearn.ensemble import RandomForestRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout

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

if len(score_X_win) > 0:
    home_rf = GridSearchCV(RandomForestRegressor(random_state=42), param_grid, cv=3, scoring='r2', n_jobs=-1)
    home_rf.fit(score_X_win, score_y_home_win)
    home_goals_model = home_rf.best_estimator_

    away_rf = GridSearchCV(RandomForestRegressor(random_state=42), param_grid, cv=3, scoring='r2', n_jobs=-1)
    away_rf.fit(score_X_win, score_y_away_win)
    away_goals_model = away_rf.best_estimator_

    home_pred = home_goals_model.predict(score_X_win)
    away_pred = away_goals_model.predict(score_X_win)

    print(f"Home Goals MAE: {mean_absolute_error(score_y_home_win, home_pred):.3f}")
    print(f"Home Goals RMSE: {np.sqrt(mean_squared_error(score_y_home_win, home_pred)):.3f}")
    print(f"Home Goals R2: {r2_score(score_y_home_win, home_pred):.3f}")

    print(f"Away Goals MAE: {mean_absolute_error(score_y_away_win, away_pred):.3f}")
    print(f"Away Goals RMSE: {np.sqrt(mean_squared_error(score_y_away_win, away_pred)):.3f}")
    print(f"Away Goals R2: {r2_score(score_y_away_win, away_pred):.3f}")
else:
    print("No predicted wins for score prediction.")

# Score prediction for all test matches
score_X = df.loc[X_test_rf.index, rolling_features]
score_y_home = df.loc[X_test_rf.index, 'FTHG']
score_y_away = df.loc[X_test_rf.index, 'FTAG']

param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [5, 10],
    'min_samples_split': [2, 5]
}

home_rf = GridSearchCV(RandomForestRegressor(random_state=42), param_grid, cv=3, scoring='r2', n_jobs=-1)
home_rf.fit(score_X, score_y_home)
home_goals_model = home_rf.best_estimator_

away_rf = GridSearchCV(RandomForestRegressor(random_state=42), param_grid, cv=3, scoring='r2', n_jobs=-1)
away_rf.fit(score_X, score_y_away)
away_goals_model = away_rf.best_estimator_

home_pred = home_goals_model.predict(score_X)
away_pred = away_goals_model.predict(score_X)

print(f"Home Goals MAE: {mean_absolute_error(score_y_home, home_pred):.3f}")
print(f"Home Goals RMSE: {np.sqrt(mean_squared_error(score_y_home, home_pred)):.3f}")
print(f"Home Goals R2: {r2_score(score_y_home, home_pred):.3f}")

print(f"Away Goals MAE: {mean_absolute_error(score_y_away, away_pred):.3f}")
print(f"Away Goals RMSE: {np.sqrt(mean_squared_error(score_y_away, away_pred)):.3f}")
print(f"Away Goals R2: {r2_score(score_y_away, away_pred):.3f}")