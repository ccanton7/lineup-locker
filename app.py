import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# --- 1. SIDEBAR: USER INPUTS ---
with st.sidebar:
    st.header("🔗 Fantrax Sync")
    # You enter your ID here. I've left it blank/generic for you.
    league_id = st.text_input("Enter League ID", placeholder="e.g. p4jlxofwmg5kgkd4")
    show_my_roster = st.checkbox("Show Only My Roster", value=False)
    
    st.divider()
    st.header("⚙️ Scoring Weights")
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

# --- 2. DATA FETCHING ---
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=60)
def get_warehouse_data():
    try:
        r = requests.get(API_URL)
        return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
    except:
        return pd.DataFrame()

# Robust Roster Fetcher
@st.cache_data(ttl=300)
def get_fantrax_roster(l_id):
    if not l_id: return []
    try:
        url = f"https://www.fantrax.com/fxea/general/getTeamRosters?leagueId={l_id}"
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return []
        data = r.json()
        
        roster_names = []
        for team in data.values():
            for player in team.get('roster', []):
                # Fantrax uses "Last, First". We flip it to "First Last"
                raw_name = player.get('name', '')
                if ',' in raw_name:
                    last, first = raw_name.split(',', 1)
                    roster_names.append(f"{first.strip()} {last.strip()}".upper())
                else:
                    roster_names.append(raw_name.strip().upper())
        return roster_names
    except:
        return []

df = get_warehouse_data()
my_roster = get_fantrax_roster(league_id) if show_my_roster else []

# --- 3. THE MATH ENGINE ---
if not df.empty:
    weights = {
        'R': r_wt, '1B': b1_wt, '2B': b2_wt, '3B': b3_wt, 'HR': hr_wt,
        'RBI': rbi_wt, 'BB': bb_wt, 'HBP': hbp_wt, 'SB': sb_wt, 
        'CS': cs_wt, 'SO': so_wt, 'GIDP': gidp_wt, 'CYC': cyc_wt, 'SF': sf_wt
    }
    
    if all(col in df.columns for col in weights.keys()):
        for col in weights.keys():
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate Points & PPV
        df['POINTS'] = sum(df[col] * wt for col, wt in weights.items())
        
        if 'AT-BATS' in df.columns:
            df['AT-BATS'] = pd.to_numeric(df['AT-BATS'], errors='coerce').replace(0, 1)
            df['PPV'] = df['POINTS'] / df['AT-BATS']
            
            # --- FILTERING ---
            if show_my_roster and my_roster:
                # Compare Uppercase for both to ensure a match
                df = df[df['PLAYER NAME'].str
