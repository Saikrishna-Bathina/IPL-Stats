import os
import json
import pandas as pd
import glob
from pathlib import Path

DATA_DIR = Path(__file__).parent / "ipl_json"
PROCESSED_DATA_DIR = Path(__file__).parent / "data"

def process_all_json():
    print("Processing all IPL JSON files...")
    all_files = glob.glob(str(DATA_DIR / "*.json"))
    
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
                    
                    # Determine exact ball number for analytics
                    
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
                    
    matches_df = pd.DataFrame(matches)
    deliveries_df = pd.DataFrame(deliveries)
    
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    print(f"Saving {len(matches_df)} matches and {len(deliveries_df)} deliveries to parquet...")
    
    matches_df.to_parquet(PROCESSED_DATA_DIR / 'matches.parquet', index=False)
    deliveries_df.to_parquet(PROCESSED_DATA_DIR / 'deliveries.parquet', index=False)
    
    print("Data processing complete!")

if __name__ == "__main__":
    process_all_json()
