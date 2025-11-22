import pandas as pd
import json
import os
import sys
from datetime import datetime
from groq import Groq
import google.generativeai as genai
from openai import OpenAI
import time
from typing import Dict, List, Any

# Add root directory to path to access .env
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from dotenv import load_dotenv

# Load environment variables from root .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_historical_data(short=False):
    """Load historical data to provide context to LLMs"""
    df = pd.read_csv('./dataset.csv')
    season_df = pd.read_csv('../2025-26.csv')
    
    # Get recent matches for context
    recent_matches = season_df[season_df['Result'].notna()].tail(1 if short else 20)
    
    # Calculate basic team stats
    team_stats = {}
    for team in season_df['Home Team'].unique():
        matches = season_df[
            ((season_df['Home Team'] == team) | (season_df['Away Team'] == team)) &
            (season_df['Result'].notna())
        ].tail(1 if short else 10)
        
        wins = draws = losses = goals_for = goals_against = 0
        
        for _, match in matches.iterrows():
            result = match['Result'].strip().split(' - ')
            home_goals = int(result[0])
            away_goals = int(result[1])
            
            if match['Home Team'] == team:
                goals_for += home_goals
                goals_against += away_goals
                if home_goals > away_goals:
                    wins += 1
                elif home_goals == away_goals:
                    draws += 1
                else:
                    losses += 1
            else:
                goals_for += away_goals
                goals_against += home_goals
                if away_goals > home_goals:
                    wins += 1
                elif home_goals == away_goals:
                    draws += 1
                else:
                    losses += 1
        
        team_stats[team] = {
            'matches': len(matches),
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goal_difference': goals_for - goals_against
        }
    
    return recent_matches, team_stats

def create_prediction_prompt(upcoming_matches, recent_matches, team_stats):
    """Create a comprehensive prompt for LLMs"""
    
    # Recent matches context
    recent_context = "Recent Premier League Results:\n"
    for _, match in recent_matches.iterrows():
        recent_context += f"- {match['Home Team']} {match['Result']} {match['Away Team']}\n"
    
    # Team stats context
    stats_context = "\nCurrent Season Team Statistics (last 10 matches):\n"
    for team, stats in team_stats.items():
        if stats['matches'] > 0:
            stats_context += f"- {team}: {stats['wins']}W-{stats['draws']}D-{stats['losses']}L, "
            stats_context += f"Goals: {stats['goals_for']}-{stats['goals_against']} (GD: {stats['goal_difference']})\n"
    
    # Upcoming matches
    matches_context = "\nUpcoming Matches to Predict:\n"
    for _, match in upcoming_matches.iterrows():
        matches_context += f"- {match['Home Team']} vs {match['Away Team']} (Match #{match['Match Number']})\n"
    
    prompt = f"""You are an expert football analyst with deep knowledge of the Premier League. Based on the following data, predict the exact scores and match outcomes.

{recent_context}
{stats_context}
{matches_context}

Please provide predictions in the following JSON format for each match:
{{
  "match_number": [match_number],
  "home_team": "[team_name]",
  "away_team": "[team_name]", 
  "predicted_score_home": [0-5],
  "predicted_score_away": [0-5],
  "home_win_probability": [0.0-1.0],
  "draw_probability": [0.0-1.0],
  "away_win_probability": [0.0-1.0],
  "confidence": [0.0-1.0],
  "reasoning": "[brief explanation]"
}}

Consider:
- Current form and momentum
- Home advantage
- Head-to-head records
- Injuries and squad strength
- Playing styles and tactical matchups
- Recent goal-scoring and defensive records

Return ONLY a valid JSON array with predictions for all matches. Ensure probabilities sum to 1.0 for each match."""

    return prompt

def get_groq_predictions(prompt):
    """Get predictions from Groq"""
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a professional football analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = completion.choices[0].message.content.strip()
        # Clean up response to extract JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
    except Exception as e:
        print(f"Groq API error: {e}")
        return None

def get_gemini_predictions(prompt):
    """Get predictions from Gemini"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2000,
            )
        )
        # Debug: print raw response
        print("Gemini raw response:", response)
        if not response.candidates or not response.candidates[0].content.parts:
            print("Gemini returned no content. Try shortening the prompt or reducing matches.")
            return None
        response_text = response.text.strip()
        # Clean up response to extract JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        return json.loads(response_text)
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None

def process_llm_predictions(predictions, llm_name, round_number):
    """Process and standardize LLM predictions"""
    processed = []
    
    if not predictions:
        return processed
    
    for pred in predictions:
        try:
            processed.append({
                'match_number': int(pred['match_number']),
                'round_number': int(round_number),
                'home_team': pred['home_team'],
                'away_team': pred['away_team'],
                'predicted_score': f"{pred['predicted_score_home']} - {pred['predicted_score_away']}",
                'home_win_probability': float(pred['home_win_probability']),
                'draw_probability': float(pred['draw_probability']),
                'away_win_probability': float(pred['away_win_probability']),
                'confidence': float(pred.get('confidence', 0.5)),
                'reasoning': pred.get('reasoning', ''),
                'llm_source': llm_name,
                'timestamp': datetime.now().isoformat()
            })
        except (KeyError, ValueError) as e:
            print(f"Error processing {llm_name} prediction: {e}")
            continue
    
    return processed

def main():
    print("🤖 Generating LLM Predictions...")
    
    # Load data
    season_df = pd.read_csv('../2025-26.csv')
    recent_matches, team_stats = load_historical_data()
    
    # Find current gameweek
    current_gw = None
    for gw in sorted(season_df['Round Number'].unique()):
        gw_matches = season_df[season_df['Round Number'] == gw]
        if gw_matches['Result'].isna().any():
            current_gw = gw
            break
    
    if current_gw is None:
        print("No upcoming gameweek found - all matches completed!")
        return
    
    upcoming_matches = season_df[
        (season_df['Round Number'] == current_gw) & 
        (season_df['Result'].isna())
    ]
    
    print(f"\n📊 Generating predictions for Gameweek {current_gw}...")
    print(f"📈 Found {len(upcoming_matches)} upcoming matches")
    
    # Create prompt for Groq (full context)
    prompt = create_prediction_prompt(upcoming_matches, recent_matches, team_stats)
    
    all_predictions = []
    
    # Get predictions from Groq
    print("\n🧠 Getting Groq predictions...")
    groq_preds = get_groq_predictions(prompt)
    if groq_preds:
        processed_groq = process_llm_predictions(groq_preds, "groq", current_gw)
        all_predictions.extend(processed_groq)
        print(f"✅ Groq: {len(processed_groq)} predictions")
        print("\n🤖 Groq Predictions:")
        for pred in processed_groq:
            print(f"  {pred['home_team']} vs {pred['away_team']}: {pred['predicted_score']}")
            print(f"    Probabilities: H:{pred['home_win_probability']:.3f} D:{pred['draw_probability']:.3f} A:{pred['away_win_probability']:.3f}")
            print(f"    Confidence: {pred['confidence']:.3f}")
            print(f"    Reasoning: {pred['reasoning'][:100]}...")
    
    time.sleep(1)  # Rate limiting
    
    # Create prompt for Gemini (short context)
    recent_matches_short, team_stats_short = load_historical_data(short=True)
    prompt_short = create_prediction_prompt(upcoming_matches, recent_matches_short, team_stats_short)
    
    print("\n🧠 Getting Gemini predictions...")
    gemini_preds = get_gemini_predictions(prompt_short)
    if gemini_preds:
        processed_gemini = process_llm_predictions(gemini_preds, "gemini", current_gw)
        all_predictions.extend(processed_gemini)
        print(f"✅ Gemini: {len(processed_gemini)} predictions")
        print("\n🤖 Gemini Predictions:")
        for pred in processed_gemini:
            print(f"  {pred['home_team']} vs {pred['away_team']}: {pred['predicted_score']}")
            print(f"    Probabilities: H:{pred['home_win_probability']:.3f} D:{pred['draw_probability']:.3f} A:{pred['away_win_probability']:.3f}")
            print(f"    Confidence: {pred['confidence']:.3f}")
            print(f"    Reasoning: {pred['reasoning'][:100]}...")
    
    # Load existing predictions and append
    llm_predictions_file = 'llm_predictions.json'
    if os.path.exists(llm_predictions_file):
        with open(llm_predictions_file, 'r') as f:
            try:
                existing_predictions = json.load(f)
            except json.JSONDecodeError:
                existing_predictions = []
    else:
        existing_predictions = []
    
    # Append new predictions
    all_existing_predictions = existing_predictions + all_predictions
    
    # Save predictions
    with open(llm_predictions_file, 'w') as f:
        json.dump(all_existing_predictions, f, indent=2)
    
    # Save to frontend data folder
    frontend_path = '../../frontend/src/data/llm_predictions.json'
    os.makedirs(os.path.dirname(frontend_path), exist_ok=True)

    with open(frontend_path, 'w') as f:
        json.dump(all_existing_predictions, f, indent=2)

    print(f"✅ Generated {len(all_predictions)} LLM predictions for Gameweek {current_gw}")
    print(f"💾 Saved to {frontend_path}")

if __name__ == "__main__":
    main()