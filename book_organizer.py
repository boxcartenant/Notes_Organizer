import streamlit as st
from Google_Drive_Management.manage_google_files import browse_google_drive, download_file, upload_file, build, list_drive_files, save_project_manifest
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from io import BytesIO

# === Book Organizer ===
# These functions are for grabbing and rearranging text in my many notes,
#  and for saving their new arrangement in some kind of book file that I 
#  haven't structured yet.
# 
# So far, you can add, delete, and rearrange text blocks.

def body(service):
    st.title("DB Organizer")

    # Ensure project is initialized
    if "project" not in st.session_state:
        st.session_state.project = {
            "folder_id": None,
            "manifest": {"chapters": {"Chapter 1": []}},
            "current_chapter": "Chapter 1"
        }

    # Get blocks for the current chapter
    current_chapter = st.session_state.project["current_chapter"]
    blocks = sorted(st.session_state.project["manifest"]["chapters"][current_chapter], key=lambda x: x["order"])

    # Display blocks
    for idx, block in enumerate(blocks):
        existing_file = next((f for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == block["file_path"]), None)
        block_content = download_file(next(f["id"] for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == block["file_path"]), service)
        new_content = st.text_area(f"Block {idx + 1} ({current_chapter})", value=block_content, key=f"textblock_{block['id']}")
        
        # Update the file if content has changed
        if new_content != block_content:
            if existing_file:
                # Update existing file
                media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
                service.files().update(fileId=existing_file["id"], media_body=media).execute()
            else:
                # Create new file if it somehow doesn't exist (shouldn't happen with proper manifest)
                new_file = upload_file(service, new_content, block["file_path"], st.session_state.project["folder_id"])
                block["file_path"] = new_file["name"]  # Update manifest with the new file name (redundant but safe)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button(f"⬆ {idx}", key=f"move_up_{block['id']}") and idx > 0:
                blocks[idx]["order"], blocks[idx - 1]["order"] = blocks[idx - 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                save_project_manifest(service)
                st.rerun()
        with col2:
            if st.button(f"⬇ {idx}", key=f"move_down_{block['id']}") and idx < len(blocks) - 1:
                blocks[idx]["order"], blocks[idx + 1]["order"] = blocks[idx + 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                save_project_manifest(service)
                st.rerun()
        with col3:
            if st.button(f"🗑 {idx}", key=f"delete_{block['id']}"):
                st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                save_project_manifest(service)
                st.rerun()
        with col4:
            chapters = list(st.session_state.project["manifest"]["chapters"].keys())
            target_chapter = st.selectbox(f"Move {idx}", [""] + chapters, key=f"move_{block['id']}", label_visibility="collapsed")
            if target_chapter and target_chapter != current_chapter:
                block_to_move = st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                block_to_move["order"] = len(st.session_state.project["manifest"]["chapters"][target_chapter])
                st.session_state.project["manifest"]["chapters"][target_chapter].append(block_to_move)
                save_project_manifest(service)
                st.rerun()

    if st.button("Add Empty Block"):
        block_id = f"block_{len(st.session_state.project['manifest']['chapters'][current_chapter])}"
        block_file_name = f"{block_id}.txt"
        upload_file(service, "", block_file_name, st.session_state.project["folder_id"])
        st.session_state.project["manifest"]["chapters"][current_chapter].append({
            "id": block_id,
            "file_path": block_file_name,
            "order": len(st.session_state.project["manifest"]["chapters"][current_chapter])
        })
        st.rerun()

