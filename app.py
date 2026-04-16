import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker", layout="centered")

# Custom UI Tweaks
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚾ Lineup Locker: PPV Engine")

# 1. DATA FETCH
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=60)
def get_data():
    try:
        r = requests.get(API_URL)
        return pd.DataFrame(r.json())
    except:
        return pd.DataFrame()

df = get_data()

if not df.empty:
    # 2. MATCH COLUMNS (Using the names you just sent me)
    # We'll look for 'Rank', but if it's missing, we'll use 'Player Name' and 'PPV'
    name_col = 'Player Name' if 'Player Name' in df.columns else df.columns[0]
    ppv_col = 'PPV' if 'PPV' in df.columns else None
    
    if ppv_col:
        df[ppv_col] = pd.to_numeric(df[ppv_col], errors='coerce')
        # Only show active players
        active_df = df[df[ppv_col] > -1].copy()

        # 3. RANK LOGIC
        # If your 'Rank' column is still missing from the API, we create it here
        if 'Rank' not in active_df.columns:
            active_df = active_df.sort_values(by=ppv_col, ascending=False)
            active_df['Rank'] = range(1, len(active_df) + 1)
        
        # 4. THE CLEAN VIEW
        st.subheader("Efficiency Leaderboard")
        
        # Define exactly what the user sees
        output_df = active_df[['Rank', name_col, ppv_col]].sort_values(by='Rank')
        
        st.dataframe(
            output_df,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
                name_col: "Player",
                ppv_col: st.column_config.NumberColumn("PPV Score", format="%.3f")
            },
            use_container_width=True,
            hide_index=True
        )

        # 5. SYNC AREA (Future Roster Logic)
        st.divider()
        with st.expander("🏆 Fantrax Roster Sync"):
            st.write("Upload your Fantrax CSV to filter for your team.")
            uploaded_file = st.file_uploader("Choose CSV", type="csv")
            if uploaded_file:
                st.success("Roster received! Matching names now...")
                # We'll put the "Last Name, First Name" logic here next
                
    else:
        st.error("Still can't find the PPV column. Double-check the Sheet headers.")
else:
    st.info("Spinning up the engine... check back in 10 seconds.")
