import pandas as pd
from pathlib import Path

def diagnose():
    deliveries_path = Path('data/deliveries.parquet')
    matches_path = Path('data/matches.parquet')
    
    if not deliveries_path.exists() or not matches_path.exists():
        print("Parquet files not found. Please run process_data.py first.")
        return

    df = pd.read_parquet(deliveries_path)
    m_df = pd.read_parquet(matches_path)
    
    # Merge for date sorting (must be done before at_crease)
    df = df.merge(m_df[['match_id', 'date']], on='match_id', how='left')
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate some derived columns
    df['is_batter_ball'] = (df['is_wide'] == 0).astype(int)
    df['is_super_over'] = (df['inning'] > 2).astype(int)
    df = df[df['is_super_over'] == 0]

    # Calculate unique matches where the player was "at the crease"
    at_crease = pd.concat([
        df[['match_id', 'date', 'batter']].rename(columns={'batter': 'player'}),
        df[['match_id', 'date', 'non_striker']].rename(columns={'non_striker': 'player'})
    ]).drop_duplicates()
    at_crease = at_crease.sort_values(by=['date', 'match_id'])
    at_crease['innings_rank'] = at_crease.groupby('player').cumcount() + 1
    
    players = ['KL Rahul', 'MS Dhoni', 'RG Sharma', 'SK Raina', 'V Kohli', 'DA Warner', 'S Dhawan', 'AB de Villiers', 'AM Rahane']
    
    results = []
    
    for player in players:
        p_df = df[df['batter'] == player].copy()
        if p_df.empty:
            print(f"No data for {player}")
            continue
            
        # Merge the innings_rank back to the deliveries
        player_innings = at_crease[at_crease['player'] == player][['match_id', 'innings_rank']]
        p_df = p_df.merge(player_innings, on='match_id', how='left')
        
        # Cumulative runs and balls ball-by-ball
        p_df = p_df.sort_values(by=['date', 'match_id', 'inning', 'over', 'ball'])
        p_df['career_runs'] = p_df['batsman_runs'].cumsum()
        p_df['career_balls'] = p_df['is_batter_ball'].cumsum()
        
        milestone = p_df[p_df['career_runs'] >= 5000].head(1)
        
        if not milestone.empty:
            results.append({
                'Player': player,
                'Innings': milestone.iloc[0]['innings_rank'],
                'Balls': milestone.iloc[0]['career_balls'],
                'Runs': milestone.iloc[0]['career_runs'],
                'Date': milestone.iloc[0]['date'],
                'Match_ID': milestone.iloc[0]['match_id']
            })
        else:
            total_runs = p_df['career_runs'].iloc[-1]
            results.append({
                'Player': player,
                'Innings': 'N/A',
                'Balls': 'N/A',
                'Runs': total_runs,
                'Date': 'N/A',
                'Match_ID': 'N/A'
            })
            
    print("\n--- Diagnostic Results (By-Ball logic) ---")
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    
    # Check for gaps for KL Rahul
    if 'KL Rahul' in at_crease['player'].values:
        kl_profile = at_crease[at_crease['player'] == 'KL Rahul'].sort_values(by='date')
        print(f"\nKL Rahul first 5 matches in data:")
        print(kl_profile.head(5))
        print(f"KL Rahul total matches at crease: {len(kl_profile)}")

            
    print("\n--- Diagnostic Results (to reach 5000 runs) ---")
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    
    # Check for specific suspicious matches for Rahul (off by 1)
    if 'KL Rahul' in df['batter'].values:
        kl_innings = df[df['batter'] == 'KL Rahul'].groupby(['match_id', 'date'])['batsman_runs'].sum().reset_index()
        kl_innings = kl_innings.sort_values(by=['date', 'match_id'])
        print(f"\nKL Rahul total innings in data: {len(kl_innings)}")
        print("Last 5 innings for KL Rahul:")
        print(kl_innings.tail(5))

if __name__ == "__main__":
    diagnose()
