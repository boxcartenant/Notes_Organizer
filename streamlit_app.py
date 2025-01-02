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

# Session state to manage visibility of panes
if "show_left_pane" not in st.session_state:
    st.session_state["show_left_pane"] = True
if "show_right_pane" not in st.session_state:
    st.session_state["show_right_pane"] = True

# Left Sidebar (Navigation)
with st.sidebar:
    st.title("Left Pane")
    if authenticate_user():
        browse_google_drive()
    if st.button("Toggle Left Pane"):
        st.session_state["show_left_pane"] = not st.session_state["show_left_pane"]

# Layout with three columns
col1, col2, col3 = st.columns([1, 3, 1])

# Left Pane
if st.session_state["show_left_pane"]:
    with col1:
        st.header("Left Pane")
        st.button("Nav Button 1", type="primary")
        st.button("Nav Button 2", type="secondary")
        st.button("Nav Button 3", type="tertiary")
else:
    col1.empty()

# Main Content Pane
with col2:
    st.header("Main Content")
    st.write("This is the main content area.")

# Right Pane
if st.session_state["show_right_pane"]:
    with col3:
        st.header("Right Pane")
        st.button("Option 1")
        st.button("Option 2")
else:
    col3.empty()

# Footer toggle button for right pane
if st.button("Toggle Right Pane", key="toggle_right_pane"):
    st.session_state["show_right_pane"] = not st.session_state["show_right_pane"]
