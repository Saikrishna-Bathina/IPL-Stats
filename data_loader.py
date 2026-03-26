import streamlit as st
import pandas as pd
from pathlib import Path

PROCESSED_DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    matches_df = pd.read_parquet(PROCESSED_DATA_DIR / 'matches.parquet')
    deliveries_df = pd.read_parquet(PROCESSED_DATA_DIR / 'deliveries.parquet')
    
    # Normalize team names
    team_mapping = {
        'Delhi Daredevils': 'Delhi Capitals',
        'Kings XI Punjab': 'Punjab Kings',
        'Rising Pune Supergiant': 'Rising Pune Supergiants',
    }
    
    matches_df['team1'] = matches_df['team1'].replace(team_mapping)
    matches_df['team2'] = matches_df['team2'].replace(team_mapping)
    matches_df['toss_winner'] = matches_df['toss_winner'].replace(team_mapping)
    matches_df['winner'] = matches_df['winner'].replace(team_mapping)
    
    deliveries_df['batting_team'] = deliveries_df['batting_team'].replace(team_mapping)
    deliveries_df['bowling_team'] = deliveries_df['bowling_team'].replace(team_mapping)
    
    # Calculate some derived columns if needed
    # Like Phase
    def determine_phase(over):
        if over < 6:
            return 'Powerplay (1-6)'
        elif over < 15:
            return 'Middle Overs (7-15)'
        else:
            return 'Death Overs (16-20)'
            
    deliveries_df['phase'] = deliveries_df['over'].apply(determine_phase)
    # Determine absolute balls for strike rate calculations 
    # Batter's ball: excludes only wides (No-balls ARE balls faced)
    deliveries_df['is_batter_ball'] = (deliveries_df['is_wide'] == 0).astype(int)
    # Bowler's ball: excludes both wides and no-balls (Legal deliveries in an over)
    deliveries_df['is_bowler_ball'] = ((deliveries_df['is_wide'] == 0) & (deliveries_df['is_noball'] == 0)).astype(int)
    # Keep is_legal_ball for backward compatibility if needed, aliasing to is_bowler_ball
    deliveries_df['is_legal_ball'] = deliveries_df['is_bowler_ball']
    
    # Identify Super Overs (Innings 3 and above)
    deliveries_df['is_super_over'] = (deliveries_df['inning'] > 2).astype(int)
    
    # Ensure date is datetime for accurate sorting
    matches_df['date'] = pd.to_datetime(matches_df['date'])
    
    return matches_df, deliveries_df
