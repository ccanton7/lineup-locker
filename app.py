import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Setup the Page
st.set_page_config(page_title="Lineup Locker", layout="wide")
st.title("⚾ Lineup Locker")
st.subheader("Live Player Production Value (PPV)")

# PASTE YOUR GOOGLE SHEET URL HERE:
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FWA7GxR6k2-5kci6TenmlFk3yJmjtP-Psy4OyQWTbYU/edit?usp=sharing"

# 2. Secure Connection Protocol
@st.cache_data(ttl=600) # Caches data for 10 mins
def load_secure_data():
    try:
        # Define the API scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Authenticate using your local bot key
        import json
creds_dict = json.loads(st.secrets["gcp_service_account_json"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the sheet and grab the first tab
        sheet = client.open_by_url(SHEET_URL).sheet1
        
        # Convert the Google Sheet data directly into a Pandas DataFrame
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
    except Exception as e:
        st.error(f"Failed to connect to the vault: {e}")
        return pd.DataFrame()

# 3. Load and Display Data
with st.spinner("Connecting to the Lineup Locker Vault..."):
    df = load_secure_data()

if not df.empty:
    # Sidebar Search
    st.sidebar.header("Locker Search")
    search = st.sidebar.text_input("Find Player")

    # Filter logic (Uses the first column, which should be the Player Name)
    name_col = df.columns[0] 
    
    if search:
        df = df[df[name_col].astype(str).str.contains(search, case=False, na=False)]

    # Display the Dashboard
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.dataframe(df, use_container_width=True, height=600)
        
    with col2:
        st.metric("Total Tracked", len(df))
        
        # If your PPV column is named 'PPV', it highlights the top scorer!
        if 'PPV' in df.columns:
            top_player = df.sort_values(by='PPV', ascending=False).iloc[0]
            st.success(f"📈 Top Value: {top_player[name_col]}")
else:
    st.warning("No data found. Ensure the bot email is shared on your Google Sheet!")
