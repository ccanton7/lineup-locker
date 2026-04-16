import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# --- 1. THE SIDEBAR (All 14 Categories) ---
with st.sidebar:
    st.header("🏆 Fantrax Sync")
    league_id = st.text_input("League ID", placeholder="Enter ID...")
    if st.button("Sync My Roster"):
        st.info("Sync logic primed. Waiting for raw stats...")

    st.divider()
    
    st.header("⚙️ Scoring Settings")
    # All 14 Categories from your screenshot
    col1, col2 = st.columns(2)
    with col1:
        r_wt = st.number_input("R", value=1.0)
        b1_wt = st.number_input("1B", value=1.0)
        b2_wt = st.number_input("2B", value=2.0)
        b3_wt = st.number_input("3B", value=3.0)
        hr_wt = st.number_input("HR", value=4.0)
        rbi_wt = st.number_input("RBI", value=1.0)
        bb_wt = st.number_input("BB", value=1.0)
    with col2:
        hbp_wt = st.number_input("HBP", value=1.0)
        sb_wt = st.number_input("SB", value=2.0)
        cs_wt = st.number_input("CS", value=-1.0)
        so_wt = st.number_input("SO", value=-0.5)
        gidp_wt = st.number_input("GIDP", value=-1.0)
        cyc_wt = st.number_input("CYC", value=5.0)
        gs_wt = st.number_input("GS", value=4.0)

# --- 2. DATA FETCH ---
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=60)
def get_stats():
    try:
        r = requests.get(API_URL)
        return pd.DataFrame(r.json())
    except:
        return pd.DataFrame()

df = get_stats()

# --- 3. THE 14-STAT MATH ---
if not df.empty:
    stat_cols = ['R', '1B', '2B', '3B', 'HR', 'RBI', 'BB', 'HBP', 'SB', 'CS', 'SO', 'GIDP', 'CYC', 'GS']
    
    # Check if all 14 exist in the sheet
    if all(col in df.columns for col in stat_cols):
        for col in stat_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # The Master Formula
        df['Custom_Total'] = (
            (df['R'] * r_wt) + (df['1B'] * b1_wt) + (df['2B'] * b2_wt) + 
            (df['3B'] * b3_wt) + (df['HR'] * hr_wt) + (df['RBI'] * rbi_wt) + 
            (df['BB'] * bb_wt) + (df['HBP'] * hbp_wt) + (df['SB'] * sb_wt) + 
            (df['CS'] * cs_wt) + (df['SO'] * so_wt) + (df['GIDP'] * gidp_wt) + 
            (df['CYC'] * cyc_wt) + (df['GS'] * gs_wt)
        )
        
        # PPV Calculation (Custom Total / Denominator)
        # Using 'Points' as the denominator to measure efficiency against current value
        denom = 'Points' if 'Points' in df.columns else df.columns[0]
        df['Live_PPV'] = df['Custom_Total'] / pd.to_numeric(df[denom], errors='coerce')
        
        # Sort and Rank
        display_df = df[df['Live_PPV'] > -1].copy()
        display_df = display_df.sort_values(by='Live_PPV', ascending=False)
        display_df['Rank'] = range(1, len(display_df) + 1)

        st.subheader("Global Leaderboard")
        st.dataframe(
            display_df[['Rank', 'Player Name', 'Live_PPV']],
            use_container_width=True, hide_index=True
        )
    else:
        missing = [c for c in stat_cols if c not in df.columns]
        st.warning(f"Stat Warehouse Alert: Please add these 14 columns to your 'App Live' sheet: {missing}")
