import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# --- 1. SIDEBAR: SCORING & SYNC ---
with st.sidebar:
    st.header("🔗 League Sync")
    # Hardcoded your specific League ID
    league_id = st.text_input("Fantrax League ID", value="p4jlxofwmg5kgkd4")
    
    # Checkbox to toggle the filter
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
        r = requests.get(API_URL)
        return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
    except:
        return pd.DataFrame()

# NEW: Fantrax Roster Fetcher
@st.cache_data(ttl=300)
def get_fantrax_roster(l_id):
    if not l_id: return []
    try:
        # Fantrax public roster endpoint
        url = f"https://www.fantrax.com/fxea/general/getTeamRosters?leagueId={l_id}"
        r = requests.get(url)
        data = r.json()
        
        # This logic finds your players. 
        # (Note: Fantrax data structures vary, we'll refine this once we see the 'Public' response)
        roster_list = []
        for teamId in data:
            for player in data[teamId]['roster']:
                roster_list.append(player['name'])
        return roster_list
    except:
        return []

df = get_warehouse_data()
my_roster = get_fantrax_roster(league_id)

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
        
        # POINTS calculation
        df['POINTS'] = sum(df[col] * wt for col, wt in weights.items())
        
        # PPV calculation
        if 'AT-BATS' in df.columns:
            df['AT-BATS'] = pd.to_numeric(df['AT-BATS'], errors='coerce').replace(0, 1)
            df['PPV'] = df['POINTS'] / df['AT-BATS']
            
            # --- FILTER LOGIC ---
            if show_my_roster and my_roster:
                # Matches player names from your sheet against the Fantrax list
                df = df[df['PLAYER NAME'].isin(my_roster)]
            
            # Rank and Sort
            df = df.sort_values(by='PPV', ascending=False)
            df['RANK'] = range(1, len(df) + 1)

            # --- 4. DISPLAY ---
            st.subheader(f"Leaderboard: {'My Roster' if show_my_roster else 'All Players'}")
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
            st.warning("Ensure 'AT-BATS' is a header in 'App Live'.")
    else:
        st.warning(f"Missing Columns: {[c for c in weights.keys() if c not in df.columns]}")
else:
    st.info("Warehouse connection pending...")
