import streamlit as st
from data_loader import load_data

st.set_page_config(
    page_title="IPL Dashboard Analytics (2008-2025)",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏏 IPL Advanced Analytics Dashboard")
st.markdown("""
Welcome to the Comprehensive IPL Analytics Dashboard! This application provides deep insights into the Indian Premier League matches from 2008 to the most recent season (2025 data included).

### Use the Sidebar to Navigate:

1. **Batters**: Visualize fastest milestones, 50s, 100s, specific team performances.
2. **Bowlers**: Analyze fastest wicket milestones, 5-wicket hauls.
3. **Teams**: View team-wide fastest and slowest scoring milestones.
4. **Phase Stats**: Explore powerplays, middle overs, and death overs statistics.

**Built with Python, Streamlit, Pandas, and Plotly.**
""")

try:
    with st.spinner("Loading Data..."):
        matches_df, deliveries_df = load_data()
        
    st.success(f"Successfully loaded {len(matches_df)} matches and {len(deliveries_df)} deliveries!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Matches", len(matches_df))
    # Filter for standard career deliveries (excl. super overs)
    career_deliveries = deliveries_df[deliveries_df['is_super_over'] == 0]
    col2.metric("Total Career Deliveries", len(career_deliveries))
    col3.metric("Total Career Runs Scored", int(career_deliveries['total_runs'].sum()))
        
except Exception as e:
    st.error(f"Error loading data: {e}\nPlease process the JSON files first by running `python process_data.py`.")
