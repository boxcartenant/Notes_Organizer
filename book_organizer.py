import streamlit as st
from Google_Drive_Management.manage_google_files import browse_google_drive, download_file, upload_file, build, list_drive_files, save_project_manifest
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import time
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)

def download_file_wrapper(file_id, service, from_session_state=True):
    """Wrapper for download_file to fetch from session_state or Google Drive."""
    if "block_cache" not in st.session_state:
        st.session_state.block_cache = {}
    
    if from_session_state and file_id in st.session_state.block_cache:
        return st.session_state.block_cache[file_id]
    
    try:
        content = download_file(file_id, service)
        st.session_state.block_cache[file_id] = content
        return content
    except HttpError as error:
        if error.resp.status == 404:
            logging.warning(f"File not found: {file_id}")
            return "HTTP 404"
        raise

def update_block_filepath(block, chapter):
    """Update a block's file_path to include chapter prefix."""
    if "file_id" in block:
        block["file_path"] = f"{chapter}_{block['id']}.txt"
    return block

def body(service):
    st.write("#### == DB Organizer ==")

    # Initialize session state
    if "project" not in st.session_state:
        st.session_state.project = {
            "folder_id": None,
            "manifest": {"chapters": {"Staging Area": []}},
            "current_chapter": "Staging Area"
        }
    if "block_cache" not in st.session_state:
        st.session_state.block_cache = {}
    if "changed_blocks" not in st.session_state:
        st.session_state.changed_blocks = set()

    # Enforce set type (workaround for Streamlit serialization)
    if not isinstance(st.session_state.changed_blocks, set):
        st.session_state.changed_blocks = set(st.session_state.changed_blocks)

    current_chapter = st.session_state.project["current_chapter"]
    blocks = sorted(st.session_state.project["manifest"]["chapters"][current_chapter], key=lambda x: x["order"])

    for idx, block in enumerate(blocks):
        existing_file = next((f for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == block["file_path"]), None)
        from_session_state = True
        if "file_id" in block and block["file_id"] in st.session_state.changed_blocks:
            from_session_state = False
        block_content = download_file_wrapper(block["file_id"], service, from_session_state) if "file_id" in block else ""
        
        if block_content == "HTTP 404":
            logging.info(f"Removing missing block {block['id']} from manifest")
            if existing_file and existing_file["id"] in st.session_state.block_cache:
                del st.session_state.block_cache[existing_file["id"]]
            if existing_file:
                try:
                    service.files().delete(fileId=existing_file["id"]).execute()
                except HttpError:
                    pass  # File already gone
            st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
            save_project_manifest(service)
            st.rerun()
            break

        new_content = st.text_area(f"Block {idx + 1} ({current_chapter})", value=block_content, key=f"textblock_{block['id']}")

        if new_content != block_content:
            if "file_id" in block:
                media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
                service.files().update(fileId=block["file_id"], media_body=media).execute()
                st.session_state.block_cache[block["file_id"]] = new_content
                st.session_state.changed_blocks.add(block["file_id"])
            else:
                block_file_name = f"{current_chapter}_{block['id']}.txt"
                new_file = upload_file(service, new_content, block_file_name, st.session_state.project["folder_id"])
                block["file_path"] = block_file_name
                block["file_id"] = new_file["id"]
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
                if "file_id" in block and block["file_id"] in st.session_state.block_cache:
                    del st.session_state.block_cache[block["file_id"]]
                if "file_id" in block:
                    service.files().delete(fileId=block["file_id"]).execute()
                st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                save_project_manifest(service)
                st.rerun()
                break
        with col4:
            if st.button(f"🔗 {idx}", key=f"merge_down_{block['id']}") and idx < len(blocks) - 1):
                try:
                    next_block = blocks[idx + 1]
                    next_file = next((f for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == next_block["file_path"]), None)
                    next_content = download_file_wrapper(next_block["file_id"], service) if "file_id" in next_block else ""
                    if next_content == "HTTP 404":
                        st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                        save_project_manifest(service)
                        st.rerun()
                        break
                    merged_content = block_content + "\n\n" + next_content
                    
                    if "file_id" in block:
                        media = MediaIoBaseUpload(BytesIO(merged_content.encode("utf-8")), mimetype="text/plain")
                        service.files().update(fileId=block["file_id"], media_body=media).execute()
                        st.session_state.block_cache[block["file_id"]] = merged_content
                        st.session_state.changed_blocks.add(block["file_id"])
                        logging.info(f"Updated file: {block["file_id"]}")
                    
                    if next_file:
                        if next_file["id"] in st.session_state.block_cache:
                            del st.session_state.block_cache[next_file["id"]]
                            logging.info(f"Deleted cache for file: {next_file['id']}")
                        service.files().delete(fileId=next_file["id"]).execute()
                        logging.info(f"Deleted file: {next_file['id']}")
                    
                    st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                    save_project_manifest(service)
                    st.rerun()
                except HttpError as e:
                    logging.error(f"Error during merge: {e}")
                    if e.resp.status == 404:
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
                block_to_move = update_block_filepath(block_to_move, target_chapter)
                if "file_id" in block:
                    media = MediaIoBaseUpload(BytesIO(block_content.encode("utf-8")), mimetype="text/plain")
                    service.files().update(fileId=block["file_id"], media_body=media, body={"name": block_to_move["file_path"]}).execute()
                    st.session_state.block_cache[block["file_id"]] = block_content
                st.session_state.project["manifest"]["chapters"][target_chapter].append(block_to_move)
                save_project_manifest(service)
                st.rerun()
                break

    if st.button("Add Empty Block"):
        block_id = f"block_{len(st.session_state.project['manifest']['chapters'][current_chapter])}_{int(time.time())}"
        block_file_name = f"{block_id}.txt"
        new_file = upload_file(service, "", block_file_name, st.session_state.project["folder_id"])
        st.session_state.project["manifest"]["chapters"][current_chapter].append({
            "id": block_id,
            "file_path": new_file["name"],
            "file_id": new_file["id"],
            "order": len(st.session_state.project["manifest"]["chapters"][current_chapter])
        })
        st.session_state.block_cache[new_file["id"]] = ""
        st.rerun()