import pandas as pd
import re

df = pd.read_csv('./dataset.csv')

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

df.to_csv('dataset.csv', index=False)