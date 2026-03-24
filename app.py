import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. Setup the Page
st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker")
st.subheader("Live Player Production Value (PPV)")

# 2. Your Google Sheet Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FWA7GxR6k2-5kci6TenmlFk3yJmjtP-Psy4OyQWTbYU/edit?usp=sharing"

# 3. Secure Connection Protocol
@st.cache_data(ttl=600) # Caches data for 10 mins
def load_secure_data():
    try:
        # Define the API scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Authenticate using the Streamlit Cloud Vault
        creds_dict = json.loads(st.secrets["gcp_service_account_json"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the sheet and grab the SPECIFIC tab we made for the app
        sheet = client.open_by_url(SHEET_URL).worksheet("app_display")
        
        # Convert the Google Sheet data directly into a Pandas DataFrame
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
    except Exception as e:
        st.error(f"Failed to connect to the vault: {e}")
        return pd.DataFrame()

# 4. Load and Display Data
with st.spinner("Connecting to the Lineup Locker Vault..."):
    df = load_secure_data()

if not df.empty:
    # Sidebar Search
    st.sidebar.header("Locker Search")
    search = st.sidebar.text_input("Find Player")

    # Filter logic (Uses 'Player' column if it exists, otherwise defaults to the first column)
    name_col = 'PLAYER' if 'PLAYER' in df.columns else df.columns[0] 
    
    if search:
        df = df[df[name_col].astype(str).str.contains(search, case=False, na=False)]

    # --- THE UI GLOW UP ---
    # 1. The "Shohei Tax" (Fixing Two-Way Players)
    if 'POSITION(S)' in df.columns and 'PPV' in df.columns:
        two_way_mask = df['POSITION(S)'].astype(str).str.contains('P') & df['POSITION(S)'].astype(str).str.contains('UT|OF|1B|2B|3B|SS|C')
        df.loc[two_way_mask, 'PPV'] = df.loc[two_way_mask, 'PPV'] * 0.65

    # 2. Sort by True PPV and Reset the Index
    if 'PPV' in df.columns:
        df = df.sort_values(by='PPV', ascending=False).reset_index(drop=True)
        
    # 3. Generate a fresh, perfectly ordered Rank column
    if 'RANK' in df.columns:
        df['RANK'] = range(1, len(df) + 1)

    # Display the Dashboard
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.dataframe(
            df, 
            use_container_width=True, 
            height=600,
            hide_index=True 
        )
        
    with col2:
        st.metric("Total Tracked", len(df))
        
        if 'PPV' in df.columns and 'PLAYER' in df.columns:
            top_player_name = df.iloc[0]['PLAYER']
            st.success(f"📈 Top Value: {top_player_name}")
else:
    st.warning("No data found. Ensure the bot email is shared on your Google Sheet!")
