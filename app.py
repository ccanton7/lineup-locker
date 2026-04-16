import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker | PPV Engine", layout="wide")

# --- CUSTOM CSS FOR THE 'NON-MISERABLE' LOOK ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚾ Lineup Locker: PPV Engine")

# 1. THE SIDEBAR (Fantrax Sync)
with st.sidebar:
    st.header("🏆 Fantrax Sync")
    st.write("Export your roster from Fantrax (CSV) and drop it here.")
    uploaded_file = st.file_uploader("Upload Roster", type=["csv"])

# 2. DATA FETCH
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
    # Finds the name column (Player, Name, or First Col)
    name_col = next((c for c in engine_df.columns if c.lower() in ['player', 'name']), engine_df.columns[0])
    # Finds the PPV column (PPV, or anything containing PPV)
    ppv_col = next((c for c in engine_df.columns if 'ppv' in c.lower()), None)

    if ppv_col:
        engine_df[ppv_col] = pd.to_numeric(engine_df[ppv_col], errors='coerce')
        
        # 3. ROSTER MATCHING LOGIC
        if uploaded_file:
            user_roster = pd.read_csv(uploaded_file)
            # Find the name column in the Fantrax CSV (usually 'Player')
            fan_name_col = next((c for c in user_roster.columns if 'player' in c.lower() or 'name' in c.lower()), user_roster.columns[0])
            
            # Merge the two
            merged = pd.merge(user_roster, engine_df, left_on=fan_name_col, right_on=name_col, how="inner")
            
            st.subheader("✅ Your Team's Ranks")
            st.dataframe(merged[[name_col, ppv_col]].sort_values(by=ppv_col, ascending=False), use_container_width=True, hide_index=True)
            
            avg_ppv = merged[ppv_col].mean()
            st.metric("Team Average PPV", f"{avg_ppv:.3f}")
        
        else:
            # 4. GLOBAL LEADERBOARD (The Clean View)
            st.subheader("Global Efficiency Leaderboard")
            # Only show top players, clean up the view
            clean_display = engine_df[engine_df[ppv_col] > -1][[name_col, ppv_col]].sort_values(by=ppv_col, ascending=False)
            
            st.dataframe(
                clean_display,
                column_config={
                    name_col: "Player",
                    ppv_col: st.column_config.NumberColumn("PPV", format="%.3f")
                },
                use_container_width=True,
                hide_index=True
            )
    else:
        st.error(f"Couldn't find a 'PPV' column. I see these: {list(engine_df.columns)}")
else:
    st.warning("Waiting for data from the Google Sheet...")
