import streamlit as st
import pandas as pd
import requests

# Set page title
st.set_page_config(page_title="Lineup Locker | PPV Engine", layout="wide")
st.title("⚾ Lineup Locker: PPV Engine")

# Your "Golden Ticket" URL from Google Sheets
API_URL = "https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec"

# 1. Fetch the data
@st.cache_data(ttl=600) # Refreshes every 10 minutes
def get_data():
    response = requests.get(API_URL)
    return pd.DataFrame(response.json())

df = get_data()

# 2. Clean up the data
# Convert columns to numbers so we can sort them
df['PPV'] = pd.to_numeric(df['PPV'], errors='coerce')
df['Points'] = pd.to_numeric(df['Points'], errors='coerce')
df['ABs'] = pd.to_numeric(df['ABs'], errors='coerce')

# Filter out the "Inactive" floor (-100)
df_active = df[df['PPV'] != -100].copy()

# 3. The Dashboard UI
st.write("### Live Player Rankings")

# Show a searchable, sortable table
st.dataframe(
    df_active.sort_values(by="PPV", ascending=False),
    column_config={
        "PPV": st.column_config.NumberColumn("PPV", format="%.3f"),
        "Trend": st.column_config.NumberColumn("Trend", format="%.3f"),
    },
    use_container_width=True,
    hide_index=True
)
