import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lineup Locker | PPV Engine", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# Your Google Sheets Web App URL
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

@st.cache_data(ttl=60)
def get_data():
    try:
        response = requests.get(API_URL)
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

df = get_data()

if not df.empty:
    # DEBUG: This helps us see what the sheet is actually sending
    # Once the table works, we can remove this line
    # st.write("Columns found in your sheet:", list(df.columns))

    # We try to find the Player and PPV columns even if the names are slightly different
    name_col = next((c for c in df.columns if 'Player' in c or 'Name' in c), df.columns[0])
    ppv_col = next((c for c in df.columns if 'PPV' in c or 'ppv' in c), None)

    if ppv_col:
        # Convert to numbers and filter out the -100 "Inactive" noise
        df[ppv_col] = pd.to_numeric(df[ppv_col], errors='coerce')
        df_active = df[df[ppv_col] != -100].copy()

        st.write(f"### Live Rankings (Based on {ppv_col})")
        
        # Display the table
        st.dataframe(
            df_active.sort_values(by=ppv_col, ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error(f"Could not find a column named 'PPV' in your sheet. I see these instead: {list(df.columns)}")
else:
    st.warning("No data found. Check if your Google Sheet 'PPV_Engine' tab has data in it.")
