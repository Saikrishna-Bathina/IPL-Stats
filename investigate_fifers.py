import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"c:\Users\Sai Krishna\OneDrive\Desktop\IPL")
PROCESSED_DATA_DIR = BASE_DIR / "data"

def investigate_fifers():
    df = pd.read_parquet(PROCESSED_DATA_DIR / 'deliveries.parquet')
    matches_df = pd.read_parquet(PROCESSED_DATA_DIR / 'matches.parquet')
    
    # Standard cleanup
    df['is_super_over'] = (df['inning'] > 2).astype(int)
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    df['is_bowler_wicket'] = ((df['is_wicket'] == 1) & (~df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    df['is_bowler_ball'] = ((df['is_wide'] == 0) & (df['is_noball'] == 0)).astype(int)
    
    # Exclude super overs
    df = df[df['is_super_over'] == 0]
    
    # Add date for sorting
    df = df.merge(matches_df[['match_id', 'date']], on='match_id', how='left')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['date', 'match_id', 'inning', 'over', 'ball'])
    
    # Calculate running stats
    grouped = df.groupby(['match_id', 'inning', 'bowler'])
    df['innings_wickets'] = grouped['is_bowler_wicket'].cumsum()
    df['innings_balls'] = grouped['is_bowler_ball'].cumsum()
    df['innings_runs'] = grouped['total_runs'].cumsum() - grouped['is_legbye'].cumsum() - grouped['is_bye'].cumsum() - grouped['is_penalty'].cumsum()
    
    fifers = df[df['innings_wickets'] == 5].groupby(['match_id', 'inning', 'bowler']).first().reset_index()
    
    print("--- Top 10 Fastest 5-Wicket Hauls (By Balls) ---")
    tops_balls = fifers.sort_values(by='innings_balls').head(10)
    print(tops_balls[['bowler', 'innings_balls', 'innings_runs', 'date']])
    
    print("\n--- Top 10 Most Economical 5-Wicket Hauls (By Runs) ---")
    tops_runs = fifers.sort_values(by='innings_runs').head(10)
    print(tops_runs[['bowler', 'innings_balls', 'innings_runs', 'date']])
    
    # Investigate Bumrah specifically
    print("\n--- JJ Bumrah's 5-Wicket Haul Details ---")
    bumrah = df[(df['bowler'] == 'JJ Bumrah') & (df['innings_wickets'] >= 5)].groupby(['match_id']).first().reset_index()
    print(bumrah[['match_id', 'innings_balls', 'innings_runs', 'date']])

if __name__ == "__main__":
    investigate_fifers()
