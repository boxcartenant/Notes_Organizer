import streamlit as st

#Layout testing

def main():
    # Set up session state for mode selection
    if 'mode' not in st.session_state:
        st.session_state.mode = 1

    # Sidebar: Mode buttons
    with st.sidebar:
        st.title("Modes")
        if st.button("Mode 1: DB Organizer"):
            st.session_state.mode = 1
        if st.button("Mode 2"):
            st.session_state.mode = 2
        if st.button("Mode 3"):
            st.session_state.mode = 3

        st.markdown("---")

        # Additional sidebar controls per mode
        if st.session_state.mode == 1:
            st.subheader("DB Organizer")
            st.button("Load Data")
            st.button("Commit Changes")

        elif st.session_state.mode == 2:
            st.subheader("Mode 2 Controls")
            for i in range(1, 4):
                if st.button(f"Toggle List {i}"):
                    st.session_state[f"list_{i}_visible"] = not st.session_state.get(f"list_{i}_visible", False)
                if st.session_state.get(f"list_{i}_visible", False):
                    for j in range(3):
                        st.button(f"Sub-button {i}.{j}")

        elif st.session_state.mode == 3:
            st.subheader("Mode 3 Controls")
            for i in range(5):
                st.button(f"Mode 3 Button {i}")

    # Main body content
    if st.session_state.mode == 1:
        mode_1_body()
    elif st.session_state.mode == 2:
        mode_2_body()
    elif st.session_state.mode == 3:
        mode_3_body()

def mode_1_body():
    st.title("DB Organizer")

    if 'textblocks' not in st.session_state:
        st.session_state.textblocks = []

    for idx, text in enumerate(st.session_state.textblocks):
        st.text_area(f"Textblock {idx + 1}", text, key=f"textblock_{idx}")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Move Up", key=f"move_up_{idx}") and idx > 0:
                st.session_state.textblocks[idx - 1], st.session_state.textblocks[idx] = (
                    st.session_state.textblocks[idx],
                    st.session_state.textblocks[idx - 1],
                )
        with col2:
            if st.button("Move Down", key=f"move_down_{idx}") and idx < len(st.session_state.textblocks) - 1:
                st.session_state.textblocks[idx + 1], st.session_state.textblocks[idx] = (
                    st.session_state.textblocks[idx],
                    st.session_state.textblocks[idx + 1],
                )
        with col3:
            if st.button("Delete", key=f"delete_{idx}"):
                st.session_state.textblocks.pop(idx)
                break

    if st.button("Add Textblock"):
        st.session_state.textblocks.append("")

def mode_2_body():
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

def mode_3_body():
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

if __name__ == "__main__":
    main()
