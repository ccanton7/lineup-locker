import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# --- 1. SIDEBAR: USER INPUTS ---
with st.sidebar:
    st.header("🔗 Fantrax Sync")
    # Enter your ID here (e.g., p4jlxofwmg5kgkd4)
    league_id = st.text_input("Enter League ID", placeholder="League ID...")
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

# --- 2. DATA PIPELINE ---
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=60)
def get_warehouse_data():
    try:
        r = requests.get(API_URL, timeout=10)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_fantrax_roster(l_id):
    if not l_id:
        return []
    try:
        url = f"https://www.fantrax.com/fxea/general/getTeamRosters?leagueId={l_id}"
        r = requests.get(url, timeout=10)
        data = r.json()
        names = []
        for team in data.values():
            players = team.get('roster', [])
            for p in players:
                n = p.get('name', '')
                if ',' in n:
                    last, first = n.split(',', 1)
                    names.append(f"{first.strip()} {last.strip()}".upper())
                else:
                    names.append(n.strip().upper())
        return names
    except:
        return []

df = get_warehouse_data()

# --- 3. THE LOGIC ENGINE ---
if not df.empty:
    weights = {
        'R': r_wt, '1B': b1_wt, '2B': b2_wt, '3B': b3_wt, 'HR': hr_wt,
        'RBI': rbi_wt, 'BB': bb_wt, 'HBP': hbp_wt, 'SB': sb_wt, 
        'CS': cs_wt, 'SO': so_wt, 'GIDP': gidp_wt, 'CYC': cyc_wt, 'SF': sf_wt
    }
    
    # Check for core columns
    if all(col in df.columns for col in weights.keys()):
        # Convert stats to numbers
        for col in weights.keys():
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate Points
        df['POINTS'] = 0.0
        for col, wt in weights.items():
            df['POINTS'] += (df[col] * wt)
        
        # Calculate PPV
        if 'AT-BATS' in df.columns:
            df['AT-BATS'] = pd.to_numeric(df['AT-BATS'], errors='coerce').replace(0, 1)
            df['PPV'] = df['POINTS'] / df['AT-BATS']
            
            # --- ROSTER FILTERING ---
            if show_my_roster and league_id:
                roster = get_fantrax_roster(league_id)
                if roster:
                    # Filter: Compare UPPERCASE names for a solid match
                    mask = df['PLAYER NAME'].str.upper().isin(roster)
                    df = df[mask]
                else:
                    st.sidebar.error("Could not fetch roster. Is the league Public?")

            # Rank and Sort
            df = df.sort_values(by='PPV', ascending=False)
            df['RANK'] = range(1, len(df) + 1)

            # --- 4. DISPLAY ---
            st.subheader("Leaderboard: Efficiency Dashboard")
            show = ['RANK', 'PLAYER NAME', 'STATUS', 'POINTS', 'PPV']
            st.dataframe(
                df[show],
                column_config={
                    "RANK": st.column_config.NumberColumn("Rank", format="#%d"),
                    "POINTS": st.column_config.NumberColumn("Pts", format="%.1f"),
                    "PPV": st.column_config.NumberColumn("PPV", format="%.3f")
                },
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.error("Missing 'AT-BATS' header in Google Sheet.")
    else:
        st.warning(f"Headers missing in Sheet: {[c for c in weights.keys() if c not in df.columns]}")
else:
    st.info("Stat Warehouse connection pending...")
