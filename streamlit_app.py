import streamlit as st
import book_organizer
import manage_google_files
import bibledb_to_book
import bibledb_editor

#Layout testing

def main():
    # Set up session state for mode selection
    if 'mode' not in st.session_state:
        st.session_state.mode = 1

    # Sidebar: Mode buttons
    with st.sidebar:
        st.title("Navigation")
        if st.button("Book Organizer"):
            st.session_state.mode = 1
        if st.button("DB to Book"):
            st.session_state.mode = 2
        if st.button("DB Editor"):
            st.session_state.mode = 3
        st.markdown("---")

    #Everything else
    match st.session_state.mode:
        case 1: #book Organizer
            book_organizer.sidebar()
            book_organizer.body()
        case 2: #bibledb to book
            bibledb_to_book.sidebar()
            bibledb_to_book.body()
        case 3: #bibledb_editor
            bibledb_editor.sidebar()
            bibledb_editor.body()
            
if __name__ == "__main__":
    main()
