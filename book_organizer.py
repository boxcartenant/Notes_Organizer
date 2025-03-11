import streamlit as st
from Google_Drive_Management.manage_google_files import browse_google_drive, download_file, upload_file, build, list_drive_files, save_project_manifest, clear_block_cache
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import logging
import time
from io import BytesIO
                      

logging.basicConfig(level=logging.INFO)

def download_file_wrapper(file_id, service, from_session_state=True):
    if "block_cache" not in st.session_state:
        st.session_state.block_cache = {}
    # Fetch from Drive if changed or not in cache
    if not from_session_state or file_id not in st.session_state.block_cache:
                                                    
        try:
            content = download_file(file_id, service)
            st.session_state.block_cache[file_id] = content
            return content
        except HttpError as error:
            if error.resp.status == 404:
                logging.warning(f"File not found: {file_id}")
                return "HTTP 404"
            raise
    return st.session_state.block_cache[file_id]

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

def body(service):
    st.write("#### == DB Organizer ==")

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
    if not isinstance(st.session_state.changed_blocks, set):
        st.session_state.changed_blocks = set(st.session_state.changed_blocks)

    current_chapter = st.session_state.project["current_chapter"]
    blocks = sorted(st.session_state.project["manifest"]["chapters"][current_chapter], key=lambda x: x["order"])

    for idx, block in enumerate(blocks):
        # Fetch content, forcing Drive update if changed
        from_session_state = "file_id" in block and block["file_id"] not in st.session_state.changed_blocks
                                      
        block_content = download_file_wrapper(block["file_id"], service, from_session_state) if "file_id" in block else ""
        
        if block_content == "HTTP 404":
            if block["file_id"] in st.session_state.block_cache:
                del st.session_state.block_cache[block["file_id"]]
            try:
                service.files().delete(fileId=block["file_id"]).execute()
            except HttpError:
                pass
            st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
            save_project_manifest(service)
            #st.rerun()
            return

                                                                              
        unique_key = f"textblock_{block['id']}_{block.get('file_id', idx)}"
        new_content = st.text_area(f"Block {idx + 1} ({current_chapter})", value=block_content, key=unique_key)

        if new_content != block_content:
            if "file_id" in block:
                media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
                service.files().update(fileId=block["file_id"], media_body=media).execute()
                st.session_state.block_cache[block["file_id"]] = new_content
                st.session_state.changed_blocks.add(block["file_id"])
                logging.info(f"Updated file: {block['file_id']}")
            else:
                block_file_name = f"{current_chapter}_{block['id']}.txt"
                new_file = upload_file(service, new_content, block_file_name, st.session_state.project["folder_id"])
                block["file_path"] = new_file["name"]
                block["file_id"] = new_file["id"]
                st.session_state.block_cache[new_file["id"]] = new_content
                st.session_state.changed_blocks.add(new_file["id"])
            save_project_manifest(service)
            #st.rerun()
            return

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button(f"⬆ {idx}", key=f"move_up_{block['id']}") and idx > 0:
                blocks[idx]["order"], blocks[idx - 1]["order"] = blocks[idx - 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                save_project_manifest(service)
                #st.rerun()
                return
        with col2:
            if st.button(f"⬇ {idx}", key=f"move_down_{block['id']}") and idx < len(blocks) - 1:
                blocks[idx]["order"], blocks[idx + 1]["order"] = blocks[idx + 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                save_project_manifest(service)
                #st.rerun()
                return
        with col3:
            if st.button(f"🗑 {idx}", key=f"delete_{block['id']}"):
                if "file_id" in block and block["file_id"] in st.session_state.block_cache:
                    del st.session_state.block_cache[block["file_id"]]
                if "file_id" in block:
                    service.files().delete(fileId=block["file_id"]).execute()
                st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                save_project_manifest(service)
                #st.rerun()
                return
        with col4:
            if st.button(f"🔗 {idx}", key=f"merge_down_{block['id']}") and idx < len(blocks) - 1:
                try:
                    next_block = blocks[idx + 1]
                    next_content = download_file_wrapper(next_block["file_id"], service) if "file_id" in next_block else ""
                    if next_content == "HTTP 404":
                        st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                        save_project_manifest(service)
                        #st.rerun()
                        return
                    merged_content = block_content + "\n\n" + next_content
                    
                    if "file_id" in block:
                        media = MediaIoBaseUpload(BytesIO(merged_content.encode("utf-8")), mimetype="text/plain")
                        service.files().update(fileId=block["file_id"], media_body=media).execute()
                        st.session_state.block_cache[block["file_id"]] = merged_content
                        st.session_state.changed_blocks.add(block["file_id"])
                        logging.info(f"Updated file: {block['file_id']}")
                    
                    if "file_id" in next_block:
                        if next_block["file_id"] in st.session_state.block_cache:
                            del st.session_state.block_cache[next_block["file_id"]]
                        service.files().delete(fileId=next_block["file_id"]).execute()
                        logging.info(f"Deleted file: {next_block['file_id']}")
                    
                    st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                    clear_block_cache()
                    save_project_manifest(service)
                    logging.info(f"Stuff is disappearing!")
                except HttpError as e:
                    logging.error(f"Error during merge: {e}")
                    if e.resp.status == 404 and "file_id" in next_block:
                        st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx + 1)
                        save_project_manifest(service)
                        #st.rerun()
                finally:
                    st.rerun()
                    return
        with col5:
            chapters = list(st.session_state.project["manifest"]["chapters"].keys())
            target_chapter = st.selectbox(f"Move {idx}", [""] + chapters, key=f"move_{block['id']}", label_visibility="collapsed")
            if target_chapter and target_chapter != current_chapter:
                block_to_move = st.session_state.project["manifest"]["chapters"][current_chapter].pop(idx)
                block_to_move["order"] = len(st.session_state.project["manifest"]["chapters"][target_chapter])
                block_to_move = update_block_filepath(block_to_move, target_chapter)
                if "file_id" in block_to_move:
                    media = MediaIoBaseUpload(BytesIO(block_content.encode("utf-8")), mimetype="text/plain")
                    service.files().update(fileId=block_to_move["file_id"], media_body=media, body={"name": block_to_move["file_path"]}).execute()
                    st.session_state.block_cache[block_to_move["file_id"]] = block_content
                st.session_state.project["manifest"]["chapters"][target_chapter].append(block_to_move)
                save_project_manifest(service)
                #st.rerun()
                return

    if st.button("Add Empty Block"):
        block_id = generate_unique_block_id(st.session_state.project["manifest"]["chapters"][current_chapter])
        block_file_name = f"{block_id}.txt"
        new_file = upload_file(service, "", block_file_name, st.session_state.project["folder_id"])
        st.session_state.project["manifest"]["chapters"][current_chapter].append({
            "id": block_id,
            "file_path": new_file["name"],
            "file_id": new_file["id"],
            "order": len(st.session_state.project["manifest"]["chapters"][current_chapter])
        })
        st.session_state.block_cache[new_file["id"]] = ""
        save_project_manifest(service)
        #st.rerun()