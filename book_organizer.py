import streamlit as st
import manage_google_files

# === Book Organizer ===
# These functions are for grabbing and rearranging text in my many notes,
#  and for saving their new arrangement in some kind of book file that I 
#  haven't structured yet.
# 
# So far, you can add, delete, and rearrange text blocks.

def sidebar():
    with st.sidebar:
        st.subheader("DB Organizer")
        st.button("Load Data")
        st.button("Commit Changes")

def body():
    st.title("DB Organizer")

    if 'textblocks' not in st.session_state:
        st.session_state.textblocks = []

    for idx, _ in enumerate(st.session_state.textblocks):
        # Display the text area and bind it to session state
        st.session_state.textblocks[idx] = st.text_area(
            f"Textblock {idx + 1}", 
            value=st.session_state.textblocks[idx], 
            key=f"textblock_{idx}"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"Move Up {idx}", key=f"move_up_{idx}") and idx > 0:
                st.session_state.textblocks[idx - 1], st.session_state.textblocks[idx] = (
                    st.session_state.textblocks[idx],
                    st.session_state.textblocks[idx - 1],
                )
                st.rerun()
        with col2:
            if st.button(f"Move Down {idx}", key=f"move_down_{idx}") and idx < len(st.session_state.textblocks) - 1:
                st.session_state.textblocks[idx + 1], st.session_state.textblocks[idx] = (
                    st.session_state.textblocks[idx],
                    st.session_state.textblocks[idx + 1],
                )
                st.rerun()
        with col3:
            if st.button(f"Delete {idx}", key=f"delete_{idx}"):
                st.session_state.textblocks.pop(idx)
                st.rerun()

    if st.button("Add Textblock"):
        st.session_state.textblocks.append("")
        st.rerun()