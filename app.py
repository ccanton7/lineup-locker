import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker: Live PPV Engine")

# --- 1. SIDEBAR: THE SCORING WEIGHTS ---
with st.sidebar:
    st.header("⚙️ Scoring Settings")
    # These values represent "Points per Stat"
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
        sf_wt = st.number_input("SF", value=1.0)

# --- 2. THE DATA PIPELINE ---
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=60)
def fetch_data():
    try:
        data = requests.get(API_URL).json()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

df = fetch_data()

# --- 3. THE CALCULATION ENGINE ---
if not df.empty:
    # Ensure all category columns are numeric
    cats = ['R', '1B', '2B', '3B', 'HR', 'RBI', 'BB', 'HBP', 'SB', 'CS', 'SO', 'GIDP', 'CYC', 'SF']
    for c in cats:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # Calculate Total Points based on user inputs
    df['Calculated_Points'] = (
        (df['R'] * r_wt) + (df['1B'] * b1_wt) + (df['2B'] * b2_wt) + 
        (df['3B'] * b3_wt) + (df['HR'] * hr_wt) + (df['RBI'] * rbi_wt) + 
        (df['BB'] * bb_wt) + (df['HBP'] * hbp_wt) + (df['SB'] * sb_wt) + 
        (df['CS'] * cs_wt) + (df['SO'] * so_wt) + (df['GIDP'] * gidp_wt) + 
        (df['CYC'] * cyc_wt) + (df['SF'] * sf_wt)
    )

    # Calculate PPV (Efficiency)
    # Using 'ABs' (Column D) as the denominator
    df['ABs'] = pd.to_numeric(df['ABs'], errors='coerce').replace(0, 1)
    df['Live_PPV'] = df['Calculated_Points'] / df['ABs']

    # --- 4. DISPLAY THE LEADERBOARD ---
    df = df.sort_values(by='Live_PPV', ascending=False)
    df['Rank'] = range(1, len(df) + 1)

    st.subheader("Global PPV Leaderboard")
    st.dataframe(
        df[['Rank', 'Player Name', 'Calculated_Points', 'Live_PPV']],
        column_config={
            "Calculated_Points": st.column_config.NumberColumn("Points", format="%.1f"),
            "Live_PPV": st.column_config.NumberColumn("PPV", format="%.3f")
        },
        use_container_width=True, hide_index=True
    )
