import json
import streamlit as st
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from io import BytesIO

#workflow: 
#  list_projects() #creates a list of projects to load
#  each button has the name of a project; clicking a button loads the project.


def list_projects():
    """Lists project files in '/streamlit work' on Google Drive inside a collapsible expander."""
    creds = Credentials.from_authorized_user_info(st.session_state["credentials"])
    service = build('drive', 'v3', credentials=creds)

    folder_id = get_folder_id(service)
    
    # Get all project files (.json) in the folder
    query = f"'{folder_id}' in parents and mimeType='application/json' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        st.write("No saved projects found.")
        return

    with st.expander("📂 Load a Project", expanded=False):
        for file in files:
            project_name = file["name"].replace(".json", "")  # Remove .json extension
            if st.button(f"📄 {project_name}", key=f"load_{project_name}"):
                load_project(project_name)
                st.session_state["current_project"] = project_name  # Store project name



def get_folder_id(service, folder_name="streamlit work"):
    """Get or create a folder in Google Drive."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    folders = results.get("files", [])

    if folders:
        return folders[0]["id"]  # Return existing folder ID

    # Create the folder if it doesn't exist
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder["id"]

def save_project(project_name):
    """Save the current text organization as a JSON project file on Google Drive."""
    if "textblocks" not in st.session_state or "gdrive_files" not in st.session_state:
        st.error("No project data to save.")
        return

    creds = Credentials.from_authorized_user_info(st.session_state["credentials"])
    service = build('drive', 'v3', credentials=creds)

    folder_id = get_folder_id(service)

    project_data = {
        "project_name": project_name,
        "files": st.session_state["gdrive_files"],  # Original files
        "textblocks": st.session_state.textblocks   # Ordered text
    }

    # Convert to JSON
    project_json = json.dumps(project_data, indent=4)
    file_stream = BytesIO(project_json.encode("utf-8"))

    # Check if the file already exists
    query = f"name='{project_name}.json' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    existing_files = results.get("files", [])

    file_metadata = {
        "name": f"{project_name}.json",
        "parents": [folder_id],
        "mimeType": "application/json"
    }

    if existing_files:
        file_id = existing_files[0]["id"]
        service.files().update(fileId=file_id, media_body=MediaFileUpload(file_stream, mimetype="application/json")).execute()
    else:
        service.files().create(body=file_metadata, media_body=MediaFileUpload(file_stream, mimetype="application/json")).execute()

    st.success(f"Project '{project_name}' saved successfully to Google Drive!")

def load_project(project_name):
    """Load a project from Google Drive."""
    creds = Credentials.from_authorized_user_info(st.session_state["credentials"])
    service = build('drive', 'v3', credentials=creds)

    folder_id = get_folder_id(service)

    # Find the project file
    query = f"name='{project_name}.json' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])

    if not files:
        st.error(f"Project '{project_name}' not found.")
        return

    file_id = files[0]["id"]
    request = service.files().get_media(fileId=file_id)
    file_stream = BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_stream.seek(0)
    project_data = json.load(file_stream)

    # Restore session state
    st.session_state["gdrive_files"] = project_data["files"]
    st.session_state.textblocks = project_data["textblocks"]

    st.success(f"Project '{project_name}' loaded successfully from Google Drive!")
