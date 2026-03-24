import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. Setup the Page
st.set_page_config(page_title="Lineup Locker V2", layout="wide")
st.title("⚾ Lineup Locker")
st.subheader("Elite Dynasty Analytics")

# 2. Your NEW Website V2 Google Sheet Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FWA7GxR6k2-5kci6TenmlFk3yJmjtP-Psy4OyQWTbYU/edit?usp=sharing"

# 3. Secure Connection Protocol
@st.cache_data(ttl=600)
def load_secure_data():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(st.secrets["gcp_service_account_json"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the SPECIFIC 'App_Live' tab in your V2 Sheet
        sheet = client.open_by_url(SHEET_URL).worksheet("App_Live")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Cloud Vault Connection Error: {e}")
        return pd.DataFrame()

# 4. Load Global Rankings
with st.spinner("Accessing the Vault..."):
    master_df = load_secure_data()

# 5. SIDEBAR: User League Sync
st.sidebar.header("🔄 Sync Your League")
uploaded_file = st.sidebar.file_uploader("Drop Fantrax Roster CSV here", type="csv")

if not master_df.empty:
    # 6. Logic for "Sync My League"
    if uploaded_file is not None:
        user_roster = pd.read_csv(uploaded_file)
        # Try to find the player column in user's uploaded file
        user_col = 'Player' if 'Player' in user_roster.columns else user_roster.columns[0]
        
        # Cross-reference user names with our Master PPV list
        synced_df = master_df[master_df['PLAYER'].isin(user_roster[user_col])]
        
        st.header("📋 Your Team's Production")
        st.dataframe(synced_df, use_container_width=True, hide_index=True)
        st.write(f"**Average Team PPV:** {round(synced_df['PPV'].mean(), 2) if 'PPV' in synced_df.columns else 'N/A'}")
        st.divider()

    # 7. Main Dashboard (Global Rankings)
    st.header("🌎 Global Rankings")
    search = st.text_input("Search the Player Pool", "")

    # Apply Shohei Tax & Sorting
    if 'POSITION(S)' in master_df.columns and 'PPV' in master_df.columns:
        two_way = master_df['POSITION(S)'].astype(str).str.contains('P') & master_df['POSITION(S)'].astype(str).str.contains('UT|OF|1B|2B|3B|SS|C')
        master_df.loc[two_way, 'PPV'] = master_df.loc[two_way, 'PPV'] * 0.65

    if 'PPV' in master_df.columns:
        master_df = master_df.sort_values(by='PPV', ascending=False).reset_index(drop=True)
        master_df['RANK'] = range(1, len(master_df) + 1)

    # Filter by Search
    if search:
        master_df = master_df[master_df['PLAYER'].astype(str).str.contains(search, case=False, na=False)]

    st.dataframe(master_df, use_container_width=True, height=600, hide_index=True)

else:
    st.warning("V2 Database not found. Check your 'App_Live' tab in Google Sheets!")
