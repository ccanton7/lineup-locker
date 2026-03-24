import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. Setup the Page
st.set_page_config(page_title="Lineup Locker V2", layout="wide")
st.title("⚾ Lineup Locker")

# 2. THE DIRECT URL (Copy/Paste your browser address bar here)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1a7EzWVcudzFnbvTYnWk9nBgJNv5OKU8-ug3TgrFJqjE/edit?gid=0#gid=0"

# 3. Secure Connection Protocol
@st.cache_data(ttl=600)
def load_secure_data():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(st.secrets["gcp_service_account_json"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the specific 'App_Live' tab
        # IMPORTANT: This must match the tab name exactly!
        spreadsheet = client.open_by_url(SHEET_URL)
        sheet = spreadsheet.worksheet("App_Live")
        
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        # This will tell us EXACTLY what failed
        st.error(f"Error Details: {e}")
        return pd.DataFrame()

# 4. Load Data
with st.spinner("Accessing the Vault..."):
    master_df = load_secure_data()

# 5. Dashboard Logic
if not master_df.empty:
    st.sidebar.header("🔄 Sync Your League")
    uploaded_file = st.sidebar.file_uploader("Drop Fantrax Roster CSV here", type="csv")
    
    # Global Search
    search = st.text_input("Search Player Pool", "")
    
    # Process Data
    if 'PLAYER' in master_df.columns:
        if search:
            master_df = master_df[master_df['PLAYER'].astype(str).str.contains(search, case=False, na=False)]
            
    st.dataframe(master_df, use_container_width=True, hide_index=True)
else:
    st.warning("Database empty. Ensure 'App_Live' tab has headers (PLAYER, TEAM, etc.) and at least one row of data!")
