import streamlit as st
from manage_google_files import *
import bibledb_lib

# === Bible DB Editor === 
# This function will mimic the behavior of the desktop app I made before.
# I'm gonna show all the books and chapters in the sidebar, and the verses in the body,
# with some selection capabilities.

def sidebar():
    with st.sidebar:
        st.subheader("DB Editor Controls")
        if authenticate_user():
            if "bible json" not in st.session_state:
                st.write("Select a bible.")
                checkthefile = browse_google_drive()
                print(checkthefile)
                if checkthefile and checkthefile.endswith(".json"):
                    st.session_state["bible json"] = checkthefile
                elif checkthefile:
                    st.session_state["gdrive_files"].pop(checkthefile)
                    st.write("bad filetype")
                else:
                    st.write("Waiting on selection of a bible.json")

            elif "bdb file" not in st.session_state:
                st.write("Select a bible db.")
                checkthefile = browse_google_drive()
                if checkthefile and checkthefile.endswith(".bdb"):
                    st.session_state["bible bdb"] = checkthefile
                elif checkthefile:
                    st.session_state["gdrive_files"].pop(checkthefile)
                    st.write("bad filetype")
                else:
                    st.write("Waiting on selection of a database.bdb")
            else:
                st.write("json and bdb loaded!", st.session_state["bible json"], st.session_state["bible bdb"])

                st.markdown("---")

                for i in range(1, 4):
                    if st.button(f"Toggle List {i}"):
                        st.session_state[f"list_{i}_visible"] = not st.session_state.get(f"list_{i}_visible", False)
                    if st.session_state.get(f"list_{i}_visible", False):
                        for j in range(3):
                            st.button(f"Sub-button {i}.{j}")

def body():
    st.title("Mode 3")

    if 'selected_buttons' not in st.session_state:
        st.session_state.selected_buttons = []

    button_labels = [f"Button {i + 1}" for i in range(10)]
    for idx, label in enumerate(button_labels):
        button_state = st.session_state.selected_buttons
        if st.button(label, key=f"button_{idx}"):
            if idx in button_state:
                st.session_state.selected_buttons = []
            else:
                st.session_state.selected_buttons = [idx]

    st.text_area("Notes:", key="notes")
    if st.button("Commit Notes"):
        st.write(f"Notes committed: {st.session_state.notes}")

    st.text_input("Tags:", key="tags")
    if st.button("Commit Tags"):
        st.write(f"Tags committed: {st.session_state.tags}")
