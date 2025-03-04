import streamlit as st
from . import book_organizer
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from urllib.parse import urlencode
from Google_Drive_Management.manage_google_files import *

#Layout testing

def main():
    # Set up session state for mode selection
    if 'mode' not in st.session_state:
        st.session_state.mode = 1

    logged_in = False

    # Sidebar: Mode buttons
    with st.sidebar:
        logged_in = authenticate_user()



    #Everything else
    if logged_in:
        match st.session_state.mode:
            case 1: #book Organizer
                book_organizer.sidebar()
                book_organizer.body()

    else:
        st.write("This app fetches text files from google drive, and lets you organize their contents.")
        st.write("It creates a project folder in which to organize notes.")
        st.write("Log into google drive using the link on the sidebar (left) to begin.")
            
if __name__ == "__main__":
    main()
