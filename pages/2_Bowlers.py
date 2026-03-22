import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data

st.set_page_config(page_title="Bowler Stats", page_icon="🏏", layout="wide")
st.title("🏏 Bowlers Dashboard")

@st.cache_data
def load_all_data():
    return load_data()

try:
    matches_df, deliveries_df = load_all_data()
except Exception as e:
    st.error(f"Please run data processor first. {e}")
    st.stop()


# Filters
st.sidebar.header("Filter Data")
teams = sorted([t for t in matches_df['team1'].dropna().unique()])
def_team = st.sidebar.selectbox("For Team (Bowling Team)", ["All"] + teams)
vs_team = st.sidebar.selectbox("Vs Team (Batting Team)", ["All"] + teams)
bowler_name = st.sidebar.text_input("Bowler Name (Leave empty for all)")

grounds = sorted([g for g in matches_df['venue'].dropna().unique()])
ground = st.sidebar.selectbox("Venue", ["All"] + grounds)

years = sorted([str(y) for y in matches_df['season'].dropna().unique() if str(y).strip() != ''])
year = st.sidebar.selectbox("Year", ["All"] + years)

merged_df = deliveries_df.merge(matches_df[['match_id', 'season', 'venue']], on='match_id', how='left')
filtered_df = merged_df.copy()

if def_team != "All":
    filtered_df = filtered_df[filtered_df['bowling_team'] == def_team]
if vs_team != "All":
    filtered_df = filtered_df[filtered_df['batting_team'] == vs_team]
if bowler_name != "":
    filtered_df = filtered_df[filtered_df['bowler'].str.contains(bowler_name, case=False, na=False)]
if ground != "All":
    filtered_df = filtered_df[filtered_df['venue'] == ground]
if year != "All":
    filtered_df = filtered_df[filtered_df['season'] == year]


# --- 1. Career Wicket Milestones ---
st.markdown("## Fastest & Slowest Wicket Milestones")
st.caption("Respects sidebar filters (e.g., fastest to 50 wickets for MI against CSK)")
wicket_target = st.selectbox("Select Wickets Milestone", [50, 100, 150, 200, 250])

@st.cache_data
def get_fastest_wickets(df, target):
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    df['is_bowler_wicket'] = ((df['is_wicket'] == 1) & (~df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    
    innings_stats = df.groupby(['match_id', 'bowler', 'season']).agg(
        wickets=('is_bowler_wicket', 'sum'),
        balls=('is_bowler_ball', 'sum')
    ).reset_index()
    
    innings_stats = innings_stats.sort_values(by=['season', 'match_id'])
    innings_stats['career_wickets'] = innings_stats.groupby('bowler')['wickets'].cumsum()
    innings_stats['career_balls'] = innings_stats.groupby('bowler')['balls'].cumsum()
    innings_stats['innings_played'] = innings_stats.groupby('bowler').cumcount() + 1
    
    reached = innings_stats[innings_stats['career_wickets'] >= target].groupby('bowler').first().reset_index()
    return reached[['bowler', 'career_wickets', 'career_balls', 'innings_played']]

with st.spinner("Calculating Wicket Milestones..."):
    wk_df = get_fastest_wickets(filtered_df, wicket_target)
    
if wk_df.empty:
    st.info(f"No bowler has reached {wicket_target} wickets with these filters.")
else:
    t1, t2 = st.tabs(["By Innings", "By Balls"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Fastest to {wicket_target} Wickets")
            st.dataframe(wk_df.sort_values(by='innings_played').head(15).set_index('bowler'), width='stretch')
        with c2:
            st.subheader(f"Slowest to {wicket_target} Wickets")
            st.dataframe(wk_df.sort_values(by='innings_played', ascending=False).head(15).set_index('bowler'), width='stretch')
    with t2:
        c3, c4 = st.columns(2)
        with c3:
            st.subheader(f"Fastest to {wicket_target} Wickets")
            st.dataframe(wk_df.sort_values(by='career_balls').head(15).set_index('bowler'), width='stretch')
        with c4:
            st.subheader(f"Slowest to {wicket_target} Wickets")
            st.dataframe(wk_df.sort_values(by='career_balls', ascending=False).head(15).set_index('bowler'), width='stretch')


# --- 2. Most Wickets (Current Filters) ---
st.markdown("---")
st.markdown("## Aggregate Wickets (Filtered)")
st.caption("Shows top wicket-takers matching your current filters (Team, Vs Team, Ground, Year)")

@st.cache_data
def get_filtered_wickets(df):
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    df['is_bowler_wicket'] = ((df['is_wicket'] == 1) & (~df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    
    agg = df.groupby('bowler').agg(
        total_wickets=('is_bowler_wicket', 'sum'),
        balls_bowled=('is_bowler_ball', 'sum')
    ).reset_index()
    return agg[agg['total_wickets'] > 0].sort_values(by='total_wickets', ascending=False)

st.dataframe(get_filtered_wickets(filtered_df).head(20).set_index('bowler'), width='stretch')


# --- 3. All-Time & Franchise Wicket Records ---
st.markdown("---")
st.markdown("## All-Time Highest Wicket Takers")
st.caption("These stats ignore sidebar filters.")

@st.cache_data
def most_wickets_overall(df):
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    df['is_bowler_wicket'] = ((df['is_wicket'] == 1) & (~df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    return df.groupby('bowler')['is_bowler_wicket'].sum().reset_index().sort_values(by='is_bowler_wicket', ascending=False)

@st.cache_data
def most_wickets_for_team(df):
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    df['is_bowler_wicket'] = ((df['is_wicket'] == 1) & (~df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    
    wkts = df.groupby(['bowling_team', 'bowler'])['is_bowler_wicket'].sum().reset_index()
    return wkts[wkts['is_bowler_wicket'] > 0].sort_values(by='is_bowler_wicket', ascending=False)

ca1, ca2 = st.columns(2)
with ca1:
    st.subheader("Most Wickets in IPL")
    st.dataframe(most_wickets_overall(merged_df).head(20).set_index('bowler'), width='stretch')
with ca2:
    st.subheader("Most Wickets for a Single Franchise")
    st.dataframe(most_wickets_for_team(merged_df).head(20).set_index(['bowling_team', 'bowler']), width='stretch')


# --- 4. Fastest 5-Wicket Hauls ---
st.markdown("---")
st.markdown("## Fastest 5-Wicket Hauls in an Innings")
@st.cache_data
def get_five_wicket_hauls(df):
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    df['is_bowler_wicket'] = ((df['is_wicket'] == 1) & (~df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    
    df = df.sort_values(by=['match_id', 'inning', 'over', 'ball'])
    
    df['innings_runs_conceded'] = df.groupby(['match_id', 'inning', 'bowler'])['total_runs'].cumsum() - df.groupby(['match_id', 'inning', 'bowler'])['is_legbye'].cumsum() - df.groupby(['match_id', 'inning', 'bowler'])['is_bye'].cumsum()
    df['innings_balls_bowled'] = df.groupby(['match_id', 'inning', 'bowler'])['is_bowler_ball'].cumsum()
    df['innings_wickets'] = df.groupby(['match_id', 'inning', 'bowler'])['is_bowler_wicket'].cumsum()
    
    five_wkt = df[df['innings_wickets'] == 5].groupby(['match_id', 'inning', 'bowler']).first().reset_index()
    return five_wkt[['bowler', 'batting_team', 'venue', 'season', 'innings_balls_bowled', 'innings_runs_conceded']]

with st.spinner("Calculating 5-Wicket Hauls..."):
    fifer_df = get_five_wicket_hauls(filtered_df)
    
if fifer_df.empty:
    st.info("No 5-wicket hauls found.")
else:
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("Fastest to 5-Wicket Haul (By Balls)")
        st.dataframe(fifer_df.sort_values(by='innings_balls_bowled').head(10).set_index('bowler'), width='stretch')
    with c6:
        st.subheader("Most Economical 5-Wicket Haul (By Runs)")
        st.dataframe(fifer_df.sort_values(by='innings_runs_conceded').head(10).set_index('bowler'), width='stretch')
