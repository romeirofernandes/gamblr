import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv('dataset.csv')

# --- Filter data for matches after 16/08/2022 ---
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
start_date = pd.to_datetime('16/08/2022', dayfirst=True)
df = df[df['Date'] > start_date].reset_index(drop=True)

# --- Add team identity features ---
teams = pd.concat([df['HomeTeam'], df['AwayTeam']]).unique()
for team in teams:
    df[f'HomeTeam_{team}'] = (df['HomeTeam'] == team).astype(int)
    df[f'AwayTeam_{team}'] = (df['AwayTeam'] == team).astype(int)

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
] + [f'HomeTeam_{team}' for team in teams] + [f'AwayTeam_{team}' for team in teams]

rolling_features = [
    'HomeTeam_GoalsScored_Last5_avg',
    'HomeTeam_GoalsConceded_Last5_avg',
    'AwayTeam_GoalsScored_Last5_avg',
    'AwayTeam_GoalsConceded_Last5_avg',
    'HomeTeam_GD_Last5_avg',
    'AwayTeam_GD_Last5_avg'
]

le = LabelEncoder()
df['FTR_encoded'] = le.fit_transform(df['FTR'])  # H=0, D=1, A=2

# --- Classification: Logistic Regression for FTR ---
X = df[nn_features]
y = df['FTR_encoded']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

lr_clf = LogisticRegression(multi_class='multinomial', max_iter=1000, random_state=42)
lr_clf.fit(X_train, y_train)
lr_pred_train = lr_clf.predict(X_train)
lr_pred_test = lr_clf.predict(X_test)
lr_acc_train = accuracy_score(y_train, lr_pred_train)
lr_acc_test = accuracy_score(y_test, lr_pred_test)

print("\n--- FTR Classification Results (Logistic Regression, after 16-08-2025) ---")
print(f"Train Accuracy: {lr_acc_train:.3f}")
print(f"Test Accuracy:  {lr_acc_test:.3f}")

# --- Regression: XGBoost for Home/Away Goals ---
X_rf = df[rolling_features]
y_home = df['FTHG']
y_away = df['FTAG']
X_rf_train, X_rf_test, y_home_train, y_home_test = train_test_split(X_rf, y_home, test_size=0.2, random_state=42)
_, _, y_away_train, y_away_test = train_test_split(X_rf, y_away, test_size=0.2, random_state=42)

param_grid_reg = {
    'n_estimators': [100, 200],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.05, 0.1, 0.2]
}

xgb_home = XGBRegressor(random_state=42)
grid_home = GridSearchCV(xgb_home, param_grid_reg, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
grid_home.fit(X_rf_train, y_home_train)
best_xgb_home = grid_home.best_estimator_
xgb_home_pred_train = best_xgb_home.predict(X_rf_train)
xgb_home_pred_test = best_xgb_home.predict(X_rf_test)

print("\n--- Home Goals Regression (XGBoost, after 16-08-2025) ---")
print(f"Best Params: {grid_home.best_params_}")
print(f"Train MAE: {mean_absolute_error(y_home_train, xgb_home_pred_train):.3f}")
print(f"Test MAE:  {mean_absolute_error(y_home_test, xgb_home_pred_test):.3f}")
print(f"Train RMSE: {np.sqrt(mean_squared_error(y_home_train, xgb_home_pred_train)):.3f}")
print(f"Test RMSE:  {np.sqrt(mean_squared_error(y_home_test, xgb_home_pred_test)):.3f}")
print(f"Train R2:   {r2_score(y_home_train, xgb_home_pred_train):.3f}")
print(f"Test R2:    {r2_score(y_home_test, xgb_home_pred_test):.3f}")

xgb_away = XGBRegressor(random_state=42)
grid_away = GridSearchCV(xgb_away, param_grid_reg, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
grid_away.fit(X_rf_train, y_away_train)
best_xgb_away = grid_away.best_estimator_
xgb_away_pred_train = best_xgb_away.predict(X_rf_train)
xgb_away_pred_test = best_xgb_away.predict(X_rf_test)

print("\n--- Away Goals Regression (XGBoost, after 16-08-2025) ---")
print(f"Best Params: {grid_away.best_params_}")
print(f"Train MAE: {mean_absolute_error(y_away_train, xgb_away_pred_train):.3f}")
print(f"Test MAE:  {mean_absolute_error(y_away_test, xgb_away_pred_test):.3f}")
print(f"Train RMSE: {np.sqrt(mean_squared_error(y_away_train, xgb_away_pred_train)):.3f}")
print(f"Test RMSE:  {np.sqrt(mean_squared_error(y_away_test, xgb_away_pred_test)):.3f}")
print(f"Train R2:   {r2_score(y_away_train, xgb_away_pred_train):.3f}")
print(f"Test R2:    {r2_score(y_away_test, xgb_away_pred_test):.3f}")