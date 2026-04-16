import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker | Fantrax Sync", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# 1. SIDEBAR: The Fantrax Sync Portal
with st.sidebar:
    st.header("🏆 Fantrax Sync")
    st.write("Export your roster from Fantrax as a CSV and drop it here.")
    uploaded_file = st.file_uploader("Upload Fantrax Roster", type=["csv"])

# 2. DATA LOAD: Your Google Sheet Engine
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=300)
def get_engine_data():
    r = requests.get(API_URL)
    return pd.DataFrame(r.json())

engine_df = get_engine_data()
engine_df['PPV'] = pd.to_numeric(engine_df['PPV'], errors='coerce')

# 3. MAIN LOGIC: Roster Comparison
if uploaded_file is not None:
    user_roster = pd.read_csv(uploaded_file)
    
    # Clean up names to make sure they match (e.g., "A. Judge" vs "Aaron Judge")
    # This is where the 'Logic Vibe' happens
    st.subheader("✅ Your Team's Efficiency")
    
    # We merge your PPV engine with their uploaded roster
    # Assuming Fantrax CSV has a 'Player' column
    team_data = pd.merge(user_roster, engine_df, on="Player", how="inner")
    
    # Show their specific team stats
    st.dataframe(
        team_data[['Player', 'PPV', 'Points', 'ABs']].sort_values(by="PPV", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    
    # Give them a "Team Grade"
    avg_ppv = team_data['PPV'].mean()
    st.metric("Average Team PPV", f"{avg_ppv:.3f}")

else:
    st.info("Top League Rankings (Upload a Fantrax CSV in the sidebar to filter for your team)")
    st.dataframe(
        engine_df[engine_df['PPV'] > -1][['Player', 'PPV']].sort_values(by="PPV", ascending=False),
        use_container_width=True,
        hide_index=True
    )
