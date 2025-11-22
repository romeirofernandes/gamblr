from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pandas as pd

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://gamblr.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_season_data():
    df = pd.read_csv('2025-26.csv')
    return df.to_dict('records')

@app.get("/")
def read_root():
    return {"message": "Premier League Predictions API"}

@app.get("/season")
def get_season_data():
    """Get raw season data (CSV as JSON)"""
    return load_season_data()