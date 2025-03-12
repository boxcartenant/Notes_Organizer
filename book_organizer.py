import streamlit as st
from Google_Drive_Management.manage_google_files import browse_google_drive, download_file, upload_file, build, list_drive_files, save_project_manifest, clear_block_cache
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import logging
import time
from io import BytesIO

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
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

def clear_block_content_store():
    global block_content_store
    block_content_store = {}

def decrement_orders_after(blocks, start_idx):
    """Decrement the 'order' value for all blocks after start_idx."""
    for i in range(start_idx, len(blocks)):
        blocks[i]["order"] -= 1

def remove_block_from_manifest(this_chapter, this_chapter_blocks, idx):
    manifest_blocks = st.session_state.project["manifest"]["chapters"][this_chapter]
    block_to_remove = next(b for b in manifest_blocks if b["order"] == this_chapter_blocks[idx]["order"])
    manifest_blocks.remove(block_to_remove)
    decrement_orders_after(this_chapter_blocks, idx)
    this_chapter_blocks.pop(idx)
    st.session_state.project["manifest"]["chapters"][this_chapter] = this_chapter_blocks

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
        logging.info(f"Updated file: {block['file_path']}")
    return new_content

def body(service):
    current_chapter = st.session_state.project["current_chapter"]
    st.write(f"#### == {current_chapter} ==")

    if "project" not in st.session_state:
        st.session_state.project = {
            "folder_id": None,
            "manifest": {"chapters": {"Staging Area": []}},
            "current_chapter": "Staging Area"
        }

    
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
                remove_block_from_manifest(current_chapter, blocks, idx)
                save_project_manifest(service)
                st.rerun()
                break
            elif merge:
                try:
                    next_block = blocks[idx + 1]
                    next_content = download_file_wrapper(next_block["file_id"], service) if "file_id" in next_block else ""
                    if next_content == "HTTP 404":
                        logging.info(f"Removing missing block: {next_block['file_id']}")
                        remove_block_from_manifest(current_chapter, blocks, idx)
                        save_project_manifest(service)
                        st.rerun()
                        break
                    elif "file_id" in block:
                        merged_content = new_content + "\n" + next_content
                        media = MediaIoBaseUpload(BytesIO(merged_content.encode("utf-8")), mimetype="text/plain")
                        service.files().update(fileId=block["file_id"], media_body=media).execute()
                        block_content_store[block["file_id"]] = merged_content
                        logging.info(f"Merged into file: {block['file_path']}")
                        if "file_id" in next_block:
                            if next_block["file_id"] in block_content_store:
                                del block_content_store[next_block["file_id"]]
                            service.files().delete(fileId=next_block["file_id"]).execute()
                            logging.info(f"Deleted file: {next_block['file_path']}")
                        remove_block_from_manifest(current_chapter, blocks, idx)
                        save_project_manifest(service)
                        st.rerun()
                        break
                    else:
                        logging.error(f"Cannot merge: No file_id for block {block['id']}")
                        break
                except HttpError as e:
                    logging.error(f"Error during merge: {e}")
                    if e.resp.status == 404 and "file_id" in next_block:
                        remove_block_from_manifest(current_chapter, blocks, idx)
                        save_project_manifest(service)
                        st.rerun()
                        break
            elif move_to_chapter and target_chapter and target_chapter != current_chapter:
                if "file_id" in block:
                    #capture this and the next block
                    this_block_id = block["file_id"]
                    next_block_id = blocks[idx+1]["file_id"]
                    this_block_order = block["order"]
                    this_block_contents = block_content_store[this_block_id]
                    next_block_contents = block_content_store[next_block_id]
                    logging.info(f"block contents (this, next): ({this_block_contents},{next_block_contents})")

                    
                    

                    #move the file on google drive
                    logging.info(f"moving file: {block['file_path']} with content {new_content}")
                    block["order"] = len(st.session_state.project["manifest"]["chapters"][target_chapter])
                    
                    block = update_block_filepath(block, target_chapter)
                    media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
                    service.files().update(fileId=this_block_id, media_body=media, body={"name": block["file_path"]}).execute()


                    #update the block content store
                    #block_content_store[this_block_id] = this_block_contents

                    #add the block back into the new chapter manifest
                    st.session_state.project["manifest"]["chapters"][target_chapter].append(block)
                    #remove the block from the old chapter manifest
                    # Find and remove by order, not idx
                    remove_block_from_manifest(current_chapter, blocks, idx)

                    logging.info(f"Moved file: {block['file_path']} with content {new_content}")
                    logging.info(f"block contents local (this, next): ({this_block_contents},{next_block_contents})")
                    logging.info(f"block contents from store: ({block_content_store[this_block_id]},{block_content_store[next_block_id]})")

                    #update block orders and save the manifest
                    save_project_manifest(service)
                    st.rerun()
                    break
    if st.session_state.project["folder_id"]:
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
    else:
        st.success("You're logged in!")
        st.write("But you haven't selected your project folder yet. If this is your first time here:\n- Create a new folder for your project by using the 'Create New Folder' dialog.")
        st.write("If you've already got a project folder made for this tool:\n- Set that folder as the project directory using the 'set' button in 'Folders and Files'.")
        st.write("Now you can create and rearrange text blocks using the buttons in the main body, or by opening .txt files from your google drive in 'Folders and files'.")
        st.write("To make a new chapter, or change what chapter you're looking at, use 'Manage Chapters'.")
        st.write("Don't worry: this program will only edit files which are in the project directory. If you add a file from somewhere else in your google drive, it will first copy that file to the project.")
