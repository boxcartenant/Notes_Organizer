import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from urllib.parse import urlencode
import book_organizer
from Google_Drive_Management.manage_google_files import *


def main():
    logged_in = False

    # Sidebar: Mode buttons
    with st.sidebar:
        logged_in = authenticate_user()

    #Everything else
    if logged_in:
            creds = Credentials.from_authorized_user_info(st.session_state["credentials"])
            service = build('drive', 'v3', credentials=creds)
            browse_google_drive(service) # a call to manage_google_files.py
            book_organizer.body(service) # a call to book_organizer.py
    else:
        st.write("This project is a tool for organizing notes into chapters...like if you're writing a book.")
        st.write("It creates a folder on your google drive for your project. To get started:")
        st.write("- Log into your google drive account using the button on the expander (left).")
        
            
if __name__ == "__main__":
    main()
