import streamlit as st
import pandas as pd
from pathlib import Path

st.title("Diagnostic Stats")

deliveries_path = Path('data/deliveries.parquet')
matches_path = Path('data/matches.parquet')

if not deliveries_path.exists() or not matches_path.exists():
    st.error("Parquet files not found.")
else:
    df = pd.read_parquet(deliveries_path)
    m_df = pd.read_parquet(matches_path)
    
    # Merge for date sorting
    df = df.merge(m_df[['match_id', 'date']], on='match_id', how='left')
    df['date'] = pd.to_datetime(df['date'])
    
    # Standard definitions
    df['is_batter_ball'] = (df['is_wide'] == 0).astype(int)
    df['is_super_over'] = (df['inning'] > 2).astype(int)
    df = df[df['is_super_over'] == 0]
    
    players = ['KL Rahul', 'MS Dhoni', 'RG Sharma', 'V Kohli']
    
    for player in players:
        st.subheader(f"Stats for {player}")
        p_df = df[df['batter'] == player].copy()
        innings = p_df.groupby(['match_id', 'date']).agg(
            runs=('batsman_runs', 'sum'),
            balls=('is_batter_ball', 'sum')
        ).reset_index().sort_values(by=['date', 'match_id'])
        
        innings['cum_runs'] = innings['runs'].cumsum()
        innings['cum_balls'] = innings['balls'].cumsum()
        innings['inn_count'] = range(1, len(innings) + 1)
        
        milestone = innings[innings['cum_runs'] >= 5000].head(1)
        if not milestone.empty:
            st.write(milestone)
        else:
            st.write(f"Total runs: {innings['cum_runs'].iloc[-1] if not innings.empty else 0}")
        
    st.subheader("Raw Data Sample (KL Rahul)")
    st.write(df[df['batter'] == 'KL Rahul'].head(20))
