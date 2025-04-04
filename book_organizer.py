import streamlit as st
from Google_Drive_Management.manage_google_files import browse_google_drive, download_file, upload_file, build, list_drive_files, save_project_manifest, clear_block_cache, generate_unique_block_id, block_content_store
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import logging
import time
from io import BytesIO

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO)

# Existing helper functions remain unchanged
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
    block["file_path"] = f"{block['id']}.txt"
    return block

def clear_block_content_store():
    global block_content_store
    block_content_store = {}

def decrement_orders_after(blocks, start_idx):
    if start_idx < len(blocks):
        for i in range(start_idx, len(blocks)):
            if blocks[i]["order"] > 0:
                blocks[i]["order"] -= 1

def remove_block_from_manifest(this_chapter, this_chapter_blocks, idx):
    manifest_blocks = st.session_state.project["manifest"]["chapters"][this_chapter]
    block_to_remove = next(b for b in manifest_blocks if b["order"] == this_chapter_blocks[idx]["order"])
    manifest_blocks.remove(block_to_remove)
    decrement_orders_after(this_chapter_blocks, idx)
    this_chapter_blocks.pop(idx)
    st.session_state.project["manifest"]["chapters"][this_chapter] = this_chapter_blocks

@st.fragment
def render_block(idx, block, service, current_chapter, mobile_friendly=False):
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
    height = st.session_state.get(f"height_{unique_key}", 300) if mobile_friendly else 300
    new_content = st.text_area(f"Block {idx + 1} ({current_chapter})", value=block_content, key=unique_key, height=height)
    
    if mobile_friendly:
        current_height = st.session_state[f"height_{unique_key}"]
        height_value = st.slider(f"Adjust height for Block {idx + 1}", min_value=100, max_value=600, value=height, key=f"slider_{unique_key}")
        if current_height != height_value:
            st.session_state[f"height_{unique_key}"] = height_value
            st.rerun()
            return None
    
    if new_content != block_content and "file_id" in block:
        media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
        service.files().update(fileId=block["file_id"], media_body=media).execute()
        block_content_store[block["file_id"]] = new_content
        logging.info(f"Updated file: {block['file_path']}")
        st.rerun()
        return None
    return new_content

def body(service):
    if "mobile_friendly_view" not in st.session_state:
        st.session_state.mobile_friendly_view = False
    
    st.session_state.mobile_friendly_view = st.checkbox("Mobile-Friendly View", value=st.session_state.mobile_friendly_view)

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
        new_content = render_block(idx, block, service, current_chapter, mobile_friendly=st.session_state.mobile_friendly_view)
        if new_content is None:
            st.rerun()
            break

        if st.session_state.mobile_friendly_view:
            actions = ["Select Action", "Move Up", "Move Down", "Delete", "Merge"]
            action = st.selectbox(f"Action for Block {idx + 1}", actions, key=f"action_{block['id']}_{idx}")
            
            chapters = list(st.session_state.project["manifest"]["chapters"].keys())
            target_chapter = st.selectbox(f"Move Block {idx + 1} to Chapter", ["Select a Chapter"] + chapters, key=f"move_select_{block['id']}_{idx}")

            if action != "Select Action":
                if action == "Move Up" and idx > 0:
                    blocks[idx]["order"], blocks[idx - 1]["order"] = blocks[idx - 1]["order"], blocks[idx]["order"]
                    st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                    save_project_manifest(service)
                    st.rerun()
                    break
                elif action == "Move Down" and idx < len(blocks) - 1:
                    blocks[idx]["order"], blocks[idx + 1]["order"] = blocks[idx + 1]["order"], blocks[idx]["order"]
                    st.session_state.project["manifest"]["chapters"][current_chapter] = blocks
                    save_project_manifest(service)
                    st.rerun()
                    break
                elif action == "Delete":
                    if "file_id" in block and block["file_id"] in block_content_store:
                        del block_content_store[block["file_id"]]
                    if "file_id" in block:
                        service.files().delete(fileId=block["file_id"]).execute()
                    remove_block_from_manifest(current_chapter, blocks, idx)
                    save_project_manifest(service)
                    st.rerun()
                    break
                elif action == "Merge" and idx < len(blocks) - 1:
                    next_block = blocks[idx + 1]
                    next_content = download_file_wrapper(next_block["file_id"], service) if "file_id" in next_block else ""
                    if next_content == "HTTP 404":
                        logging.info(f"Removing missing block: {next_block['file_id']}")
                        remove_block_from_manifest(current_chapter, blocks, idx + 1)
                        save_project_manifest(service)
                        st.rerun()
                        break
                    elif "file_id" in block:
                        merged_content = new_content + "\n\n" + next_content
                        media = MediaIoBaseUpload(BytesIO(merged_content.encode("utf-8")), mimetype="text/plain")
                        service.files().update(fileId=block["file_id"], media_body=media).execute()
                        block_content_store[block["file_id"]] = merged_content
                        if "file_id" in next_block:
                            if next_block["file_id"] in block_content_store:
                                del block_content_store[next_block["file_id"]]
                            service.files().delete(fileId=next_block["file_id"]).execute()
                        remove_block_from_manifest(current_chapter, blocks, idx + 1)
                        save_project_manifest(service)
                        st.rerun()
                        break

            if target_chapter != "Select a Chapter" and target_chapter != current_chapter:
                block["order"] = len(st.session_state.project["manifest"]["chapters"][target_chapter]) + 1
                st.session_state.project["manifest"]["chapters"][target_chapter].append(block)
                remove_block_from_manifest(current_chapter, blocks, idx)
                save_project_manifest(service)
                st.rerun()
                break

        else:
            form_key = f"actions_{block['id']}_{idx}"
            with st.form(key=form_key, clear_on_submit=True):
                col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 2, 1])
                with col1:
                    move_up = st.form_submit_button(f"⬆ {idx}", disabled=idx == 0, help="Swap this block with the block above it")
                with col2:
                    move_down = st.form_submit_button(f"⬇ {idx}", disabled=idx == len(blocks) - 1, help="Swap this block with the block below it")
                with col3:
                    delete = st.form_submit_button(f"🗑 {idx}", help="Delete this block")
                with col4:
                    merge = st.form_submit_button(f"🔗 {idx}", disabled=idx == len(blocks) - 1, help="Merge this block with the block below it")
                with col5:
                    chapters = list(st.session_state.project["manifest"]["chapters"].keys())
                    target_chapter = st.selectbox(f"Move {idx}", ["Select a Chapter"] + chapters, key=f"move_select_{block['id']}", label_visibility="collapsed")
                with col6:
                    move_to_chapter = st.form_submit_button("Move", help="Move this block to the selected chapter")
                
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
                            remove_block_from_manifest(current_chapter, blocks, idx + 1)
                            save_project_manifest(service)
                            st.rerun()
                            break
                        elif "file_id" in block:
                            merged_content = new_content + "\n\n" + next_content
                            media = MediaIoBaseUpload(BytesIO(merged_content.encode("utf-8")), mimetype="text/plain")
                            service.files().update(fileId=block["file_id"], media_body=media).execute()
                            block_content_store[block["file_id"]] = merged_content
                            if "file_id" in next_block:
                                if next_block["file_id"] in block_content_store:
                                    del block_content_store[next_block["file_id"]]
                                service.files().delete(fileId=next_block["file_id"]).execute()
                            remove_block_from_manifest(current_chapter, blocks, idx + 1)
                            save_project_manifest(service)
                            st.rerun()
                            break
                        else:
                            logging.error(f"Cannot merge: No file_id for block {block['id']}")
                            break
                    except HttpError as e:
                        logging.error(f"Error during merge: {e}")
                        if e.resp.status == 404 and "file_id" in next_block:
                            remove_block_from_manifest(current_chapter, blocks, idx + 1)
                            save_project_manifest(service)
                            st.rerun()
                            break
                elif move_to_chapter and target_chapter and target_chapter != current_chapter:
                    if "file_id" in block:
                        #move the file on google drive
                        #the index is +1'd becauase remove_block_from_manifes decrements it. 
                        #....... I'll fix that later.
                        block["order"] = len(st.session_state.project["manifest"]["chapters"][target_chapter]) +1
    
                        
                        #are these lines necessary?
                        #block = update_block_filepath(block, target_chapter)
                        #media = MediaIoBaseUpload(BytesIO(new_content.encode("utf-8")), mimetype="text/plain")
    
                        #add the block back into the new chapter manifest
                        st.session_state.project["manifest"]["chapters"][target_chapter].append(block)
                        
                        #remove the block from the old chapter manifest
                        remove_block_from_manifest(current_chapter, blocks, idx)
                        save_project_manifest(service)
                        st.rerun()
                        break

    if st.session_state.project["folder_id"]:
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
            block_content_store[new_file["id"]] = ""
            save_project_manifest(service)
            st.rerun()
    else:
        st.success("You're logged in!")
        st.write("\
But you haven't selected your project folder yet. If this is your first time here, follow these steps to get started:\n\
1. Create a new project or select an existing project that you made before.\n\
2. Upload any .txt files that you might want to use in the project\n\
3. Start making blocks and chapters. Use the file-browser to select any files you want to bring into a block in the current chapter.\n\
\n\
Then you can create and rearrange text blocks using the buttons in the main body, or by opening .txt files from your google drive in 'Folders and files'.\n\
Keep in mind: this app can only access files that you upload or create using this app.\n\n\
To make a new chapter, or change what chapter you're looking at, use 'Manage Chapters'.\n\
\n\
DISCLAIMER: I make no promises about the usefulness of this tool. It might have bugs. It might delete your data. It might cause you other kinds of problems. Who knows? Use at your own risk.")