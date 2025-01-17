import streamlit as st
import manage_google_files

def sidebar():
    st.subheader("Mode 3 Controls")
    for i in range(5):
        st.button(f"Mode 3 Button {i}")

def body():
    st.title("Mode 3")

    if 'selected_button' not in st.session_state:
        st.session_state.selected_button = None

    button_labels = [f"Button {i + 1}" for i in range(10)]
    for idx, label in enumerate(button_labels):
        if st.button(label, key=f"mode3_button_{idx}"):
            st.session_state.selected_button = idx

        if st.session_state.selected_button == idx:
            st.text_area("Details:")
            st.text_input("Tags:")
            st.button("Commit")