import pandas as pd

try:
    df = pd.read_parquet('data/matches.parquet')
    teams = list(df['team1'].dropna().unique())
    print("Unique Teams:")
    for t in sorted(teams):
        print(" -", t)
    
    print("\nMax Season:", df['season'].max())
    print("Min Season:", df['season'].min())
except Exception as e:
    print(e)
