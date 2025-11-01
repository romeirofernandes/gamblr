from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import json
from datetime import datetime

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Match(BaseModel):
    match_number: int
    round_number: int
    date: str
    location: str
    home_team: str
    away_team: str
    result: Optional[str] = None
    predicted_score: Optional[str] = None
    home_win_probability: Optional[float] = None
    draw_probability: Optional[float] = None
    away_win_probability: Optional[float] = None

class GameweekResponse(BaseModel):
    round_number: int
    matches: List[Match]
    is_current: bool
    all_completed: bool

# Load data
def load_season_data():
    df = pd.read_csv('2025-26.csv')
    return df

def load_predictions():
    try:
        with open('./scripts/predictions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.get("/")
def read_root():
    return {"message": "Premier League Predictions API"}

@app.get("/gameweeks", response_model=List[GameweekResponse])
def get_all_gameweeks():
    """Get all gameweeks with results and predictions"""
    df = load_season_data()
    predictions = load_predictions()
    
    # Create predictions lookup
    pred_lookup = {p['match_number']: p for p in predictions}
    
    # Find current gameweek (first with incomplete matches)
    current_gw = None
    for gw in df['Round Number'].unique():
        gw_matches = df[df['Round Number'] == gw]
        if gw_matches['Result'].isna().any():
            current_gw = gw
            break
    
    gameweeks = []
    for round_num in sorted(df['Round Number'].unique()):
        gw_matches = df[df['Round Number'] == round_num]
        
        matches = []
        for _, match in gw_matches.iterrows():
            match_data = {
                'match_number': int(match['Match Number']),
                'round_number': int(match['Round Number']),
                'date': match['Date'],
                'location': match['Location'],
                'home_team': match['Home Team'],
                'away_team': match['Away Team'],
                'result': match['Result'] if pd.notna(match['Result']) else None
            }
            
            # Add predictions only for current gameweek
            if round_num == current_gw and pd.isna(match['Result']):
                pred = pred_lookup.get(int(match['Match Number']))
                if pred:
                    match_data.update({
                        'predicted_score': pred['predicted_score'],
                        'home_win_probability': pred['home_win_probability'],
                        'draw_probability': pred['draw_probability'],
                        'away_win_probability': pred['away_win_probability']
                    })
            
            matches.append(Match(**match_data))
        
        all_completed = gw_matches['Result'].notna().all()
        
        gameweeks.append(GameweekResponse(
            round_number=int(round_num),
            matches=matches,
            is_current=round_num == current_gw,
            all_completed=all_completed
        ))
    
    return gameweeks

@app.get("/gameweek/{round_number}", response_model=GameweekResponse)
def get_gameweek(round_number: int):
    """Get a specific gameweek"""
    df = load_season_data()
    predictions = load_predictions()
    
    gw_matches = df[df['Round Number'] == round_number]
    
    if gw_matches.empty:
        raise HTTPException(status_code=404, detail="Gameweek not found")
    
    pred_lookup = {p['match_number']: p for p in predictions}
    
    # Find current gameweek
    current_gw = None
    for gw in df['Round Number'].unique():
        gw_df = df[df['Round Number'] == gw]
        if gw_df['Result'].isna().any():
            current_gw = gw
            break
    
    matches = []
    for _, match in gw_matches.iterrows():
        match_data = {
            'match_number': int(match['Match Number']),
            'round_number': int(match['Round Number']),
            'date': match['Date'],
            'location': match['Location'],
            'home_team': match['Home Team'],
            'away_team': match['Away Team'],
            'result': match['Result'] if pd.notna(match['Result']) else None
        }
        
        if round_number == current_gw and pd.isna(match['Result']):
            pred = pred_lookup.get(int(match['Match Number']))
            if pred:
                match_data.update({
                    'predicted_score': pred['predicted_score'],
                    'home_win_probability': pred['home_win_probability'],
                    'draw_probability': pred['draw_probability'],
                    'away_win_probability': pred['away_win_probability']
                })
        
        matches.append(Match(**match_data))
    
    all_completed = gw_matches['Result'].notna().all()
    
    return GameweekResponse(
        round_number=round_number,
        matches=matches,
        is_current=round_number == current_gw,
        all_completed=all_completed
    )

@app.post("/regenerate-predictions")
def regenerate_predictions():
    """Regenerate predictions (run this after updating results)"""
    import subprocess
    result = subprocess.run(['python', 'scripts/generate_predictions.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        return {"message": "Predictions regenerated successfully"}
    else:
        raise HTTPException(status_code=500, detail=f"Error: {result.stderr}")