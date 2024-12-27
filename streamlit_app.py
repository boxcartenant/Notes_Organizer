import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from urllib.parse import urlencode
from manage_google_files import *

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']




# Streamlit app interface
st.title("Google Drive Viewer")
authenticate_user()

if st.button("List My Files"):
    files = list_drive_files()
    if files:
        st.write("Files:")
        for file in files:
            st.write(f"{file['name']} ({file['id']})")
    else:
        st.write("No files found.")

#if "credentials" in st.session_state:
#    print("credentials in the sesh")
#    files = list_drive_files()

#    if files:
#        print("files in the drive")
#        # Create a dropdown for file selection
#        file_options = {file["name"]: file["id"] for file in files}
#        selected_file_name = st.selectbox("Select a file to download:", list(file_options.keys()))
#        selected_file_id = file_options[selected_file_name]

#        if st.button("Download and View File"):
#            print("where is this button, yo?")
#            file_content = download_file(selected_file_id)
#            if file_content:
#                st.write("File Content:")
#                if isinstance(file_content, str):
#                    st.code(file_content[:500])  # Show first 500 characters for text files
#                else:
#                    st.write("Binary file content loaded successfully.")
#    else:
#        st.write("No files found in your Google Drive.")
