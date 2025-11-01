import pandas as pd
import json

# Load the CSV
df = pd.read_csv('../2025-26.csv')

# Load predictions to get probabilities
try:
    with open('./predictions.json', 'r') as f:
        predictions = json.load(f)
    pred_lookup = {p['match_number']: p for p in predictions}
except FileNotFoundError:
    pred_lookup = {}
    print("⚠️  predictions.json not found. Using empty predictions.")

# Group by gameweek
gameweeks = []
for gw in sorted(df['Round Number'].unique()):
    gw_matches = df[df['Round Number'] == gw]
    bets = []
    
    for _, match in gw_matches.iterrows():
        match_num = int(match['Match Number'])
        home_team = match['Home Team']
        away_team = match['Away Team']
        has_result = pd.notna(match['Result'])
        
        # Get prediction for this match
        pred = pred_lookup.get(match_num, {})
        
        # Determine bet selection based on highest probability
        bet_on = None
        stake = 0
        
        if not has_result and pred:
            # Only bet on upcoming matches with predictions
            home_prob = pred.get('home_win_probability', 0)
            draw_prob = pred.get('draw_probability', 0)
            away_prob = pred.get('away_win_probability', 0)
            
            max_prob = max(home_prob, draw_prob, away_prob)
            
            if max_prob == home_prob:
                bet_on = home_team
            elif max_prob == draw_prob:
                bet_on = "Draw"
            else:
                bet_on = away_team
            
            stake = 100
        
        # For completed matches or matches without predictions, stake is 0
        if has_result or not pred:
            stake = 0
            bet_on = None
        
        bets.append({
            "match_number": match_num,
            "home_team": home_team,
            "away_team": away_team,
            "bet_on": bet_on,
            "odds": 0,  # Placeholder for manual entry
            "stake": stake,
            "result": None  # Will be updated manually
        })
    
    gameweeks.append({
        "gameweek": int(gw),
        "bets": bets
    })

# Save to JSON
output_file = '../../frontend/src/data/bets.json'
with open(output_file, 'w') as f:
    json.dump(gameweeks, f, indent=2)

print(f"✅ Generated bets JSON with {len(gameweeks)} gameweeks")
print(f"💾 Saved to {output_file}")

# Print summary
total_bets = sum(len(gw['bets']) for gw in gameweeks)
active_bets = sum(1 for gw in gameweeks for bet in gw['bets'] if bet['stake'] > 0)
print(f"📊 Total matches: {total_bets}")
print(f"🎯 Active bets (stake > 0): {active_bets}")
print(f"⏸️  Zero stake (completed/no prediction): {total_bets - active_bets}")