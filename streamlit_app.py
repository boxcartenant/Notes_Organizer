import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from urllib.parse import urlencode

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
        query_params = st.query_params()
        if "code" in query_params:
            flow = create_auth_flow()
            flow.fetch_token(code=query_params["code"][0])
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
        else:
            flow = create_auth_flow()
            auth_url, _ = flow.authorization_url(prompt="consent")
            st.write("Click the link below to log in:")
            st.markdown(f"[Log in with Google]({auth_url})")
    else:
        st.success("You are already logged in!")


def list_drive_files():
    """List files in Google Drive."""
    if "credentials" in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state["credentials"])
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(pageSize=10, fields="files(id, name)").execute()
        files = results.get("files", [])
        return files
    else:
        st.error("Please authenticate first.")

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
