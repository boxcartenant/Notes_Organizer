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


def download_file_wrapper(file_id, service, from_session_state=True):
    """Wrapper for download_file to fetch from session_state or Google Drive."""
    if "block_cache" not in st.session_state:
        st.session_state.block_cache = {}
    
    if from_session_state and file_id in st.session_state.block_cache:
        return st.session_state.block_cache[file_id]
    
    # Fetch from Google Drive and update session_state
    content = download_file(file_id, service)
    st.session_state.block_cache[file_id] = content
    return content


def body(service):
    st.write("DB Organizer")

    # Ensure project and session state are initialized
    if "project" not in st.session_state:
        st.session_state.project = {
            "folder_id": None,
            "manifest": {"chapters": {"Chapter 1": []}},
            "current_chapter": "Chapter 1"
        }
    if "block_cache" not in st.session_state:
        st.session_state.block_cache = {}
    if "changed_blocks" not in st.session_state:
        st.session_state.changed_blocks = set()  # Initialize as a set for unique IDs

    current_chapter = st.session_state.project["current_chapter"]
    blocks = sorted(st.session_state.project["manifest"]["chapters"][current_chapter], key=lambda x: x["order"])

    for idx, block in enumerate(blocks):
        existing_file = next((f for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == block["file_path"]), None)
        # Check whether this block needs to be re-cached
        from_session_state = True
        if "file_id" in block and block["file_id"] in st.session_state.changed_blocks:
            from_session_state = False
        # Get contents of block
        block_content = download_file_wrapper(block["file_id"], service, from_session_state) if "file_id" in block else ""
        new_content = st.text_area(f"Block {idx + 1} ({current_chapter})", value=block_content, key=f"textblock_{block['id']}")

        # Save changed/new files to Google Drive and update cache
        if new_content != block_content:
            if existing_file:
                media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
                service.files().update(fileId=existing_file["id"], media_body=media).execute()
                st.session_state.block_cache[existing_file["id"]] = new_content  # Sync cache
                st.session_state.changed_blocks.add(existing_file["id"])  # Track change
            else:
                new_file = upload_file(service, new_content, block["file_path"], st.session_state.project["folder_id"])
                block["file_path"] = new_file["name"]
                block["file_id"] = new_file["id"]  # Ensure file_id is stored in manifest
                st.session_state.block_cache[new_file["id"]] = new_content
                st.session_state.changed_blocks.add(new_file["id"])

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button(f"⬆ {idx}", key=f"move_up_{block['id']}") and idx > 0:
                blocks[idx]["order"], blocks[idx - 1]["order"] = blocks[idx - 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                save_project_manifest(service)
                st.rerun()
                break
        with col2:
            if st.button(f"⬇ {idx}", key=f"move_down_{block['id']}") and idx < len(blocks) - 1:
                blocks[idx]["order"], blocks[idx + 1]["order"] = blocks[idx + 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                save_project_manifest(service)
                st.rerun()
                break
        with col3:
            if st.button(f"🗑 {idx}", key=f"delete_{block['id']}"):
                if existing_file and existing_file["id"] in st.session_state.block_cache:
                    del st.session_state.block_cache[existing_file["id"]]
                if existing_file:
                    service.files().delete(fileId=existing_file["id"]).execute()
                st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                save_project_manifest(service)
                st.rerun()
                break
        with col4:
            if st.button(f"🔗 {idx}", key=f"merge_down_{block['id']}") and idx < len(blocks) - 1:
                next_block = blocks[idx + 1]
                next_file = next((f for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == next_block["file_path"]), None)
                next_content = download_file_wrapper(next_file["id"], service) if next_file and "file_id" in next_block else ""
                merged_content = block_content + "\n" + next_content
                if existing_file:
                    media = MediaIoBaseUpload(BytesIO(merged_content.encode("utf-8")), mimetype="text/plain")
                    service.files().update(fileId=existing_file["id"], media_body=media).execute()
                    st.session_state.block_cache[existing_file["id"]] = merged_content
                    st.session_state.changed_blocks.add(existing_file["id"])
                if next_file:
                    if next_file["id"] in st.session_state.block_cache:
                        del st.session_state.block_cache[next_file["id"]]
                    service.files().delete(fileId=next_file["id"]).execute()
                st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                save_project_manifest(service)
                st.rerun()
                break
        with col5:
            chapters = list(st.session_state.project["manifest"]["chapters"].keys())
            target_chapter = st.selectbox(f"Move {idx}", [""] + chapters, key=f"move_{block['id']}", label_visibility="collapsed")
            if target_chapter and target_chapter != current_chapter:
                block_to_move = st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                block_to_move["order"] = len(st.session_state.project["manifest"]["chapters"][target_chapter])
                st.session_state.project["manifest"]["chapters"][target_chapter].append(block_to_move)
                save_project_manifest(service)
                st.rerun()
                break

    if st.button("Add Empty Block"):
        block_id = f"block_{len(st.session_state.project['manifest']['chapters'][current_chapter])}"
        block_file_name = f"{block_id}.txt"
        new_file = upload_file(service, "", block_file_name, st.session_state.project["folder_id"])
        st.session_state.project["manifest"]["chapters"][current_chapter].append({
            "id": block_id,
            "file_path": block_file_name,
            "file_id": new_file,  # Store file_id in manifest
            "order": len(st.session_state.project["manifest"]["chapters"][current_chapter])
        })
        st.session_state.block_cache[new_file] = ""  # Cache empty content
        st.rerun()

    # Reset changed_blocks only on chapter switch (via clear_block_cache) or manual action, not here

