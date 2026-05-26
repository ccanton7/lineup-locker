import streamlit as st
import pandas as pd
import numpy as np
import requests

# Set page layout to wide for easy sports data viewing
st.set_page_config(page_title="Lineup Locker", layout="wide")

st.title("🔒 Lineup Locker")
st.write("Professional-grade asset tracking and trend dampening for your fantasy league.")

# 1. User Inputs League ID
default_league = "p4jlxofwmg5kgkd4"
league_id = st.text_input("Enter your Fantrax League ID:", value=default_league)

@st.cache_data(ttl=3600)  # Caches the data for 1 hour so it loads instantly
def load_league_data(id):
    # This URL connects directly to the Fantrax public-facing tables
    url = f"https://www.fantrax.com/fxpa/req?t=106"
    payload = {
        "ms": "view", "pageNumber": 1, "maxResults": 1000, "view": "STATS",
        "positionOrGroup": "H", "seasonOrPeriod": "SC_REG", "leagueId": id,
        "statusOrTeam": "ALL_AVAILABLE"
    }
    try:
        res = requests.post(url, json=payload).json()
        player_list = res['responses'][0]['data']['tableList']
        
        parsed = []
        for p in player_list:
            stats = p.get('stats', [])
            points = float(stats[0]) if len(stats) > 0 else 0.0
            ab = int(stats[1]) if len(stats) > 1 else 0
            
            # Simple check for IL/Minors strings or short-names
            status = p.get('statusShortNames', 'FA')
            is_inactive = False
            if 'IL' in p.get('injuryStatus', '') or status in ['MINORS', 'IL']:
                is_inactive = True
                
            parsed.append({
                "Player": p.get('name'),
                "Team": p.get('teamShortName', 'N/A'),
                "Status": status,
                "Points": points,
                "AB": ab,
                "Is_Inactive": is_inactive
            })
        return pd.DataFrame(parsed)
    except:
        st.error("Could not fetch data for this League ID. Check the ID or try again.")
        return pd.DataFrame()

if league_id:
    raw_df = load_league_data(league_id)
    
    if not raw_df.empty:
        # --- THE EXACT COOPER EQUATION ENGINE ---
        # Note: In a production environment with rolling history, 
        # 'Trend' would fetch from a history file. For this live display, 
        # we calculate current baseline values.
        raw_df['Points_Per_AB'] = np.where(raw_df['AB'] > 0, raw_df['Points'] / raw_df['AB'], 0.0)
        
        # Hardcoded trend placeholder to display layout until your history file syncs
        raw_df['Trend'] = 0.0 
        
        # Exact Column F Conditions:
        # IF(H2="IL/MINORS",-100, if(E2<=50, I2*(E2/50), if(E2>50, I2+G2)))
        ppv_low = raw_df['Points_Per_AB'] * (raw_df['AB'] / 50)
        ppv_high = raw_df['Points_Per_AB'] + raw_df['Trend']
        
        raw_df['PPV'] = np.where(
            raw_df['Is_Inactive'] == True, -100.0,
            np.where(raw_df['AB'] <= 50, ppv_low, ppv_high)
        )
        
        # Rank sorting
        raw_df = raw_df.sort_values(by='PPV', ascending=False).reset_index(drop=True)
        raw_df['Rank'] = raw_df.index + 1
        
        # Clean columns to show user
        final_df = raw_df[['Rank', 'Player', 'Team', 'Status', 'Points', 'AB', 'PPV']]
        
        # --- APP INTERFACE NAVIGATION ---
        tab1, tab2, tab3 = st.tabs(["📋 My Team", "🌎 All Players Leaderboard", "🔥 Waiver Wire / Unrostered"])
        
        # Dynamically figure out what rosters exist in this league to populate a dropdown
        teams_list = sorted([t for t in final_df['Status'].unique() if t not in ['FA', 'WAV']])
        
        with tab1:
            my_team = st.selectbox("Select Your Team:", options=teams_list)
            if my_team:
                team_df = final_df[final_df['Status'] == my_team].copy()
                team_df['Team Rank'] = range(1, len(team_df) + 1)
                st.dataframe(team_df[['Team Rank', 'Player', 'Points', 'AB', 'PPV']], use_container_width=True)
                
        with tab2:
            search_query = st.text_input("Search Player Name:")
            display_df = final_df.copy()
            if search_query:
                display_df = display_df[display_df['Player'].str.contains(search_query, case=False)]
            st.dataframe(display_df, use_container_width=True)
            
        with tab3:
            st.subheader("Available Free Agents Ranked by True Production Value")
            waiver_df = final_df[final_df['Status'].isin(['FA', 'WAV'])].reset_index(drop=True)
            waiver_df['Waiver Rank'] = waiver_df.index + 1
            st.dataframe(waiver_df[['Waiver Rank', 'Player', 'Team', 'Points', 'AB', 'PPV']], use_container_width=True)
