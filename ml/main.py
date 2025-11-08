from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import json
import subprocess
import os

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://gamblr.vercel.app"],
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

class LLMMatch(BaseModel):
    match_number: int
    round_number: int
    date: str
    location: str
    home_team: str
    away_team: str
    result: Optional[str] = None
    llm_predictions: Optional[List[dict]] = None

class GameweekResponse(BaseModel):
    round_number: int
    matches: List[Match]
    is_current: bool
    all_completed: bool

class LLMGameweekResponse(BaseModel):
    round_number: int
    matches: List[LLMMatch]
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

def load_llm_predictions():
    try:
        with open('./scripts/llm_predictions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.get("/")
def read_root():
    return {"message": "Premier League Predictions API"}

@app.get("/gameweeks", response_model=List[GameweekResponse])
def get_all_gameweeks():
    """Get all gameweeks with ML predictions"""
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

@app.get("/gameweeks/llm", response_model=List[LLMGameweekResponse])
def get_all_gameweeks_llm():
    """Get all gameweeks with LLM predictions"""
    df = load_season_data()
    llm_predictions = load_llm_predictions()
    
    # Group LLM predictions by match number
    llm_lookup = {}
    for pred in llm_predictions:
        match_num = pred['match_number']
        if match_num not in llm_lookup:
            llm_lookup[match_num] = []
        llm_lookup[match_num].append(pred)
    
    # Find current gameweek
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
                'result': match['Result'] if pd.notna(match['Result']) else None,
                'llm_predictions': llm_lookup.get(int(match['Match Number']), [])
            }
            
            matches.append(LLMMatch(**match_data))
        
        all_completed = gw_matches['Result'].notna().all()
        
        gameweeks.append(LLMGameweekResponse(
            round_number=int(round_num),
            matches=matches,
            is_current=round_num == current_gw,
            all_completed=all_completed
        ))
    
    return gameweeks

@app.get("/gameweek/{round_number}", response_model=GameweekResponse)
def get_gameweek(round_number: int):
    """Get specific gameweek with ML predictions"""
    df = load_season_data()
    predictions = load_predictions()
    
    pred_lookup = {p['match_number']: p for p in predictions}
    
    gw_matches = df[df['Round Number'] == round_number]
    if gw_matches.empty:
        raise HTTPException(status_code=404, detail="Gameweek not found")
    
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
        pred = pred_lookup.get(int(match['Match Number']))
        if pred:
            match_data.update({
                'predicted_score': pred['predicted_score'],
                'home_win_probability': pred['home_win_probability'],
                'draw_probability': pred['draw_probability'],
                'away_win_probability': pred['away_win_probability']
            })
        
        matches.append(Match(**match_data))
    
    # Check if current gameweek
    current_gw = None
    for gw in df['Round Number'].unique():
        gw_matches_check = df[df['Round Number'] == gw]
        if gw_matches_check['Result'].isna().any():
            current_gw = gw
            break
    
    all_completed = gw_matches['Result'].notna().all()
    
    return GameweekResponse(
        round_number=round_number,
        matches=matches,
        is_current=round_number == current_gw,
        all_completed=all_completed
    )

@app.get("/gameweek/{round_number}/llm", response_model=LLMGameweekResponse)
def get_gameweek_llm(round_number: int):
    """Get specific gameweek with LLM predictions"""
    df = load_season_data()
    llm_predictions = load_llm_predictions()
    
    # Group LLM predictions by match number
    llm_lookup = {}
    for pred in llm_predictions:
        match_num = pred['match_number']
        if match_num not in llm_lookup:
            llm_lookup[match_num] = []
        llm_lookup[match_num].append(pred)
    
    gw_matches = df[df['Round Number'] == round_number]
    if gw_matches.empty:
        raise HTTPException(status_code=404, detail="Gameweek not found")
    
    matches = []
    for _, match in gw_matches.iterrows():
        match_data = {
            'match_number': int(match['Match Number']),
            'round_number': int(match['Round Number']),
            'date': match['Date'],
            'location': match['Location'],
            'home_team': match['Home Team'],
            'away_team': match['Away Team'],
            'result': match['Result'] if pd.notna(match['Result']) else None,
            'llm_predictions': llm_lookup.get(int(match['Match Number']), [])
        }
        
        matches.append(LLMMatch(**match_data))
    
    # Check if current gameweek
    current_gw = None
    for gw in df['Round Number'].unique():
        gw_matches_check = df[df['Round Number'] == gw]
        if gw_matches_check['Result'].isna().any():
            current_gw = gw
            break
    
    all_completed = gw_matches['Result'].notna().all()
    
    return LLMGameweekResponse(
        round_number=round_number,
        matches=matches,
        is_current=round_number == current_gw,
        all_completed=all_completed
    )

@app.post("/regenerate-predictions")
def regenerate_predictions():
    """Regenerate ML predictions"""
    try:
        result = subprocess.run(
            ["python", "scripts/generate_predictions.py"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {"message": "ML predictions regenerated successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Error: {result.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/regenerate-llm-predictions")
def regenerate_llm_predictions():
    """Regenerate LLM predictions"""
    try:
        result = subprocess.run(
            ["python", "scripts/llm_predictions.py"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {"message": "LLM predictions regenerated successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Error: {result.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))