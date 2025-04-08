import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from urllib.parse import urlencode
import book_organizer
from Google_Drive_Management.manage_google_files import *


def main():
    logged_in = False

    myLogoUrl = "https://boxcarprojectspace.wordpress.com/wp-content/uploads/2025/03/wing-pen-1.jpg"
    st.logo(image = myLogoUrl, link = myLogoUrl)
    st.set_page_config(page_title="Boxcar-Notes", page_icon=myLogoUrl)

    if not "mobile_friendly_view" in st.session_state:
        st.session_state.mobile_friendly_view = False
        st.session_state.mobile_boxsize_fixed = False
        st.session_state.default_box_size = 150

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
        st.write("If you are like me, you have hundreds of pages of notes stored in .txt files, \
and you want to organize them into topical units (“chapters”) and present the information in an orderly manner.\n\n \
This project is a tool for organizing notes into chapters...like if you're writing a book. \
It creates a folder on your google drive for your project, and another folder for txt files you want to use across projects. To get started:")
        st.write("- Log into your google drive account using the button on the expander (left).")
        st.write("When you’re done, you can dump the contents of the project to a folder called “output”, which will contain a single \".txt\" file for each chapter.")
        
            
if __name__ == "__main__":
    main()
