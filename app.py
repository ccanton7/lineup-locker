# 2. Secure Connection Protocol
@st.cache_data(ttl=600) # Caches data for 10 mins
def load_secure_data():
    try:
        # Define the API scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Authenticate using the Streamlit Cloud Vault
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
