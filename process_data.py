import os
import json
import pandas as pd
import glob
import numpy as np
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
JSON_DATA_DIR = BASE_DIR / "ipl_json"
CSV_DATA_DIR = BASE_DIR / "kaggle-ipl"
PROCESSED_DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"dataset_type": "json"}

def process_all_json():
    print("Processing all IPL JSON files...")
    all_files = glob.glob(str(JSON_DATA_DIR / "*.json"))
    
    matches = []
    deliveries = []
    
    for file_path in all_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        info = data.get('info', {})
        match_id = Path(file_path).stem
        
        # Parse match info
        match_info = {
            'match_id': match_id,
            'season': str(info.get('season', '')),
            'city': info.get('city'),
            'date': info.get('dates', [None])[0],
            'team1': info.get('teams', [None, None])[0],
            'team2': info.get('teams', [None, None])[1],
            'toss_winner': info.get('toss', {}).get('winner'),
            'toss_decision': info.get('toss', {}).get('decision'),
            'winner': info.get('outcome', {}).get('winner'),
            'result': 'runs' if 'runs' in info.get('outcome', {}).get('by', {}) else ('wickets' if 'wickets' in info.get('outcome', {}).get('by', {}) else 'tie/no result'),
            'result_margin': info.get('outcome', {}).get('by', {}).get('runs') or info.get('outcome', {}).get('by', {}).get('wickets'),
            'player_of_match': info.get('player_of_match', [None])[0],
            'venue': info.get('venue')
        }
        matches.append(match_info)
        
        # Parse delivery info
        innings_data = data.get('innings', [])
        for inning_idx, inning in enumerate(innings_data):
            batting_team = inning.get('team')
            # Extract bowling team by finding the other team
            bowling_team = match_info['team1'] if batting_team == match_info['team2'] else match_info['team2']
            
            for over in inning.get('overs', []):
                over_num = over.get('over')
                for ball_num, delivery in enumerate(over.get('deliveries', [])):
                    runs = delivery.get('runs', {})
                    extras = delivery.get('extras', {})
                    wickets = delivery.get('wickets', [])
                    
                    is_wicket = 1 if len(wickets) > 0 else 0
                    player_dismissed = wickets[0].get('player_out') if is_wicket else None
                    dismissal_kind = wickets[0].get('kind') if is_wicket else None
                    fielder = wickets[0].get('fielders', [{}])[0].get('name') if is_wicket and 'fielders' in wickets[0] else None
                    
                    deliv_info = {
                        'match_id': match_id,
                        'inning': inning_idx + 1,
                        'batting_team': batting_team,
                        'bowling_team': bowling_team,
                        'over': over_num,
                        'ball': ball_num + 1,
                        'batter': delivery.get('batter'),
                        'bowler': delivery.get('bowler'),
                        'non_striker': delivery.get('non_striker'),
                        'batsman_runs': runs.get('batter', 0),
                        'extra_runs': runs.get('extras', 0),
                        'total_runs': runs.get('total', 0),
                        'is_wicket': is_wicket,
                        'player_dismissed': player_dismissed,
                        'dismissal_kind': dismissal_kind,
                        'fielder': fielder,
                        'is_wide': 1 if 'wides' in extras else 0,
                        'is_noball': 1 if 'noballs' in extras else 0,
                        'is_legbye': 1 if 'legbyes' in extras else 0,
                        'is_bye': 1 if 'byes' in extras else 0,
                        'is_penalty': 1 if 'penalty' in extras else 0
                    }
                    deliveries.append(deliv_info)
                    
    save_to_parquet(matches, deliveries)

def process_all_csv():
    print("Processing all IPL CSV files from Kaggle...")
    matches_csv = CSV_DATA_DIR / "matches_updated_ipl_upto_2025.csv"
    deliveries_csv = CSV_DATA_DIR / "deliveries_updated_ipl_upto_2025.csv"
    
    if not matches_csv.exists() or not deliveries_csv.exists():
        print(f"Error: Required CSV files not found in {CSV_DATA_DIR}")
        return

    # Read matches
    m_df = pd.read_csv(matches_csv)
    # Map columns to matches schema
    matches_df = pd.DataFrame()
    matches_df['match_id'] = m_df['matchId'].astype(str)
    matches_df['season'] = m_df['season'].astype(str)
    matches_df['city'] = m_df['city']
    matches_df['date'] = m_df['date']
    matches_df['team1'] = m_df['team1']
    matches_df['team2'] = m_df['team2']
    matches_df['toss_winner'] = m_df['toss_winner']
    matches_df['toss_decision'] = m_df['toss_decision']
    matches_df['winner'] = m_df['winner']
    
    # Deriving result and result_margin
    matches_df['result'] = np.where(m_df['winner_runs'] > 0, 'runs', 
                            np.where(m_df['winner_wickets'] > 0, 'wickets', 'tie/no result'))
    matches_df['result_margin'] = m_df['winner_runs'].fillna(0) + m_df['winner_wickets'].fillna(0)
    
    matches_df['player_of_match'] = m_df['player_of_match']
    matches_df['venue'] = m_df['venue']

    # Read deliveries
    d_df = pd.read_csv(deliveries_csv)
    # Map columns to deliveries schema
    deliveries_df = pd.DataFrame()
    deliveries_df['match_id'] = d_df['matchId'].astype(str)
    deliveries_df['inning'] = d_df['inning']
    deliveries_df['batting_team'] = d_df['batting_team']
    deliveries_df['bowling_team'] = d_df['bowling_team']
    deliveries_df['over'] = d_df['over']
    deliveries_df['ball'] = d_df['ball']
    deliveries_df['batter'] = d_df['batsman']
    deliveries_df['bowler'] = d_df['bowler']
    deliveries_df['non_striker'] = d_df['non_striker']
    deliveries_df['batsman_runs'] = d_df['batsman_runs'].fillna(0)
    deliveries_df['extra_runs'] = d_df['extras'].fillna(0)
    deliveries_df['total_runs'] = deliveries_df['batsman_runs'] + deliveries_df['extra_runs']
    
    deliveries_df['is_wicket'] = np.where(d_df['player_dismissed'].notnull(), 1, 0)
    deliveries_df['player_dismissed'] = d_df['player_dismissed']
    deliveries_df['dismissal_kind'] = d_df['dismissal_kind']
    deliveries_df['fielder'] = None # Not present in this CSV
    
    deliveries_df['is_wide'] = np.where(d_df['isWide'].notnull(), 1, 0)
    deliveries_df['is_noball'] = np.where(d_df['isNoBall'].notnull(), 1, 0)
    deliveries_df['is_legbye'] = np.where(d_df['LegByes'].notnull(), 1, 0)
    deliveries_df['is_bye'] = np.where(d_df['Byes'].notnull(), 1, 0)
    deliveries_df['is_penalty'] = np.where(d_df['Penalty'].notnull(), 1, 0)

    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    print(f"Saving {len(matches_df)} matches and {len(deliveries_df)} deliveries to parquet...")
    matches_df.to_parquet(PROCESSED_DATA_DIR / 'matches.parquet', index=False)
    deliveries_df.to_parquet(PROCESSED_DATA_DIR / 'deliveries.parquet', index=False)
    print("Data processing complete!")

def save_to_parquet(matches, deliveries):
    matches_df = pd.DataFrame(matches)
    deliveries_df = pd.DataFrame(deliveries)
    
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    print(f"Saving {len(matches_df)} matches and {len(deliveries_df)} deliveries to parquet...")
    
    matches_df.to_parquet(PROCESSED_DATA_DIR / 'matches.parquet', index=False)
    deliveries_df.to_parquet(PROCESSED_DATA_DIR / 'deliveries.parquet', index=False)
    
    print("Data processing complete!")

if __name__ == "__main__":
    config = load_config()
    if config.get("dataset_type") == "csv":
        process_all_csv()
    else:
        process_all_json()
