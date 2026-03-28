import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data

st.set_page_config(page_title="Batter Stats", page_icon="🏏", layout="wide")
st.title("🏏 Batters Dashboard")

@st.cache_data
def load_all_data():
    return load_data(v="2.1")

try:
    matches_df, deliveries_df = load_all_data()
except Exception as e:
    st.error(f"Please run data processor first. {e}")
    st.stop()
    
# Process Batting Position
@st.cache_data
def get_batting_positions(df):
    first_ball = df.groupby(['match_id', 'inning', 'batter']).first().reset_index()
    first_ball['batting_position'] = first_ball.groupby(['match_id', 'inning'])['ball'].rank(method='first').astype(int)
    return first_ball[['match_id', 'inning', 'batter', 'batting_position']]

# Filter Section
st.sidebar.header("Filter Data")
teams = sorted([t for t in matches_df['team1'].dropna().unique()])
def_team = st.sidebar.selectbox("For Team", ["All"] + teams)
vs_team = st.sidebar.selectbox("Vs Team", ["All"] + teams)
batter_name = st.sidebar.text_input("Batter Name (Leave empty for all)")
grounds = sorted([g for g in matches_df['venue'].dropna().unique()])
ground = st.sidebar.selectbox("Ground", ["All"] + grounds)
years = sorted([str(y) for y in matches_df['season'].dropna().unique() if str(y).strip() != ''])
year = st.sidebar.selectbox("Year", ["All"] + years)

# Get positions and merge
positions_df = get_batting_positions(deliveries_df)
merged_df = deliveries_df.merge(positions_df, on=['match_id', 'inning', 'batter'], how='left')
merged_df = merged_df.merge(matches_df[['match_id', 'season', 'venue']], on='match_id', how='left')

# GLOBAL FIX: Exclude Super Overs from all player stats as they don't count towards career records
merged_df = merged_df[merged_df['is_super_over'] == 0]

positions = sorted([int(p) for p in merged_df['batting_position'].dropna().unique()])
bat_pos = st.sidebar.selectbox("Batting Position", ["All"] + [str(p) for p in positions])

# Apply filters
filtered_df = merged_df.copy()
if def_team != "All":
    filtered_df = filtered_df[filtered_df['batting_team'] == def_team]
if vs_team != "All":
    filtered_df = filtered_df[filtered_df['bowling_team'] == vs_team]
if batter_name != "":
    filtered_df = filtered_df[filtered_df['batter'].str.contains(batter_name, case=False, na=False)]
if ground != "All":
    filtered_df = filtered_df[filtered_df['venue'] == ground]
if year != "All":
    filtered_df = filtered_df[filtered_df['season'] == year]
if bat_pos != "All":
    filtered_df = filtered_df[filtered_df['batting_position'] == int(bat_pos)]

# --- 1. Fastest / Slowest 50s, 100s, 150s ---
st.markdown("## Fastest & Slowest Milestones (Innings)")
st.caption("Filters applied: Team, Vs Team, Ground, Year, Batting Position")
milestone_type = st.radio("Select Milestone", ["50s", "100s", "150s"], horizontal=True)
target_runs = int(milestone_type.replace("s", ""))

@st.cache_data
def get_inning_milestones(df, target):
    df = df.sort_values(by=['match_id', 'inning', 'over', 'ball'])
    df['cumulative_runs'] = df.groupby(['match_id', 'inning', 'batter'])['batsman_runs'].cumsum()
    df['cumulative_balls'] = df.groupby(['match_id', 'inning', 'batter'])['is_batter_ball'].cumsum()
    
    reached = df[df['cumulative_runs'] >= target].groupby(['match_id', 'inning', 'batter']).first().reset_index()
    return reached[['batter', 'batting_team', 'bowling_team', 'venue', 'season', 'batting_position', 'cumulative_runs', 'cumulative_balls']]

with st.spinner("Calculating..."):
    milestone_df = get_inning_milestones(filtered_df, target_runs)
    
if milestone_df.empty:
    st.info(f"No records found for {target_runs} runs with the selected filters.")
else:
    col1, col2 = st.columns(2)
    disp_cols = ['batter', 'cumulative_balls', 'cumulative_runs', 'batting_team', 'bowling_team', 'venue', 'season', 'batting_position']
    with col1:
        st.subheader(f"Fastest {milestone_type} (by balls)")
        fastest = milestone_df.sort_values(by='cumulative_balls').head(15)
        st.dataframe(fastest[disp_cols], width='stretch')
    with col2:
        st.subheader(f"Slowest {milestone_type} (by balls)")
        slowest = milestone_df.sort_values(by='cumulative_balls', ascending=False).head(15)
        st.dataframe(slowest[disp_cols], width='stretch')


# --- 2. Most 6s, 4s for a team and against a team (Using Filters) ---
st.markdown("---")
st.markdown("## Career Aggregates (Runs, 4s, 6s)")
st.caption("These stats respect the filters you've set in the sidebar (e.g. For Team, Vs Team, Venue).")

@st.cache_data
def get_filtered_aggregates(df):
    df['is_four'] = (df['batsman_runs'] == 4).astype(int)
    df['is_six'] = (df['batsman_runs'] == 6).astype(int)
    
    agg = df.groupby('batter').agg(
        total_runs=('batsman_runs', 'sum'),
        total_4s=('is_four', 'sum'),
        total_6s=('is_six', 'sum'),
        balls_faced=('is_batter_ball', 'sum')
    ).reset_index()
    return agg[agg['total_runs'] > 0]

with st.spinner("Calculating Aggregates..."):
    agg_df = get_filtered_aggregates(filtered_df)

if agg_df.empty:
    st.info("No data available for the selected filters.")
else:
    t1, t2, t3 = st.tabs(["Most Runs", "Most 4s", "Most 6s"])
    with t1:
        st.dataframe(agg_df.sort_values(by='total_runs', ascending=False).head(20).set_index('batter'), width='stretch')
    with t2:
        st.dataframe(agg_df.sort_values(by='total_4s', ascending=False).head(20).set_index('batter'), width='stretch')
    with t3:
        st.dataframe(agg_df.sort_values(by='total_6s', ascending=False).head(20).set_index('batter'), width='stretch')

# --- 3 & 4. Overall Most Runs & Most Runs for Single Franchise ---
st.markdown("---")
st.markdown("## All-Time Highest Run Scorers")
st.caption("These stats are all-time records and ignore the sidebar filters.")

@st.cache_data
def get_all_time_runs(df):
    return df.groupby('batter')['batsman_runs'].sum().reset_index().sort_values(by='batsman_runs', ascending=False)

@st.cache_data
def get_franchise_runs(df):
    return df.groupby(['batting_team', 'batter'])['batsman_runs'].sum().reset_index().sort_values(by='batsman_runs', ascending=False)

c_all1, c_all2 = st.columns(2)
with c_all1:
    st.subheader("Most Runs in IPL (Excl. Super Overs)")
    st.dataframe(get_all_time_runs(merged_df).head(20).set_index('batter'), width='stretch')
with c_all2:
    st.subheader("Most Runs for a Single Franchise (Excl. Super Overs)")
    st.dataframe(get_franchise_runs(merged_df).head(20).set_index(['batting_team', 'batter']), width='stretch')


# --- 5. Career Run Milestones (Fastest to X Runs) ---
st.markdown("---")
st.markdown("## Career Run Milestones (Fastest to X Runs)")
st.caption("Respects sidebar filters (e.g., fastest to 1000 runs against CSK)")
runs_milestone = st.selectbox("Select Career Runs Milestone", [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000])

@st.cache_data
def get_career_milestones(df, target, matches_df):
    # Ensure true chronological order by merging with match dates
    df = df.merge(matches_df[['match_id', 'date']], on='match_id', how='left')
    # Use date, match_id, inning, over, and ball for precise career sequence
    df = df.sort_values(by=['date', 'match_id', 'inning', 'over', 'ball'])
    
    # Calculate unique innings: a player has "played an innings" if they were at the crease 
    # (either as a batter or as a non-striker) in a match.
    at_crease = pd.concat([
        df[['match_id', 'date', 'batter']].rename(columns={'batter': 'player'}),
        df[['match_id', 'date', 'non_striker']].rename(columns={'non_striker': 'player'})
    ]).drop_duplicates()
    at_crease = at_crease.sort_values(by=['date', 'match_id'])
    at_crease['innings_rank'] = at_crease.groupby('player').cumcount() + 1
    
    # Process milestones for each player
    results = []
    unique_batters = df['batter'].unique()
    
    for batter in unique_batters:
        # Get only the balls faced by this batter
        p_df = df[df['batter'] == batter].copy()
        
        # Merge the total innings rank back to the delivery data
        # This link ensures we have the correct "career innings number" for each match
        player_innings = at_crease[at_crease['player'] == batter][['match_id', 'innings_rank']]
        p_df = p_df.merge(player_innings, on='match_id', how='left')
        
        # Calculate cumulative totals ball-by-ball
        p_df['career_runs'] = p_df['batsman_runs'].cumsum()
        p_df['career_balls'] = p_df['is_batter_ball'].cumsum()
        
        # Find the VERY FIRST ball where the player reaches the target runs
        milestone = p_df[p_df['career_runs'] >= target].head(1)
        
        if not milestone.empty:
            results.append({
                'batter': batter,
                'career_runs': milestone.iloc[0]['career_runs'],
                'career_balls': milestone.iloc[0]['career_balls'],
                'innings_played': milestone.iloc[0]['innings_rank'],
                'season': milestone.iloc[0]['season']
            })
            
    return pd.DataFrame(results)

with st.spinner("Calculating Career Milestones..."):
    # Fix: If we want TRUE career milestones, we should calculate them on the full merged_df (excl. super overs)
    # and then filter the results if the user has specific team/year filters.
    # However, to support "Fastest to reach 1000 against team X", we use the filtered_df.
    # To fix the "Year resets career count" issue, we check if Year filter is applied.
    
    milestone_context_df = filtered_df.copy()
    if year != "All":
        # If year is filtered, we want to know who reached the milestone IN THAT YEAR
        # but using their FULL CAREER inning count.
        # So we calculate milestones on the FULL dataset and then filter the ones reached in 'year'.
        all_milestones = get_career_milestones(merged_df, runs_milestone, matches_df)
        career_ms_df = all_milestones[all_milestones['season'] == year]
    else:
        career_ms_df = get_career_milestones(milestone_context_df, runs_milestone, matches_df)
    
if career_ms_df.empty:
    st.info(f"No records found for {runs_milestone} runs with current filters.")
else:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"Fastest to {runs_milestone} (By Innings)")
        f_innings = career_ms_df.sort_values(by='innings_played').head(10)
        st.dataframe(f_innings.set_index('batter'), width='stretch')
    with c2:
        st.subheader(f"Fastest to {runs_milestone} (By Balls)")
        f_balls = career_ms_df.sort_values(by='career_balls').head(10)
        st.dataframe(f_balls.set_index('batter'), width='stretch')
