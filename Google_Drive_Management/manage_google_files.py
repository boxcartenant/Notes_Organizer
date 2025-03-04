import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
#from urllib.parse import urlencode
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import json

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def create_auth_flow():
    """Create an OAuth flow using Streamlit secrets."""
    client_config = {
        "web": {
            "client_id": st.secrets["google"]["client_id"],
            "client_secret": st.secrets["google"]["client_secret"],
            "redirect_uris": [st.secrets["google"]["redirect_uri"]],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=st.secrets["google"]["redirect_uri"])

def authenticate_user():
    """Authenticate user with Google OAuth 2.0."""
    if "credentials" not in st.session_state:
        query_params = st.query_params
        if "code" in query_params:
            flow = create_auth_flow()
            flow.fetch_token(code=query_params["code"])
            creds = flow.credentials
            # Manually extract credentials to store in session state
            st.session_state["credentials"] = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }
            st.success("Authentication successful!")
            st.query_params.clear()
            #st.rerun()
            return True
        else:
            flow = create_auth_flow()
            auth_url, _ = flow.authorization_url(prompt="consent")
            st.write("Click the link below to log in:")
            st.markdown(f"[Log in with Google]({auth_url})")
            return False
    else:
        return True




def list_drive_files(service, folder_id=None):
    """List files and folders in Google Drive."""
    query = "'root' in parents" if not folder_id else f"'{folder_id}' in parents"
    query += " and trashed=false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get("files", [])

def download_file(file_id, service):
    """Download a file from Google Drive as bytes."""
    request = service.files().get_media(fileId=file_id)
    file_stream = BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file_stream.seek(0)
    return file_stream.getvalue().decode("utf-8")  # Decode bytes to string

def upload_file(service, file_content, file_name, folder_id=None):
    """Upload a file to Google Drive."""
    file_metadata = {"name": file_name, "parents": [folder_id] if folder_id else []}
    media = MediaFileUpload(BytesIO(file_content.encode("utf-8")), mimetype="text/plain")
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file.get("id")

def browse_google_drive(service):
    """Google Drive browser with cleaner UX."""
    # Initialize session state for navigation and project
    if "folder_stack" not in st.session_state:
        st.session_state.folder_stack = []
    if "project" not in st.session_state:
        st.session_state.project = {"folder_id": None, "manifest": {"blocks": []}}

    current_folder = st.session_state.folder_stack[-1] if st.session_state.folder_stack else None
    files = list_drive_files(service, current_folder)

    # Navigation
    with st.sidebar:
        st.write("### Google Drive Browser")
        if st.session_state.folder_stack and st.button("⬆ Go Up", key="go_up"):
            st.session_state.folder_stack.pop()
            st.rerun()

        # Folder/file selection with expander for better mobile UX
        with st.expander("Folders and Files", expanded=True):
            for file in files:
                if file["mimeType"] == "application/vnd.google-apps.folder":
                    if st.button(f"📁 {file['name']}", key=f"folder_{file['id']}"):
                        st.session_state.folder_stack.append(file["id"])
                        st.rerun()
                else:
                    if st.button(f"📄 {file['name']}", key=f"file_{file['id']}"):
                        content = download_file(file["id"], service)
                        # Instead of storing full content in session_state, add to project
                        block_id = f"block_{len(st.session_state.project['manifest']['blocks'])}"
                        block_file_name = f"{block_id}.txt"
                        upload_file(service, content, block_file_name, st.session_state.project["folder_id"])
                        st.session_state.project["manifest"]["blocks"].append({
                            "id": block_id,
                            "file_path": block_file_name,
                            "order": len(st.session_state.project["manifest"]["blocks"])
                        })
                        st.success(f"Added {file['name']} as block {block_id}")
                        st.rerun()

        # Project management
        st.write("### Project")
        project_folder = st.text_input("Project Folder ID", value=st.session_state.project["folder_id"] or "")
        if st.button("Set Project Folder"):
            st.session_state.project["folder_id"] = project_folder
            # Check if manifest exists, otherwise create it
            manifest_file = next((f for f in list_drive_files(service, project_folder) if f["name"] == "manifest.json"), None)
            if not manifest_file:
                upload_file(service, json.dumps({"blocks": []}), "manifest.json", project_folder)
            else:
                manifest_content = download_file(manifest_file["id"], service)
                st.session_state.project["manifest"] = json.loads(manifest_content)
            st.rerun()

        if st.button("Save Project"):
            manifest_content = json.dumps(st.session_state.project["manifest"])
            manifest_file = next((f for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == "manifest.json"), None)
            if manifest_file:
                service.files().update(fileId=manifest_file["id"], media_body=MediaFileUpload(BytesIO(manifest_content.encode("utf-8")), mimetype="application/json")).execute()
            else:
                upload_file(service, manifest_content, "manifest.json", st.session_state.project["folder_id"])
            st.success("Project saved!")