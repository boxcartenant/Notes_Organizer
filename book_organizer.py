import streamlit as st
from Google_Drive_Management import save_load_projects
from Google_Drive_Management.manage_google_files import browse_google_drive, download_file, upload_file, build
from google.oauth2.credentials import Credentials

# === Book Organizer ===
# These functions are for grabbing and rearranging text in my many notes,
#  and for saving their new arrangement in some kind of book file that I 
#  haven't structured yet.
# 
# So far, you can add, delete, and rearrange text blocks.

def sidebar():
    with st.sidebar:
        save_load_projects.list_projects()
        
        if "current_project" in st.session_state:
            st.write(f"**Current Project:** `{st.session_state['current_project']}`")
        
        if st.button("💾 Save"):
            if "current_project" in st.session_state:
                save_load_projects.save_project(st.session_state["current_project"])
            else:
                st.warning("No project loaded. Use 'Save As' to create a new one.")

        if st.button("💾 Save As"):
            new_project_name = st.text_input("Enter new project name:")
            if new_project_name:
                st.session_state["current_project"] = new_project_name
                save_load_projects.save_project(new_project_name)



def body(service):
    st.title("DB Organizer")

    # Ensure project is initialized
    if "project" not in st.session_state:
        st.session_state.project = {"folder_id": None, "manifest": {"blocks": []}}

    # Display blocks from manifest
    blocks = sorted(st.session_state.project["manifest"]["blocks"], key=lambda x: x["order"])
    for idx, block in enumerate(blocks):
        # Fetch block content on demand
        block_content = download_file(next(f["id"] for f in list_drive_files(service, st.session_state.project["folder_id"]) if f["name"] == block["file_path"]), service)
        new_content = st.text_area(f"Block {idx + 1}", value=block_content, key=f"textblock_{block['id']}")
        
        # Update block content if changed
        if new_content != block_content:
            upload_file(service, new_content, block["file_path"], st.session_state.project["folder_id"])

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"⬆ {idx}", key=f"move_up_{block['id']}") and idx > 0:
                blocks[idx]["order"], blocks[idx - 1]["order"] = blocks[idx - 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["blocks"] = blocks
                st.rerun()
        with col2:
            if st.button(f"⬇ {idx}", key=f"move_down_{block['id']}") and idx < len(blocks) - 1:
                blocks[idx]["order"], blocks[idx + 1]["order"] = blocks[idx + 1]["order"], blocks[idx]["order"]
                st.session_state.project["manifest"]["blocks"] = blocks
                st.rerun()
        with col3:
            if st.button(f"🗑 {idx}", key=f"delete_{block['id']}"):
                st.session_state.project["manifest"]["blocks"].pop(idx)
                # Optionally delete the file from Google Drive here
                st.rerun()

    if st.button("Add Empty Block"):
        block_id = f"block_{len(st.session_state.project['manifest']['blocks'])}"
        block_file_name = f"{block_id}.txt"
        upload_file(service, "", block_file_name, st.session_state.project["folder_id"])
        st.session_state.project["manifest"]["blocks"].append({
            "id": block_id,
            "file_path": block_file_name,
            "order": len(st.session_state.project["manifest"]["blocks"])
        })
        st.rerun()

def main():
    if "credentials" in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state["credentials"])
        service = build('drive', 'v3', credentials=creds)
        browse_google_drive(service)
        body(service)
    else:
        st.error("Please authenticate first.")

if __name__ == "__main__":
    main()