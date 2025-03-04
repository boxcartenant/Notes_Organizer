from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import streamlit as st
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import json

SCOPES = ['https://www.googleapis.com/auth/drive']  # Updated scope for read/write access

#OK ZAC -- troubleshoot this by comparing with the revision you mostly wrote, a few rev's back.

def list_drive_files(service, folder_id=None):
    """List files and folders in Google Drive."""
    query = "'root' in parents" if not folder_id else f"'{folder_id}' in parents"
    query += " and trashed=false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get("files", [])

def download_file(file_id, service):
    """Download a file from Google Drive as string."""
    request = service.files().get_media(fileId=file_id)
    file_stream = BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file_stream.seek(0)
    return file_stream.getvalue().decode("utf-8")

def upload_file(service, file_content, file_name, folder_id=None):
    """Upload a file to Google Drive."""
    file_metadata = {"name": file_name, "parents": [folder_id] if folder_id else []}
    media = MediaFileUpload(BytesIO(file_content.encode("utf-8")), mimetype="text/plain")
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file.get("id")

def create_folder(service, folder_name, parent_id=None):
    """Create a new folder in Google Drive."""
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id] if parent_id else []
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")

def browse_google_drive(service):
    """Google Drive browser with folder selection and creation."""
    # Initialize session state
    if "folder_stack" not in st.session_state:
        st.session_state.folder_stack = []
    if "project" not in st.session_state:
        st.session_state.project = {
            "folder_id": None,
            "manifest": {"chapters": {"Chapter 1": []}},
            "current_chapter": "Chapter 1"
        }

    current_folder = st.session_state.folder_stack[-1] if st.session_state.folder_stack else None
    files = list_drive_files(service, current_folder)

    with st.sidebar:
        # Navigation
        st.write("### Google Drive Browser")
        if st.session_state.folder_stack and st.button("⬆ Go Up", key="go_up"):
            st.session_state.folder_stack.pop()
            st.rerun()

        # Project status
        project_folder_name = "Not set" if not st.session_state.project["folder_id"] else next((f["name"] for f in files if f["id"] == st.session_state.project["folder_id"]), "Unknown")
        st.write(f"**Current Project Folder**: {project_folder_name}")

        # Folder creation
        with st.expander("Create New Folder", expanded=False):
            new_folder_name = st.text_input("Folder Name", key="new_folder_name")
            if st.button("Create", key="create_folder") and new_folder_name:
                new_folder_id = create_folder(service, new_folder_name, current_folder)
                st.success(f"Created folder: {new_folder_name}")
                st.rerun()

        # Folder/file selection
        with st.expander("Folders and Files", expanded=True):
            for file in files:
                if file["mimeType"] == "application/vnd.google-apps.folder":
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"📁 {file['name']}", key=f"folder_{file['id']}"):
                            st.session_state.folder_stack.append(file["id"])
                            st.rerun()
                    with col2:
                        if st.button("Set", key=f"set_{file['id']}"):
                            st.session_state.project["folder_id"] = file["id"]
                            manifest_file = next((f for f in list_drive_files(service, file["id"]) if f["name"] == "manifest.json"), None)
                            if not manifest_file:
                                upload_file(service, json.dumps({"chapters": {"Chapter 1": []}}), "manifest.json", file["id"])
                            else:
                                manifest_content = download_file(manifest_file["id"], service)
                                st.session_state.project["manifest"] = json.loads(manifest_content)
                                if "chapters" not in st.session_state.project["manifest"]:
                                    st.session_state.project["manifest"]["chapters"] = {"Chapter 1": []}
                                st.session_state.project["current_chapter"] = list(st.session_state.project["manifest"]["chapters"].keys())[0]
                            st.success(f"Project folder set to: {file['name']}")
                            st.rerun()
                else:
                    if st.button(f"📄 {file['name']}", key=f"file_{file['id']}"):
                        if not st.session_state.project["folder_id"]:
                            st.error("Please set a project folder first!")
                        else:
                            content = download_file(file["id"], service)
                            block_id = f"block_{len(st.session_state.project['manifest']['chapters'][st.session_state.project['current_chapter']])}"
                            block_file_name = f"{block_id}.txt"
                            upload_file(service, content, block_file_name, st.session_state.project["folder_id"])
                            st.session_state.project["manifest"]["chapters"][st.session_state.project["current_chapter"]].append({
                                "id": block_id,
                                "file_path": block_file_name,
                                "order": len(st.session_state.project["manifest"]["chapters"][st.session_state.project["current_chapter"]])
                            })
                            st.success(f"Added {file['name']} to {st.session_state.project['current_chapter']}")
                            st.rerun()

        # Save project
        if st.session_state.project["folder_id"] and st.button("Save Project"):
            manifest_content = json.dumps(st.session_state.project["manifest"])
            manifest_file = next((f for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == "manifest.json"), None)
            if manifest_file:
                service.files().update(fileId=manifest_file["id"], media_body=MediaFileUpload(BytesIO(manifest_content.encode("utf-8")), mimetype="application/json")).execute()
            else:
                upload_file(service, manifest_content, "manifest.json", st.session_state.project["folder_id"])
            st.success("Project saved!")

        # Chapter management
        if st.session_state.project["folder_id"]:
            st.write("### Chapters")
            with st.expander("Manage Chapters", expanded=True):
                chapters = list(st.session_state.project["manifest"]["chapters"].keys())
                st.session_state.project["current_chapter"] = st.selectbox("Current Chapter", chapters, index=chapters.index(st.session_state.project["current_chapter"]))
                new_chapter = st.text_input("New Chapter Name")
                if st.button("Add Chapter") and new_chapter and new_chapter not in chapters:
                    st.session_state.project["manifest"]["chapters"][new_chapter] = []
                    st.rerun()

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
            return True
        else:
            flow = create_auth_flow()
            auth_url, _ = flow.authorization_url(prompt="consent")
            st.write("Click the link below to log in:")
            st.markdown(f"[Log in with Google]({auth_url})")
            return False
    else:
        return True