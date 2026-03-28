import streamlit as st
import pandas as pd
from pathlib import Path

PROCESSED_DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data(v="3.0"):
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
    
    # --- DEBUT MATCH IDENTIFICATION ---
    # Merge with date to find the absolute chronological first match for each player
    temp_df = deliveries_df.merge(matches_df[['match_id', 'date']], on='match_id', how='left')
    temp_df = temp_df.sort_values(by=['date', 'match_id'])
    
    # Find the first match for each batter
    first_match_batter = temp_df.groupby('batter')['match_id'].first().to_dict()
    # Find the first match for each bowler
    first_match_bowler = temp_df.groupby('bowler')['match_id'].first().to_dict()
    
    # Mark debut matches in the main deliveries_df using vectorized mapping for performance
    deliveries_df['is_batter_debut'] = deliveries_df['match_id'] == deliveries_df['batter'].map(first_match_batter)
    deliveries_df['is_bowler_debut'] = deliveries_df['match_id'] == deliveries_df['bowler'].map(first_match_bowler)
    
    # --- BOWLER WICKETS LOGIC ---
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    deliveries_df['is_bowler_wicket'] = ((deliveries_df['is_wicket'] == 1) & (~deliveries_df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    
    return matches_df, deliveries_df
