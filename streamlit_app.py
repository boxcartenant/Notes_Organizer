import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from urllib.parse import urlencode
from manage_google_files import *

# Streamlit app interface
#st.title("Google Drive Viewer")

#if authenticate_user():
#    browse_google_drive()


import streamlit as st

# Sidebar navigation pane
with st.sidebar:
    st.title("Navigation Pane")
    if st.button("Toggle Left Pane"):
        st.session_state["show_left_pane"] = not st.session_state.get("show_left_pane", True)
    
    st.markdown("---")
    st.write("This is the navigation area.")
    # Add your navigation buttons or folder hierarchy here

# Main and right panes
col1, col2, col3 = st.columns([1, 2, 1])  # Adjust widths as needed

# Left Pane
if st.session_state.get("show_left_pane", True):
    with col1:
        st.header("Left Pane")
        st.button("Action 1")
        st.button("Action 2")
else:
    col1.empty()

# Middle Pane
with col2:
    st.header("Main Content")
    st.write("This is where file contents and primary interactions will appear.")

# Right Pane
with col3:
    st.header("Special Controls")
    st.write("Add specialized actions here.")
