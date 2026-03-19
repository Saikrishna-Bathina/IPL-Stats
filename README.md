# 🏏 IPL Advanced Analytics Dashboard (2008-2025)

A comprehensive, interactive analytics dashboard for Indian Premier League (IPL) data, built with **Python**, **Streamlit**, **Pandas**, and **Plotly**. This dashboard provides deep insights into match performances, player stats, and historical trends from the inception of IPL through the 2025 season.

🚀 **Live Demo:** [Deploy your app to see the link here]

## 📊 Features

### 1. 🏠 Home
- Quick overview of total matches, deliveries, and runs scored.
- Easy navigation to specialized analytics pages.

### 2. 🏏 Batters Analytics
- **Milestone Tracker:** Fastest to 50s, 100s, and career run milestones.
- **Strike Rate Analysis:** Performance vs. specific teams.
- **Boundary Stats:** Analysis of sixes and fours by season.

### 3. 🥎 Bowlers Analytics
- **Wicket Milestones:** Fastest to reach 50, 100, 150, and 200 wickets.
- **Impact Stats:** 5-wicket hauls and season-wise performance.
- **Team-specific Stats:** Bowlers' performance against specific franchises.

### 4. 🏘️ Team Analytics
- **Scoring Trends:** Fastest and slowest scoring milestones (50, 100, 150, 200, 250 runs) by team and season.
- **Historical Comparison:** Head-to-head metrics and season-wise growth.

### 5. ⏱️ Phase Statistics
- **Powerplay (1-6 overs):** Analyzing the early aggression.
- **Middle Overs (7-15 overs):** Tactical consolidation and wicket-taking.
- **Death Overs (16-20 overs):** High-stakes finish and scoring rates.

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Data Processing:** [Pandas](https://pandas.pydata.org/), [Pyarrow](https://arrow.apache.org/docs/python/index.html)
- **Visualizations:** [Plotly](https://plotly.com/python/)
- **Data Format:** Parquet (for optimized performance)

## ⚙️ Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Saikrishna-Bathina/IPL-Stats.git
   cd IPL-Stats
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Process Data (Optional - if JSON files are updated):**
   ```bash
   python process_data.py
   ```

4. **Run the Dashboard:**
   ```bash
   streamlit run Home.py
   ```

## 📂 Data Source

The raw data is sourced in JSON format (Cricsheet/IPL official) and processed into efficient Parquet files using the `process_data.py` script.

## 🤝 Contributing

Feel free to fork this project, open issues, or submit pull requests for new features!

---
Developed by [Saikrishna Bathina](https://github.com/Saikrishna-Bathina)
