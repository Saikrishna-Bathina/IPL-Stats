import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__name__))))
from data_loader import load_data

st.set_page_config(page_title="Debut Records", page_icon="🌟", layout="wide")
st.title("🌟 IPL Debut Match Records")
st.caption("Performances in each player's very first IPL match.")

@st.cache_data
def load_all_data():
    return load_data(v="3.0")

try:
    matches_df, deliveries_df = load_all_data()
except Exception as e:
    st.error(f"Please run data processor first. {e}")
    st.stop()

# --- 1. Batting Debut Records ---
st.markdown("## 🏏 Batting Performance on Debut")

@st.cache_data
def get_debut_batting_stats(df, matches_df):
    # Filter for debut matches only
    debut_df = df[df['is_batter_debut'] == True].copy()
    if debut_df.empty:
        return pd.DataFrame()
        
    # Aggregate by match and batter
    debut_scores = debut_df.groupby(['match_id', 'batter', 'batting_team', 'bowling_team']).agg(
        runs=('batsman_runs', 'sum'),
        balls=('is_batter_ball', 'sum')
    ).reset_index()
    
    # Merge with matches for season and venue
    debut_scores = debut_scores.merge(matches_df[['match_id', 'season', 'venue', 'date']], on='match_id', how='left')
    return debut_scores.sort_values(by=['runs', 'date'], ascending=[False, True])

debut_batting = get_debut_batting_stats(deliveries_df, matches_df)

if debut_batting.empty:
    st.info("No debut batting data found.")
else:
    st.subheader("Highest Scores on IPL Debut")
    st.dataframe(debut_batting.head(20).set_index('batter')[['runs', 'balls', 'batting_team', 'bowling_team', 'season', 'venue']], width='stretch')

# --- 2. Debut Milestones (Fastest 50/100) ---
st.markdown("---")
st.subheader("⚡ Fastest Milestones on Debut")

@st.cache_data
def get_debut_milestones(df, target, matches_df):
    debut_df = df[df['is_batter_debut'] == True].copy()
    if debut_df.empty:
        return pd.DataFrame()
    
    # Sort ball by ball
    debut_df = debut_df.sort_values(by=['match_id', 'inning', 'over', 'ball'])
    debut_df['cum_runs'] = debut_df.groupby(['match_id', 'batter'])['batsman_runs'].cumsum()
    debut_df['cum_balls'] = debut_df.groupby(['match_id', 'batter'])['is_batter_ball'].cumsum()
    
    reached = debut_df[debut_df['cum_runs'] >= target].groupby(['match_id', 'batter']).first().reset_index()
    reached = reached.merge(matches_df[['match_id', 'season', 'venue', 'date']], on='match_id', how='left')
    return reached.sort_values(by=['cum_balls', 'date'], ascending=[True, True])

m_col1, m_col2 = st.columns(2)
with m_col1:
    st.markdown("#### Fastest 50 on Debut")
    d_50s = get_debut_milestones(deliveries_df, 50, matches_df)
    if not d_50s.empty:
        st.dataframe(d_50s[['batter', 'cum_balls', 'season', 'venue']].set_index('batter'), width='stretch')
    else:
        st.write("No one scored a 50 on debut in this dataset.")

with m_col2:
    st.markdown("#### Fastest 100 on Debut")
    d_100s = get_debut_milestones(deliveries_df, 100, matches_df)
    if not d_100s.empty:
        st.dataframe(d_100s[['batter', 'cum_balls', 'season', 'venue']].set_index('batter'), width='stretch')
    else:
        st.write("No one scored a 100 on debut in this dataset.")

# --- 3. Bowling Debut Records ---
st.markdown("---")
st.markdown("## ⚾ Bowling Performance on Debut")

@st.cache_data
def get_debut_bowling_stats(df, matches_df):
    # Filter for debut matches only
    debut_df = df[df['is_bowler_debut'] == True].copy()
    if debut_df.empty:
        return pd.DataFrame()
        
    # Aggregate by match and bowler
    debut_wickets = debut_df.groupby(['match_id', 'bowler', 'bowling_team', 'batting_team']).agg(
        wickets=('is_bowler_wicket', 'sum'),
        runs_conceded=('total_runs', 'sum'), # Note: technically includes non-bowler extras but usually used for simplicity in summaries
        balls=('is_bowler_ball', 'sum'),
        legbyes=('is_legbye', 'sum'),
        byes=('is_bye', 'sum'),
        penalty=('is_penalty', 'sum')
    ).reset_index()
    
    # Precise bowler runs: subtract byes, legbyes, penalties
    debut_wickets['bowler_runs'] = debut_wickets['runs_conceded'] - debut_wickets['legbyes'] - debut_wickets['byes'] - debut_wickets['penalty']
    debut_wickets['overs'] = (debut_wickets['balls'] // 6).astype(str) + "." + (debut_wickets['balls'] % 6).astype(str)
    debut_wickets['figures'] = debut_wickets['wickets'].astype(str) + "/" + debut_wickets['bowler_runs'].astype(str)
    
    # Merge with matches
    debut_wickets = debut_wickets.merge(matches_df[['match_id', 'season', 'venue', 'date']], on='match_id', how='left')
    return debut_wickets.sort_values(by=['wickets', 'bowler_runs', 'date'], ascending=[False, True, True])

debut_bowling = get_debut_bowling_stats(deliveries_df, matches_df)

if debut_bowling.empty:
    st.info("No debut bowling data found.")
else:
    st.subheader("Best Bowling Figures on IPL Debut")
    st.dataframe(debut_bowling.head(20).set_index('bowler')[['figures', 'overs', 'bowling_team', 'batting_team', 'season', 'venue']], width='stretch')
