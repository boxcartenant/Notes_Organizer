import streamlit as st
import manage_google_files

# === Bible DB to Book ===
# This function will be for taking notes out of the Bible DB and adding them to the book.
# We'll show all the passages with comments in the navigation
# and we'll have buttons to add them to the body somewhere...
# and probably the body should seamlessly integrate with the book_organizer body?
# honestly I'm not sure how I'm gonna swing this yet.
# .... tbh I don't remember why I made this mode the way it is....
# ......... I gotta go read my old notes............


def sidebar():
    with st.sidebar:
        st.subheader("Mode 2 Controls")
        for i in range(5):
            st.button(f"Mode 2 Button {i}")

def body():
    st.title("Mode 2")

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