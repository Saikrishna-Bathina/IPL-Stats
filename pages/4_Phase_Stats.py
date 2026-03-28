import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_data

st.set_page_config(page_title="Phase Stats", page_icon="🏏", layout="wide")
st.title("🏏 Match Phase Statistics")

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


st.markdown("""
### Match Phases:
- **Powerplay**: Overs 1-6
- **Middle Overs**: Overs 7-15
- **Death Overs**: Overs 16-20
""")

@st.cache_data
def get_phase_stats(df):
    # Group by match, inning, team, and phase
    phase_stats = df.groupby(['match_id', 'inning', 'batting_team', 'bowling_team', 'venue', 'season', 'phase']).agg(
        total_runs=('total_runs', 'sum'),
        total_balls=('is_bowler_ball', 'sum'),
        total_wickets=('is_bowler_wicket', 'sum')
    ).reset_index()
    return phase_stats

with st.spinner("Calculating Phase Stats..."):
    phase_df = get_phase_stats(filtered_df)

if phase_df.empty:
    st.info("No stats found for the selected filters.")
    st.stop()

selected_phase = st.selectbox("Select Phase to Analyze", ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"])
perspective = st.radio("Choose Perspective", ["Batting (Runs)", "Bowling (Wickets)"], horizontal=True)

phase_filtered = phase_df[phase_df['phase'] == selected_phase]

if phase_filtered.empty:
    st.info(f"No match data found specifically for {selected_phase}.")
else:
    if perspective == "Batting (Runs)":
        c1, col2 = st.columns(2)
        with c1:
            st.subheader("Highest Runs in This Phase")
            highest = phase_filtered.sort_values(by='total_runs', ascending=False).head(15).set_index('batting_team')
            st.dataframe(highest[['bowling_team', 'total_runs', 'total_balls', 'venue', 'season']], width='stretch')
        with col2:
            st.subheader("Lowest Runs in This Phase")
            if selected_phase == "Powerplay (1-6)": min_balls = 18
            elif selected_phase == "Middle Overs (7-15)": min_balls = 30
            else: min_balls = 15
                
            lowest = phase_filtered[phase_filtered['total_balls'] >= min_balls].sort_values(by='total_runs', ascending=True).head(15).set_index('batting_team')
            st.dataframe(lowest[['bowling_team', 'total_runs', 'total_balls', 'venue', 'season']], width='stretch')

        st.markdown("---")
        st.markdown("### Average Runs per Phase (by Team)")
        avg_df = phase_filtered.groupby('batting_team')['total_runs'].mean().reset_index().sort_values(by='total_runs')
        fig = px.bar(avg_df, x='batting_team', y='total_runs', title=f"Average {selected_phase} Runs by Team", color='total_runs', text_auto='.1f')
        st.plotly_chart(fig, width='stretch')
    else:
        c1, col2 = st.columns(2)
        with c1:
            st.subheader("Most Wickets in This Phase")
            highest_wkts = phase_filtered.sort_values(by='total_wickets', ascending=False).head(15).set_index('bowling_team')
            st.dataframe(highest_wkts[['batting_team', 'total_wickets', 'total_balls', 'venue', 'season']], width='stretch')
        with col2:
            st.subheader("Best Economy in This Phase (Min 12 balls)")
            phase_filtered['economy'] = (phase_filtered['total_runs'] / (phase_filtered['total_balls'] / 6))
            best_econ = phase_filtered[phase_filtered['total_balls'] >= 12].sort_values(by='economy', ascending=True).head(15).set_index('bowling_team')
            st.dataframe(best_econ[['batting_team', 'economy', 'total_runs', 'total_balls', 'venue', 'season']], width='stretch')

        st.markdown("---")
        st.markdown("### Average Wickets per Phase (by Team)")
        avg_wkts = phase_filtered.groupby('bowling_team')['total_wickets'].mean().reset_index().sort_values(by='total_wickets')
        fig = px.bar(avg_wkts, x='bowling_team', y='total_wickets', title=f"Average {selected_phase} Wickets by Team", color='total_wickets', text_auto='.2f')
        st.plotly_chart(fig, width='stretch')

