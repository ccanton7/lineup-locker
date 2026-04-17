import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# --- 1. SIDEBAR: SCORING SETTINGS ---
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

# --- 3. THE MATH ENGINE ---
if not df.empty:
    # Categories to multiply by weights
    weights = {
        'R': r_wt, '1B': b1_wt, '2B': b2_wt, '3B': b3_wt, 'HR': hr_wt,
        'RBI': rbi_wt, 'BB': bb_wt, 'HBP': hbp_wt, 'SB': sb_wt, 
        'CS': cs_wt, 'SO': so_wt, 'GIDP': gidp_wt, 'CYC': cyc_wt, 'SF': sf_wt
    }
    
    if all(col in df.columns for col in weights.keys()):
        # Convert stats to numbers
        for col in weights.keys():
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate Points based on your specific weights
        df['POINTS'] = 0.0
        for col, wt in weights.items():
            df['POINTS'] += (df[col] * wt)
        
        # Calculate PPV using AT-BATS denominator
        if 'AT-BATS' in df.columns:
            df['AT-BATS'] = pd.to_numeric(df['AT-BATS'], errors='coerce').replace(0, 1)
            df['PPV'] = df['POINTS'] / df['AT-BATS']
            
            # Sort by Efficiency and Rank them
            df = df.sort_values(by='PPV', ascending=False)
            df['RANK'] = range(1, len(df) + 1)

            # --- 4. DISPLAY LEADERBOARD ---
            st.subheader("Leaderboard: Efficiency by Custom Scoring")
            
            # Match your App Live header names exactly
            show_cols = ['RANK', 'PLAYER NAME', 'STATUS', 'POINTS', 'PPV']
            
            st.dataframe(
                df[show_cols],
                column_config={
                    "RANK": st.column_config.NumberColumn("Rank", format="#%d"),
                    "POINTS": st.column_config.NumberColumn("Points", format="%.1f"),
                    "PPV": st.column_config.NumberColumn("PPV", format="%.3f")
                },
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("Denominator Missing: 'AT-BATS' column not found in data.")
    else:
        missing = [c for c in weights.keys() if c not in df.columns]
        st.warning(f"Stat Columns Missing: {missing}")
else:
    st.info("Awaiting data from the Stat Warehouse...")
