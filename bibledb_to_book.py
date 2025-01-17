import streamlit as st
import manage_google_files

# === Bible DB to Book ===
# This function will be for taking notes out of the Bible DB and adding them to the book.

def sidebar():
    with st.sidebar:
        st.subheader("Mode 2 Controls")
            for i in range(1, 4):
                if st.button(f"Toggle List {i}"):
                    st.session_state[f"list_{i}_visible"] = not st.session_state.get(f"list_{i}_visible", False)
                if st.session_state.get(f"list_{i}_visible", False):
                    for j in range(3):
                        st.button(f"Sub-button {i}.{j}")

def body():
    st.title("Mode 2")

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