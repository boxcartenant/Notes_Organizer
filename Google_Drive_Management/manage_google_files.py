from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import streamlit as st
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload, MediaFileUpload
import json, time
import datetime
import logging

block_content_store = {}

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def generate_unique_block_id(chapter_blocks):
    existing_ids = {block["id"] for block in chapter_blocks}
    i = len(chapter_blocks)
    while True:
        new_id = f"block_{i}_{int(time.time())}"
        if new_id not in existing_ids:
            return new_id
        i += 1

def save_project_manifest(service, rerun = True):
    manifest_content = json.dumps(st.session_state.project["manifest"])
    manifest_file = next((f for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == "manifest.json"), None)
    if manifest_file:
        service.files().update(fileId=manifest_file["id"], media_body=MediaIoBaseUpload(BytesIO(manifest_content.encode("utf-8")), mimetype="application/json")).execute()
    else:
        upload_file(service, manifest_content, "manifest.json", st.session_state.project["folder_id"])
    if rerun:
        st.rerun()

def dump_project_to_files(service):
    """Dump all chapters into text files in an output folder within the project directory."""
    logging.info(f"Time to make the output!")
    # Step 1: Save the project manifest
    save_project_manifest(service, False)
    #logging.info(f"Still going!")

    # Get project folder ID
    project_folder_id = st.session_state.project["folder_id"]
    if not project_folder_id:
        st.error("No project folder set!")
        return

    # Step 2: Handle existing output folder
    files = list_drive_files(service, project_folder_id)
    output_folder = next((f for f in files if f["name"] == "output" and f["mimeType"] == "application/vnd.google-apps.folder"), None)
    if output_folder:
        # Rename to "archive [datetime]"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_name = f"archive_{timestamp}"
        service.files().update(
            fileId=output_folder["id"],
            body={"name": new_name}
        ).execute()
        logging.info(f"Renamed existing output folder to {new_name}")

    # Step 3: Create new output folder
    output_folder_id = create_folder(service, "output", project_folder_id)
    logging.info(f"Created new output folder with ID: {output_folder_id}")

    # Step 4: Process each chapter
    chapters = st.session_state.project["manifest"]["chapters"]
    for chapter_name, blocks in chapters.items():
        # Sort blocks by order
        sorted_blocks = sorted(blocks, key=lambda x: x["order"])
        # Combine block contents
        combined_content = ""
        for block in sorted_blocks:
            if "file_id" in block:
                content = download_file(block["file_id"], service)
                if content == "HTTP 404":
                    logging.warning(f"Block {block['id']} not found, skipping")
                    continue
                combined_content += content + "\n\n"
            else:
                logging.warning(f"Block {block['id']} has no file_id, skipping")
        
        # Remove trailing newline
        combined_content = combined_content.rstrip("\n")
        
        # Upload combined content as a text file
        file_name = f"{chapter_name}.txt"
        upload_file(service, combined_content, file_name, output_folder_id)
        logging.info(f"Created {file_name} in output folder")

    st.success("Project dumped to output files!")

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
    return file_stream.getvalue().decode("utf-8", errors="replace")

def upload_file(service, file_content, file_name, folder_id=None):
    """Upload a file to Google Drive and return the file object."""
    file_metadata = {"name": file_name, "parents": [folder_id] if folder_id else []}
    media = MediaIoBaseUpload(BytesIO(file_content.encode("utf-8")), mimetype="text/plain")
    file = service.files().create(body=file_metadata, media_body=media, fields="id, name").execute()
    return file  # Returns {"id": "abc123", "name": "file_name.txt"}

def create_folder(service, folder_name, parent_id=None):
    """Create a new folder in Google Drive."""
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id] if parent_id else []
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")

def clear_block_cache():
    """Clear all block contents from session_state."""
    if "block_cache" in st.session_state:
        st.session_state.block_cache.clear()
    if "changed_blocks" in st.session_state:
        st.session_state.changed_blocks.clear()  #changed blocks to new empty set

def browse_google_drive(service):
    global block_content_store
    """Google Drive browser with project selection, file uploads, and toggle between project-specific and shared files."""
    # Initialize session state
    if "folder_stack" not in st.session_state:
        st.session_state.folder_stack = []
    if "project" not in st.session_state:
        st.session_state.project = {
            "folder_id": None,
            "folder_name": None,
            "manifest": {"chapters": {"Staging Area": []}},
            "current_chapter": "Staging Area"
        }
    if "uploads_folder_id" not in st.session_state:
        st.session_state.uploads_folder_id = None  # For project-specific uploads
    if "shared_uploads_folder_id" not in st.session_state:
        st.session_state.shared_uploads_folder_id = None  # For shared "Boxcar Notes Uploads"

    with st.sidebar:
        # Step 1: Project Picker (shown if no project is selected)
        if not st.session_state.project["folder_id"]:
            # List top-level project folders (excluding "Boxcar Notes Uploads")
            project_folders = list_drive_files(service, None)
            project_folders = [
                f for f in project_folders
                if f["mimeType"] == "application/vnd.google-apps.folder"
                and f["name"].startswith("BoxcarProj.")
                and f["name"] != "Boxcar Notes Uploads"
            ]
            project_names = [f["name"] for f in project_folders]
            project_names.append("Create New Project")

            # Wrap project selection in a form
            with st.form(key="project_selection_form", clear_on_submit=False):
                # Default to "Create New Project" if it exists in the list
                default_index = len(project_names) - 1 if "Create New Project" in project_names else 0
                selected_project = st.selectbox(
                    "Select a Project",
                    project_names,
                    index=default_index,
                    key="project_selectbox"
                )
                # Add text input for new project name (only shown if "Create New Project" is selected)
                new_project_name = st.text_input(
                    "New Project Name",
                    value="",
                    key="new_project_name",
                    disabled=selected_project != "Create New Project"
                )
                submit_button = st.form_submit_button("Confirm")

                if submit_button and selected_project:
                    if selected_project == "Create New Project":
                        if not new_project_name:
                            st.error("Please enter a project name!")
                        else:
                            # Create the project folder
                            project_folder = create_folder(service, f"BoxcarProj.{new_project_name}", None)
                            # Create an "uploads" subdirectory
                            uploads_folder = create_folder(service, "uploads", project_folder)
                            st.session_state.uploads_folder_id = uploads_folder
                            
                            # Check for "Boxcar Notes Uploads" in root and create if not exists
                            root_files = list_drive_files(service, None)
                            shared_uploads_folder = next((f for f in root_files if f["name"] == "Boxcar Notes Uploads"), None)
                            if shared_uploads_folder:
                                shared_uploads_folder = shared_uploads_folder["id"]
                            else:
                                shared_uploads_folder = create_folder(service, "Boxcar Notes Uploads", None)
                            st.session_state.shared_uploads_folder_id = shared_uploads_folder
                            # Set project state
                            st.session_state.project["folder_id"] = project_folder
                            st.session_state.project["folder_name"] = f"BoxcarProj.{new_project_name}"
                            st.session_state.project["manifest"] = {"chapters": {"Staging Area": []}}
                            # Upload initial manifest
                            upload_file(service, json.dumps(st.session_state.project["manifest"]), "manifest.json", project_folder)
                            st.rerun()
                    else:
                        # User selected an existing project
                        selected_folder = next(f for f in project_folders if f["name"] == selected_project)
                        st.session_state.project["folder_id"] = selected_folder["id"]
                        st.session_state.project["folder_name"] = selected_folder["name"]
                        # Load manifest
                        manifest_file = next((f for f in list_drive_files(service, selected_folder["id"]) if f["name"] == "manifest.json"), None)
                        if not manifest_file:
                            upload_file(service, json.dumps({"chapters": {"Staging Area": []}}), "manifest.json", selected_folder["id"])
                        else:
                            manifest_content = download_file(manifest_file["id"], service)
                            st.session_state.project["manifest"] = json.loads(manifest_content)
                            if "chapters" not in st.session_state.project["manifest"]:
                                st.session_state.project["manifest"]["chapters"] = {"Staging Area": []}
                            st.session_state.project["current_chapter"] = list(st.session_state.project["manifest"]["chapters"].keys())[0]
                        # Set uploads folder IDs
                        uploads_folder = next((f for f in list_drive_files(service, selected_folder["id"]) if f["name"] == "uploads"), None)
                        st.session_state.uploads_folder_id = uploads_folder["id"]
                        root_files = list_drive_files(service, None)
                        shared_uploads_folder = next((f for f in root_files if f["name"] == "Boxcar Notes Uploads"), None)
                        if shared_uploads_folder:
                            shared_uploads_folder = shared_uploads_folder["id"]
                        else:
                            shared_uploads_folder = create_folder(service, "Boxcar Notes Uploads", None)
                        st.session_state.shared_uploads_folder_id = shared_uploads_folder
                        st.rerun()

        # Step 2: File Browser (shown after a project is selected)
        else:
            # Display current project folder
            project_folder_name = st.session_state.project["folder_name"]
            HeaderName = project_folder_name.replace("BoxcarProj.","")
            st.write(f"**Current Project**: {HeaderName}")

            # Toggle to switch between project-specific and shared uploads
            if "show_shared_uploads" not in st.session_state:
                st.session_state.show_shared_uploads = False
            show_shared_uploads = st.toggle("Show files shared by all projects", value=st.session_state.show_shared_uploads) #st.checkbox("Show files for all projects", value=False)
            if show_shared_uploads != st.session_state.show_shared_uploads:
                st.session_state.show_shared_uploads = show_shared_uploads
                st.rerun()
                return
            current_uploads_folder_id = st.session_state.shared_uploads_folder_id if st.session_state.show_shared_uploads else st.session_state.uploads_folder_id
            current_uploads_folder_name = "Boxcar Notes Uploads" if st.session_state.show_shared_uploads else "uploads"
            #logging.info(f"selected folder: {current_uploads_folder_name} : {current_uploads_folder_id}")

            # List files in the current uploads folder
            with st.expander("Files", expanded=False):
                files = list_drive_files(service, current_uploads_folder_id)
                for file in files:
                    if file["name"].endswith(".txt"):
                        if st.button(f"📄 {file['name']}", key=f"file_{file['id']}"):
                            current_chapter = st.session_state.project["current_chapter"]
                            content = download_file(file["id"], service)
                            block_id = generate_unique_block_id(st.session_state.project["manifest"]["chapters"][current_chapter])
                            block_file_name = f"{current_chapter}_{block_id}.txt"
                            # Copy the file into the project folder's root (alongside manifest.json)
                            new_file = upload_file(service, content, block_file_name, st.session_state.project["folder_id"])
                            st.session_state.project["manifest"]["chapters"][current_chapter].append({
                                "id": block_id,
                                "file_path": new_file["name"],
                                "file_id": new_file["id"],
                                "order": len(st.session_state.project["manifest"]["chapters"][current_chapter])
                            })
                            block_content_store[new_file["id"]] = content
                            save_project_manifest(service)

            # Chapter management
            #st.write("### Chapters")
            with st.expander("Chapters", expanded=True):
                chapters = list(st.session_state.project["manifest"]["chapters"].keys())
                new_target_chapter = st.selectbox("Current Chapter", chapters, index=chapters.index(st.session_state.project["current_chapter"]))
                if new_target_chapter and new_target_chapter != st.session_state.project["current_chapter"]:
                    clear_block_cache()  # Clear cache when switching chapters
                    st.session_state.project["current_chapter"] = new_target_chapter
                    st.rerun()
                with st.form(key="New_Chapter_Name", clear_on_submit=True, enter_to_submit=True):
                    new_chapter = st.text_input("New Chapter Name", key="new_chapter")
                    submitted = st.form_submit_button("Add Chapter")
                    if submitted and new_chapter and new_chapter not in chapters:
                        st.session_state.project["manifest"]["chapters"][new_chapter] = []
                        st.success("Chapter Added!")
                        st.rerun()

            # Save and Dump buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Project"):
                    save_project_manifest(service)
            with col2:
                if st.button("Dump to Output Files"):
                    dump_project_to_files(service)
            if "show_shared_uploads" not in st.session_state:
                st.session_state.show_shared_uploads = False

            with st.expander("Upload Files", expanded=False):
                # File uploader to the current folder (either project-specific "uploads" or shared "Boxcar Notes Uploads")
                with st.form(key="file_upload_form", clear_on_submit=True):
                    uploaded_files = st.file_uploader(
                        f"Upload .txt files to '{current_uploads_folder_name}'",
                        type="txt",
                        accept_multiple_files=True,
                        key="file_uploader"
                    )
                    submit_button = st.form_submit_button("Upload Files")
                    if submit_button and uploaded_files:
                        for uploaded_file in uploaded_files:
                            content = uploaded_file.read().decode("utf-8", errors="replace")
                            file_name = uploaded_file.name
                            logging.info(f"Uploading: {file_name}")
                            upload_file(service, content, file_name, current_uploads_folder_id)
                            st.success(f"Uploaded {file_name} to {current_uploads_folder_name}!")
                        # Clear the uploader's state
                        #st.session_state["file_uploader"] = []
                        st.rerun()


        with st.expander("Settings", expanded = False):
            #Mobile friendly view: changes the buttons under the blocks to a dropdown list
            old_mobile_friendly = st.session_state.mobile_friendly_view
            st.session_state.mobile_friendly_view = st.checkbox("Mobile-Friendly View", value=st.session_state.mobile_friendly_view)
            if old_mobile_friendly != st.session_state.mobile_friendly_view:
                st.rerun()
            
            #Mobile Boxsize Fixed: Shows a slider to resize textboxes under every block
            if st.session_state.mobile_friendly_view:
                old_mobile_boxsize_fixed = st.session_state.mobile_boxsize_fixed
                st.session_state.mobile_boxsize_fixed = st.checkbox("Slider under every block", value=st.session_state.mobile_boxsize_fixed)
                if old_mobile_boxsize_fixed != st.session_state.mobile_boxsize_fixed:
                    st.rerun()
            
            #Default Box Size: sets the default height of textboxes in blocks
            old_default_box_size = st.session_state.default_box_size
            st.session_state.default_box_size = st.slider(f"Adjust default block height", min_value=100, max_value=600, value=st.session_state.default_box_size)
            if old_default_box_size != st.session_state.default_box_size:
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