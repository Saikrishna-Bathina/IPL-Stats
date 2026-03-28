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
    return load_data(v="2.1")

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

# GLOBAL FIX: Exclude Super Overs from all player stats as they don't count towards career records
merged_df = merged_df[merged_df['is_super_over'] == 0]

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
def get_fastest_wickets(df, target, matches_df):
    # Ensure true chronological order by merging with match dates
    df = df.merge(matches_df[['match_id', 'date']], on='match_id', how='left')
    # Use date, match_id, inning, over, and ball for precise career sequence
    df = df.sort_values(by=['date', 'match_id', 'inning', 'over', 'ball'])
    
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    df['is_bowler_wicket'] = ((df['is_wicket'] == 1) & (~df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    
    # Process milestones for each bowler
    results = []
    unique_bowlers = df['bowler'].unique()
    
    for bowler in unique_bowlers:
        # Get only the balls bowled by this bowler
        p_df = df[df['bowler'] == bowler].copy()
        
        # Calculate cumulative totals ball-by-ball
        p_df['career_wickets'] = p_df['is_bowler_wicket'].cumsum()
        p_df['career_balls'] = p_df['is_bowler_ball'].cumsum()
        
        # Calculate unique innings: a bowler has "played an innings" if they bowled at least one ball
        # Since we are already filtering for p_df (balls bowled by this bowler), 
        # we can just count unique match_ids.
        p_df['innings_rank'] = p_df.groupby('bowler')['match_id'].transform(lambda x: pd.factorize(x)[0] + 1)
        
        # Find the VERY FIRST ball where the bowler reaches the target wickets
        milestone = p_df[p_df['career_wickets'] >= target].head(1)
        
        if not milestone.empty:
            results.append({
                'bowler': bowler,
                'career_wickets': milestone.iloc[0]['career_wickets'],
                'career_balls': milestone.iloc[0]['career_balls'],
                'innings_played': milestone.iloc[0]['innings_rank'],
                'season': milestone.iloc[0]['season']
            })
            
    return pd.DataFrame(results)

with st.spinner("Calculating Wicket Milestones..."):
    if year != "All":
        all_milestones = get_fastest_wickets(merged_df, wicket_target, matches_df)
        wk_df = all_milestones[all_milestones['season'] == year]
    else:
        wk_df = get_fastest_wickets(filtered_df.copy(), wicket_target, matches_df)
    
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
    st.subheader("Most Wickets in IPL (Excl. Super Overs)")
    st.dataframe(most_wickets_overall(merged_df).head(20).set_index('bowler'), width='stretch')
with ca2:
    st.subheader("Most Wickets for a Single Franchise (Excl. Super Overs)")
    st.dataframe(most_wickets_for_team(merged_df).head(20).set_index(['bowling_team', 'bowler']), width='stretch')


# --- 4. Fastest 5-Wicket Hauls ---
st.markdown("---")
st.markdown("## Fastest 5-Wicket Hauls in an Innings")
@st.cache_data
def get_five_wicket_hauls(df, matches_df):
    # Merge for date
    df = df.merge(matches_df[['match_id', 'date']], on='match_id', how='left')
    
    non_bowler_wickets = ['run out', 'retired hurt', 'obstructing the field', 'hit ball twice', 'timed out']
    df['is_bowler_wicket'] = ((df['is_wicket'] == 1) & (~df['dismissal_kind'].isin(non_bowler_wickets))).astype(int)
    
    # Sort chronologically
    df = df.sort_values(by=['date', 'match_id', 'inning', 'over', 'ball'])
    
    # Accurate runs conceded: subtract legbyes, byes, and penalties
    # Note: total_runs = batsman_runs + extra_runs. 
    # Bowler's extras are wides and noballs.
    # Non-bowler extras are legbyes, byes, penalties.
    df['innings_runs_conceded'] = df.groupby(['match_id', 'inning', 'bowler'])['total_runs'].cumsum() - \
                                  df.groupby(['match_id', 'inning', 'bowler'])['is_legbye'].cumsum() - \
                                  df.groupby(['match_id', 'inning', 'bowler'])['is_bye'].cumsum() - \
                                  df.groupby(['match_id', 'inning', 'bowler'])['is_penalty'].cumsum()
                                  
    df['innings_balls_bowled'] = df.groupby(['match_id', 'inning', 'bowler'])['is_bowler_ball'].cumsum()
    df['innings_wickets'] = df.groupby(['match_id', 'inning', 'bowler'])['is_bowler_wicket'].cumsum()
    
    # Corrected fifer logic: get total innings summary for anyone who reached 5 wickets
    # First, identify the bowlers who took 5+ wickets in an innings
    fifer_matches = df[df['innings_wickets'] >= 5].groupby(['match_id', 'inning', 'bowler']).first().reset_index()
    
    # Now get the final summary for those bowler-innings (last delivery of their spell)
    fifer_summary = df.groupby(['match_id', 'inning', 'bowler']).last().reset_index()
    
    # Merge to only include those who reached 5 wickets
    fifers = fifer_summary.merge(fifer_matches[['match_id', 'inning', 'bowler', 'innings_balls_bowled']], on=['match_id', 'inning', 'bowler'], how='inner', suffixes=('', '_at_5th'))
    
    # Renaming for clarity
    fifers['balls_to_5_wickets'] = fifers['innings_balls_bowled_at_5th']
    fifers['final_wickets'] = fifers['innings_wickets']
    fifers['final_runs'] = fifers['innings_runs_conceded']
    fifers['final_overs'] = (fifers['innings_balls_bowled'] / 6).astype(int).astype(str) + "." + (fifers['innings_balls_bowled'] % 6).astype(str)
    fifers['figures'] = fifers['final_wickets'].astype(str) + "/" + fifers['final_runs'].astype(str)
    
    return fifers[['bowler', 'batting_team', 'venue', 'season', 'balls_to_5_wickets', 'final_wickets', 'final_runs', 'figures', 'final_overs']]

with st.spinner("Calculating 5-Wicket Hauls..."):
    fifer_df = get_five_wicket_hauls(filtered_df, matches_df)
    
if fifer_df.empty:
    st.info("No 5-wicket hauls found.")
else:
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("Fastest to 5-Wicket Haul (By Balls)")
        fast_bowlers = fifer_df.sort_values(by='balls_to_5_wickets').head(10).set_index('bowler')
        st.dataframe(fast_bowlers[['batting_team', 'balls_to_5_wickets', 'figures', 'final_overs', 'venue', 'season']], width='stretch')
    with c6:
        st.subheader("Most Economical 5-Wicket Haul (By Runs)")
        # Sort by final runs conceded, then by final overs
        econ_bowlers = fifer_df.sort_values(by=['final_runs', 'final_overs']).head(10).set_index('bowler')
        st.dataframe(econ_bowlers[['batting_team', 'figures', 'final_overs', 'venue', 'season']], width='stretch')
