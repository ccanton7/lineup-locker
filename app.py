import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker | PPV Engine", layout="wide")

st.title("⚾ Lineup Locker: PPV Engine")
st.caption("Simplified Efficiency Rankings")

# 1. THE SIDEBAR (Fantrax Sync)
with st.sidebar:
    st.header("🏆 Fantrax Sync")
    st.write("Export your roster from Fantrax (CSV) and drop it here.")
    uploaded_file = st.file_uploader("Upload Roster", type=["csv"])

# 2. DATA FETCH (Google Sheets API)
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=300)
def get_engine_data():
    try:
        r = requests.get(API_URL)
        return pd.DataFrame(r.json())
    except:
        return pd.DataFrame()

engine_df = get_engine_data()

if not engine_df.empty:
    # --- SMART COLUMN DETECTION ---
    # Finds your new 'Rank' column
    rank_col = next((c for c in engine_df.columns if 'rank' in c.lower()), None)
    name_col = next((c for c in engine_df.columns if c.lower() in ['player', 'name']), engine_df.columns[0])
    ppv_col = next((c for c in engine_df.columns if 'ppv' in c.lower()), None)

    if ppv_col and rank_col:
        engine_df[ppv_col] = pd.to_numeric(engine_df[ppv_col], errors='coerce')
        
        # Filter out the -100 noise
        display_df = engine_df[engine_df[ppv_col] > -1].copy()

        # 3. ROSTER MATCHING (If user uploads Fantrax CSV)
        if uploaded_file:
            user_roster = pd.read_csv(uploaded_file)
            fan_name_col = next((c for c in user_roster.columns if 'player' in c.lower() or 'name' in c.lower()), user_roster.columns[0])
            
            # Merge to show only THEIR team's ranks
            merged = pd.merge(user_roster, display_df, left_on=fan_name_col, right_on=name_col, how="inner")
            
            st.subheader("✅ Your Team's Efficiency")
            # Only show the 3 columns they care about
            st.dataframe(
                merged[[rank_col, name_col, ppv_col]].sort_values(by=rank_col),
                use_container_width=True, 
                hide_index=True
            )
        
        else:
            # 4. THE GLOBAL VIEW (Clean Table)
            st.subheader("Global Leaderboard")
            
            # Slim it down to just the big 3
            final_view = display_df[[rank_col, name_col, ppv_col]].sort_values(by=rank_col)
            
            st.dataframe(
                final_view,
                column_config={
                    rank_col: st.column_config.NumberColumn("Rank", format="%d"),
                    name_col: "Player",
                    ppv_col: st.column_config.NumberColumn("PPV", format="%.3f")
                },
                use_container_width=True,
                hide_index=True
            )
    else:
        st.error(f"Missing columns. I need Rank and PPV. Found: {list(engine_df.columns)}")
else:
    st.warning("Connecting to Google Sheets...")
