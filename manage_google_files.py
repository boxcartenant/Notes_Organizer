import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
#from urllib.parse import urlencode
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload

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
            return True
        else:
            flow = create_auth_flow()
            auth_url, _ = flow.authorization_url(prompt="consent")
            st.write("Click the link below to log in:")
            st.markdown(f"[Log in with Google]({auth_url})")
            return False
    else:
        st.success("You are already logged in!")
        return True


def old_list_drive_files():
    """List files in Google Drive."""
    if "credentials" in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state["credentials"])
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(pageSize=10, fields="files(id, name)").execute()
        files = results.get("files", [])
        return files
    else:
        st.error("Please authenticate first.")
        return []

def list_drive_files(service, folder_id=None):
    """List files and folders in Google Drive."""
    query = "'root' in parents" if not folder_id else f"'{folder_id}' in parents"
    query += " and trashed=false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get("files", [])

def browse_google_drive():
    """Implement a file browser for Google Drive."""
    if "credentials" in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state["credentials"])
        service = build('drive', 'v3', credentials=creds)

        folder_stack = st.session_state.get("folder_stack", [])
        current_folder = folder_stack[-1] if folder_stack else None

        # Get files and folders in the current folder
        files = list_drive_files(service, current_folder)

        if folder_stack:
            if st.button("Go Up One Level"):
                folder_stack.pop()
                st.session_state["folder_stack"] = folder_stack
                st.query_params.clear()

        # Display files and folders
        for file in files:
            if file["mimeType"] == "application/vnd.google-apps.folder":
                if st.button(f"Open Folder: {file['name']}"):
                    folder_stack.append(file["id"])
                    st.session_state["folder_stack"] = folder_stack
                    st.query_params.clear()
            else:
                if st.button(f"Download File: {file['name']}"):
                    file_content = download_file(file["id"], service)
                    if file_content:
                        st.write(f"File '{file['name']}' downloaded successfully!\n{file_content}")

    else:
        st.error("Please authenticate first.")

def download_file(file_id, service):
    """Download a file from Google Drive."""
    # Get file metadata
    file = service.files().get(fileId=file_id, fields="name, mimeType").execute()
    file_name = file["name"]

    # Download the file content
    request = service.files().get_media(fileId=file_id)
    file_stream = BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_stream.seek(0)
    return file_stream.getvalue()