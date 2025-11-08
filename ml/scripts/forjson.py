import pandas as pd
import json

# Load existing bets data
bets_file = '../../frontend/src/data/bets.json'
try:
    with open(bets_file, 'r') as f:
        existing_data = json.load(f)
except FileNotFoundError:
    existing_data = []

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

# Create new structure
new_gameweeks = []

for gw_data in existing_data:
    gw_num = gw_data['gameweek']
    
    # Convert old structure to new structure
    if 'bets' in gw_data and 'ml_bets' not in gw_data:
        # Old structure - convert it
        old_bets = gw_data.get('bets', [])
        
        # Keep all existing bets in both ML and LLM (you'll update LLM later)
        new_gameweeks.append({
            "gameweek": gw_num,
            "ml_bets": old_bets,  # Keep ALL existing bets
            "llm_bets": old_bets  # Same bets for now, you'll update later
        })
    else:
        # Already in new structure - keep as is
        new_gameweeks.append({
            "gameweek": gw_num,
            "ml_bets": gw_data.get('ml_bets', []),
            "llm_bets": gw_data.get('llm_bets', [])
        })

# Fill in missing gameweeks
existing_gws = {gw['gameweek'] for gw in new_gameweeks}
for gw in sorted(df['Round Number'].unique()):
    if gw not in existing_gws:
        new_gameweeks.append({
            "gameweek": int(gw),
            "ml_bets": [],
            "llm_bets": []
        })

# Sort by gameweek
new_gameweeks.sort(key=lambda x: x['gameweek'])

# Save to JSON
with open(bets_file, 'w') as f:
    json.dump(new_gameweeks, f, indent=2)

print(f"✅ Converted bets JSON structure with {len(new_gameweeks)} gameweeks")
print(f"💾 Updated {bets_file}")

# Print summary
total_ml_bets = sum(len(gw['ml_bets']) for gw in new_gameweeks)
total_llm_bets = sum(len(gw['llm_bets']) for gw in new_gameweeks)
print(f"📊 Total ML bets: {total_ml_bets}")
print(f"🤖 Total LLM bets: {total_llm_bets}")