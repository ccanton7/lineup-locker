import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. Setup the Page
st.set_page_config(page_title="Lineup Locker V2", layout="wide")
st.title("⚾ Lineup Locker")
st.subheader("Elite Dynasty Analytics | Player Production Value")

# 2. THE DIRECT URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1a7EzWVcudzFnbvTYnWk9nBgJNv5OKU8-ug3TgrFJqjE/edit?gid=0#gid=0"

# 3. Secure Connection Protocol
@st.cache_data(ttl=600)
def load_secure_data():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(st.secrets["gcp_service_account_json"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_url(SHEET_URL)
        sheet = spreadsheet.worksheet("App_Live")
        
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Vault Connection Error: {e}")
        return pd.DataFrame()

# 4. Load Master Data
with st.spinner("Syncing with Lineup Locker Database..."):
    master_df = load_secure_data()

# 5. SIDEBAR: User League Sync
st.sidebar.header("🔄 Sync Your League")
uploaded_file = st.sidebar.file_uploader("Drop Fantrax Roster CSV here", type="csv")

if not master_df.empty:
    # 6. Logic for "Sync My League"
    if uploaded_file is not None:
        user_roster = pd.read_csv(uploaded_file)
        user_col = 'Player' if 'Player' in user_roster.columns else user_roster.columns[0]
        
        # Cross-reference user names with Master PPV
        synced_df = master_df[master_df['PLAYER'].isin(user_roster[user_col])]
        
        st.header("📋 Your Team's Production")
        st.dataframe(synced_df, use_container_width=True, hide_index=True)
        
        if 'PPV' in synced_df.columns:
            avg_ppv = round(synced_df['PPV'].mean(), 2)
            st.metric("Your Team Average PPV", avg_ppv)
        st.divider()

    # 7. Main Dashboard (Global Rankings)
    st.header("🌎 Global Player Rankings")
    search = st.text_input("Search the Player Pool", "")

    # Apply Shohei Tax (0.65x for 2-way players)
    if 'POSITION(S)' in master_df.columns and 'PPV' in master_df.columns:
        two_way_mask = master_df['POSITION(S)'].astype(str).str.contains('P') & \
                       master_df['POSITION(S)'].astype(str).str.contains('UT|OF|1B|2B|3B|SS|C')
        master_df.loc[two_way_mask, 'PPV'] = pd.to_numeric(master_df.loc[two_way_mask, 'PPV'], errors='coerce') * 0.65

    # Re-sort and Generate Fresh Ranks
    if 'PPV' in master_df.columns:
        master_df['PPV'] = pd.to_numeric(master_df['PPV'], errors='coerce')
        master_df = master_df.sort_values(by='PPV', ascending=False).reset_index(drop=True)
        master_df['RANK'] = range(1, len(master_df) + 1)
        
        # Put Rank first
        cols = ['RANK'] + [c for c in master_df.columns if c != 'RANK']
        master_df = master_df[cols]

    # Search Filter
    if search:
        master_df = master_df[master_df['PLAYER'].astype(str).str.contains(search, case=False, na=False)]

    # Display Table
    st.dataframe(master_df, use_container_width=True, height=600, hide_index=True)
    st.success(f"Top Value: {master_df.iloc[0]['PLAYER'] if not master_df.empty else 'N/A'}")

else:
    st.warning("Database empty. Ensure 'App_Live' tab in your V2 sheet has data!")
