import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# --- 1. SIDEBAR: THE SCORING WEIGHTS ---
with st.sidebar:
    st.header("⚙️ Scoring Settings")
    c1, c2 = st.columns(2)
    with c1:
        r_wt = st.number_input("R", value=1.0)
        b1_wt = st.number_input("1B", value=1.0)
        b2_wt = st.number_input("2B", value=2.0)
        b3_wt = st.number_input("3B", value=3.0)
        hr_wt = st.number_input("HR", value=4.0)
        rbi_wt = st.number_input("RBI", value=1.0)
        bb_wt = st.number_input("BB", value=1.0)
    with c2:
        hbp_wt = st.number_input("HBP", value=1.0)
        sb_wt = st.number_input("SB", value=2.0)
        cs_wt = st.number_input("CS", value=-1.0)
        so_wt = st.number_input("SO", value=-0.5)
        gidp_wt = st.number_input("GIDP", value=-1.0)
        cyc_wt = st.number_input("CYC", value=5.0)
        sf_wt = st.number_input("SF", value=1.0)

# --- 2. DATA FETCH ---
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=60)
def get_data():
    try:
        r = requests.get(API_URL)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = get_data()

# --- 3. THE LIVE MATH ---
if not df.empty:
    # Categories needed for calculation
    stat_cols = ['R', '1B', '2B', '3B', 'HR', 'RBI', 'BB', 'HBP', 'SB', 'CS', 'SO', 'GIDP', 'CYC', 'SF']
    
    if all(col in df.columns for col in stat_cols):
        for col in stat_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate Points (Broken into lines so it doesn't clip)
        df['LIVE_POINTS'] = (
            (df['R'] * r_wt) + 
            (df['1B'] * b1_wt) + 
            (df['2B'] * b2_wt) + 
            (df['3B'] * b3_wt) + 
            (df['HR'] * hr_wt) + 
            (df['RBI'] * rbi_wt) + 
            (df['BB'] * bb_wt) + 
            (df['HBP'] * hbp_wt) + 
            (df['SB'] * sb_wt) + 
            (df['CS'] * cs_wt) + 
            (df['SO'] * so_wt) + 
            (df['GIDP'] * gidp_wt) + 
            (df['CYC'] * cyc_wt) + 
            (df['SF'] * sf_wt)
        )
        
        # Calculate PPV using AT-BATS as the denominator
        df['AT-BATS'] = pd.to_numeric(df['AT-BATS'], errors='coerce').replace(0, 1)
        df['LIVE_PPV'] = df['LIVE_POINTS'] / df['AT-BATS']
        
        # 4. RANK AND SORT
        df = df.sort_values(by='LIVE_PPV', ascending=False)
        df['LIVE_RANK'] = range(1, len(df) + 1)

        # 5. DISPLAY
        st.subheader("Leaderboard: Live PPV Efficiency")
        cols_to_show = ['LIVE_RANK', 'PLAYER NAME', 'STATUS', 'LIVE_POINTS', 'LIVE_PPV']
        st.dataframe(
            df[cols_to_show],
            column_config={
                "LIVE_RANK": st.column_config.NumberColumn("Rank", format="#%d"),
                "LIVE_POINTS": st.column_config.NumberColumn("Points", format="%.1f"),
                "LIVE_PPV": st.column_config.NumberColumn("PPV", format="%.3f")
            },
            use_container_width=True, 
            hide_index=True
        )
    else:
