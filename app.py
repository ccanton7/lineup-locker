import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# --- 1. THE SIDEBAR (League ID & Scoring) ---
with st.sidebar:
    st.header("🏆 Fantrax Sync")
    # We ask ONLY for the League ID, Harry-style.
    league_id = st.text_input("Enter Fantrax League ID", placeholder="e.g. f34zxn9qml5d9oh7")
    if st.button("Sync My Roster"):
        if league_id:
            st.info(f"Syncing with Fantrax League {league_id}...")
            # LOGIC: This is where we will fetch the roster data
        else:
            st.warning("Please enter a League ID first.")

    st.divider()
    
    st.header("⚙️ Scoring Settings")
    st.write("Defaulted to your league settings:")
    # These match your screenshot exactly
    c1, c2 = st.columns(2)
    with c1:
        r_wt = st.number_input("R", value=1.0)
        b1_wt = st.number_input("1B", value=1.0)
        b2_wt = st.number_input("2B", value=2.0)
        b3_wt = st.number_input("3B", value=3.0)
        hr_wt = st.number_input("HR", value=4.0)
    with c2:
        rbi_wt = st.number_input("RBI", value=1.0)
        bb_wt = st.number_input("BB", value=1.0)
        so_wt = st.number_input("SO", value=-0.5)
        sb_wt = st.number_input("SB", value=2.0)
        cs_wt = st.number_input("CS", value=-1.0)

# --- 2. THE STAT WAREHOUSE (Google Sheets) ---
# NOTE: Make sure your Sheet headers match these names exactly!
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=60)
def get_stats():
    try:
        r = requests.get(API_URL)
        return pd.DataFrame(r.json())
    except:
        return pd.DataFrame()

df = get_stats()

# --- 3. THE LOGIC ENGINE ---
if not df.empty:
    # 1. Ensure all columns are numeric
    stat_cols = ['R', '1B', '2B', '3B', 'HR', 'RBI', 'BB', 'SO', 'SB', 'CS']
    for col in stat_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 2. The Calculation (The 'Engine' part)
    if all(col in df.columns for col in stat_cols):
        df['Total_Pts'] = (
            (df['R'] * r_wt) + (df['1B'] * b1_wt) + (df['2B'] * b2_wt) + 
            (df['3B'] * b3_wt) + (df['HR'] * hr_wt) + (df['RBI'] * rbi_wt) + 
            (df['BB'] * bb_wt) + (df['SO'] * so_wt) + (df['SB'] * sb_wt) + 
            (df['CS'] * cs_wt)
        )
        
        # 3. Calculate Live PPV 
        # (Total Points divided by whatever base metric you want, e.g., 'Points' or 'At-Bats')
        denom = 'Points' if 'Points' in df.columns else df.columns[0]
        df['Live_PPV'] = df['Total_Pts'] / pd.to_numeric(df[denom], errors='coerce')

        # 4. Display & Ranking
        display_df = df[df['Live_PPV'] > -1].copy()
        display_df = display_df.sort_values(by='Live_PPV', ascending=False)
        display_df['Rank'] = range(1, len(display_df) + 1)

        st.subheader("Global PPV Efficiency Rankings")
        st.dataframe(
            display_df[['Rank', 'Player Name', 'Live_PPV']],
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
                "Live_PPV": st.column_config.NumberColumn("PPV", format="%.3f")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        # If headers don't match, we tell you which ones are missing
        missing = [c for c in stat_cols if c not in df.columns]
        st.warning(f"Stat Warehouse check: Please add these columns to your Google Sheet: {missing}")

else:
    st.info("Waiting for the Stat Warehouse to connect...")
