import streamlit as st
from Google_Drive_Management.manage_google_files import browse_google_drive, download_file, upload_file, build, list_drive_files, save_project_manifest
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import logging
import time
from io import BytesIO

logging.basicConfig(level=logging.INFO)

block_content_store = {}

def download_file_wrapper(file_id, service):
    global block_content_store
    if file_id not in block_content_store:
        try:
            content = download_file(file_id, service)
            block_content_store[file_id] = content
            return content
        except HttpError as error:
            if error.resp.status == 404:
                logging.warning(f"File not found: {file_id}")
                return "HTTP 404"
            raise
    return block_content_store[file_id]

def update_block_filepath(block, chapter):
    block["file_path"] = f"{chapter}_{block['id']}.txt"
    return block

def generate_unique_block_id(chapter_blocks):
    existing_ids = {block["id"] for block in chapter_blocks}
    i = len(chapter_blocks)
    while True:
        new_id = f"block_{i}_{int(time.time())}"
        if new_id not in existing_ids:
            return new_id
        i += 1

@st.fragment
def render_block(idx, block, service, current_chapter):
    global block_content_store
    block_content = download_file_wrapper(block["file_id"], service) if "file_id" in block else ""
    
    if block_content == "HTTP 404":
        if block["file_id"] in block_content_store:
            del block_content_store[block["file_id"]]
        try:
            service.files().delete(fileId=block["file_id"]).execute()
        except HttpError:
            pass
        st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
        save_project_manifest(service)
        return None

    unique_key = f"textblock_{block['id']}_{block.get('file_id', idx)}"
    new_content = st.text_area(f"Block {idx + 1} ({current_chapter})", value=block_content, key=unique_key)
    
    if new_content != block_content and "file_id" in block:
        media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
        service.files().update(fileId=block["file_id"], media_body=media).execute()
        block_content_store[block["file_id"]] = new_content
        logging.info(f"Updated file: {block['file_id']}")
    return new_content

def body(service):
    st.write("#### == DB Organizer ==")

    if "project" not in st.session_state:
        st.session_state.project = {
            "folder_id": None,
            "manifest": {"chapters": {"Staging Area": []}},
            "current_chapter": "Staging Area"
        }

    current_chapter = st.session_state.project["current_chapter"]
    blocks = sorted(st.session_state.project["manifest"]["chapters"][current_chapter], key=lambda x: x["order"])

    for idx, block in enumerate(blocks):
        new_content = render_block(idx, block, service, current_chapter)
        if new_content is None:
            st.rerun()
            break

        with st.form(key=f"actions_{block['id']}_{idx}", clear_on_submit=True):
            col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 2, 1])  # Added col6 for move button
            with col1:
                move_up = st.form_submit_button(f"⬆ {idx}", disabled=idx == 0)
            with col2:
                move_down = st.form_submit_button(f"⬇ {idx}", disabled=idx == len(blocks) - 1)
            with col3:
                delete = st.form_submit_button(f"🗑 {idx}")
            with col4:
                merge = st.form_submit_button(f"🔗 {idx}", disabled=idx == len(blocks) - 1)
            with col5:
                chapters = list(st.session_state.project["manifest"]["chapters"].keys())
                target_chapter = st.selectbox(f"Move {idx}", [""] + chapters, key=f"move_select_{block['id']}", label_visibility="collapsed")
            with col6:
                move_to_chapter = st.form_submit_button("Move")

            if move_up:
                blocks[idx]["order"], blocks[idx - 1]["order"] = blocks[idx - 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                save_project_manifest(service)
                st.rerun()
                break
            elif move_down:
                blocks[idx]["order"], blocks[idx + 1]["order"] = blocks[idx + 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                save_project_manifest(service)
                st.rerun()
                break
            elif delete:
                if "file_id" in block and block["file_id"] in block_content_store:
                    del block_content_store[block["file_id"]]
                if "file_id" in block:
                    service.files().delete(fileId=block["file_id"]).execute()
                st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                save_project_manifest(service)
                st.rerun()
                break
            elif merge:
                try:
                    next_block = blocks[idx + 1]
                    next_content = download_file_wrapper(next_block["file_id"], service) if "file_id" in next_block else ""
                    if next_content == "HTTP 404":
                        logging.info(f"Removing missing block: {next_block['file_id']}")
                        st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                        save_project_manifest(service)
                        st.rerun()
                        break
                    elif "file_id" in block:
                        merged_content = new_content + "\n" + next_content
                        media = MediaIoBaseUpload(BytesIO(merged_content.encode("utf-8")), mimetype="text/plain")
                        service.files().update(fileId=block["file_id"], media_body=media).execute()
                        block_content_store[block["file_id"]] = merged_content
                        logging.info(f"Merged into file: {block['file_id']}")
                        if "file_id" in next_block:
                            if next_block["file_id"] in block_content_store:
                                del block_content_store[next_block["file_id"]]
                            service.files().delete(fileId=next_block["file_id"]).execute()
                            logging.info(f"Deleted file: {next_block['file_id']}")
                        st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                        save_project_manifest(service)
                        st.rerun()
                        break
                    else:
                        logging.error(f"Cannot merge: No file_id for block {block['id']}")
                        break
                except HttpError as e:
                    logging.error(f"Error during merge: {e}")
                    if e.resp.status == 404 and "file_id" in next_block:
                        st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                        save_project_manifest(service)
                        st.rerun()
                        break
            elif move_to_chapter and target_chapter and target_chapter != current_chapter:
                block_to_move = st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                block_to_move["order"] = len(st.session_state.project["manifest"]["chapters"][target_chapter])
                block_to_move = update_block_filepath(block_to_move, target_chapter)
                if "file_id" in block_to_move:
                    media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
                    service.files().update(fileId=block_to_move["file_id"], media_body=media, body={"name": block_to_move["file_path"]}).execute()
                    block_content_store[block_to_move["file_id"]] = new_content
                st.session_state.project["manifest"]["chapters"][target_chapter].append(block_to_move)
                save_project_manifest(service)
                st.rerun()
                break

    if st.button("Add Empty Block"):
        block_id = generate_unique_block_id(st.session_state.project["manifest"]["chapters"][current_chapter])
        block_file_name = f"{current_chapter}_{block_id}.txt"
        new_file = upload_file(service, "", block_file_name, st.session_state.project["folder_id"])
        st.session_state.project["manifest"]["chapters"][current_chapter].append({
            "id": block_id,
            "file_path": new_file["name"],
            "file_id": new_file["id"],
            "order": len(st.session_state.project["manifest"]["chapters"][current_chapter])
        })
        block_content_store[new_file["id"]] = ""
        save_project_manifest(service)
        st.rerun()
