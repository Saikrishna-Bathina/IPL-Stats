import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data

st.set_page_config(page_title="Team Stats", page_icon="🏏", layout="wide")
st.title("🏏 Teams Dashboard")

@st.cache_data
def load_all_data():
    return load_data(v="3.0")

try:
    matches_df, deliveries_df = load_all_data()
except Exception as e:
    st.error(f"Please run data processor first. {e}")
    st.stop()


# Filters
st.sidebar.header("Filter Data")
teams = sorted([t for t in matches_df['team1'].dropna().unique()])
def_team = st.sidebar.selectbox("Batting Team", ["All"] + teams)
vs_team = st.sidebar.selectbox("Bowling Team", ["All"] + teams)

grounds = sorted([g for g in matches_df['venue'].dropna().unique()])
ground = st.sidebar.selectbox("Venue", ["All"] + grounds)

years = sorted([str(y) for y in matches_df['season'].dropna().unique() if str(y).strip() != ''])
year = st.sidebar.selectbox("Year", ["All"] + years)

merged_df = deliveries_df.merge(matches_df[['match_id', 'season', 'venue']], on='match_id', how='left')

# GLOBAL FIX: Exclude Super Overs from all player/team stats as they don't count towards career records
merged_df = merged_df[merged_df['is_super_over'] == 0]

filtered_df = merged_df.copy()
if def_team != "All":
    filtered_df = filtered_df[filtered_df['batting_team'] == def_team]
if vs_team != "All":
    filtered_df = filtered_df[filtered_df['bowling_team'] == vs_team]
if ground != "All":
    filtered_df = filtered_df[filtered_df['venue'] == ground]
if year != "All":
    filtered_df = filtered_df[filtered_df['season'] == year]


st.markdown("## Team Innings Milestones")
milestone = st.selectbox("Select Team Milestone", [50, 100, 150, 200, 250, 300])

@st.cache_data
def get_team_milestones(df, target):
    df = df.sort_values(by=['match_id', 'inning', 'over', 'ball'])
    
    df['innings_runs'] = df.groupby(['match_id', 'inning', 'batting_team'])['total_runs'].cumsum()
    df['innings_balls'] = df.groupby(['match_id', 'inning', 'batting_team'])['is_bowler_ball'].cumsum()
    df['overs_completed'] = df['innings_balls'] / 6.0
    
    reached = df[df['innings_runs'] >= target].groupby(['match_id', 'inning', 'batting_team']).first().reset_index()
    return reached[['batting_team', 'bowling_team', 'venue', 'season', 'innings_balls', 'overs_completed', 'innings_runs', 'match_id']]

with st.spinner("Calculating Team Milestones..."):
    ms_df = get_team_milestones(filtered_df, milestone)

if ms_df.empty:
    st.info(f"No team reached {milestone} runs with the selected filters.")
else:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"Fastest to {milestone} Runs (By Balls)")
        fast_teams = ms_df.sort_values(by='innings_balls').head(15).set_index('batting_team')
        fast_teams['overs_completed'] = fast_teams['overs_completed'].round(1)
        st.dataframe(fast_teams[['bowling_team', 'innings_balls', 'overs_completed', 'venue', 'season']], width='stretch')
    with c2:
        st.subheader(f"Slowest to {milestone} Runs (By Balls)")
        slow_teams = ms_df.sort_values(by='innings_balls', ascending=False).head(15).set_index('batting_team')
        slow_teams['overs_completed'] = slow_teams['overs_completed'].round(1)
        st.dataframe(slow_teams[['bowling_team', 'innings_balls', 'overs_completed', 'venue', 'season']], width='stretch')

