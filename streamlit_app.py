import streamlit as st
from O1_Book_Organizer import book_organizer
import O2_Bibledb_to_Book.bibledb_to_book as bibledb_to_book
import O3_Bibledb_Editor.bibledb_editor as bibledb_editor
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

    # Sidebar: Mode buttons
    with st.sidebar:
        st.title("Navigation")
        if st.button("Book Organizer"):
            st.session_state.mode = 1
        if st.button("DB to Book"):
            st.session_state.mode = 2
        if st.button("DB Editor"):
            st.session_state.mode = 3
        st.markdown("---")

    #Everything else
    match st.session_state.mode:
        case 1: #book Organizer
            book_organizer.sidebar()
            book_organizer.body()
        case 2: #bibledb to book
            bibledb_to_book.sidebar()
            bibledb_to_book.body()
        case 3: #bibledb_editor
            bibledb_editor.sidebar()
            bibledb_editor.body()
            
if __name__ == "__main__":
    main()
