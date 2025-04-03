import streamlit.components.v1 as components
import os

# Declare the component, pointing to the frontend build directory
# In production, the frontend will be built and served from this path
_button_row = components.declare_component(
    "button_row",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "build")
)

def button_row(
    block_id: str,
    idx: int,
    chapters: list,
    current_chapter: str,
    total_blocks: int,
    key: str = None
):
    """
    A custom Streamlit component to render a row of buttons with wrapping behavior.

    Args:
        block_id (str): The ID of the block.
        idx (int): The index of the block in the current chapter.
        chapters (list): List of chapter names for the move dropdown.
        current_chapter (str): The current chapter name.
        total_blocks (int): Total number of blocks in the current chapter.
        key (str, optional): A unique key for the component.

    Returns:
        dict: The action triggered by the user (e.g., {"action": "move_up"}).
    """
    # Call the frontend component and pass the necessary arguments
    component_value = _button_row(
        blockId=block_id,
        idx=idx,
        chapters=chapters,
        currentChapter=current_chapter,
        totalBlocks=total_blocks,
        key=key,
        default=None
    )
    return component_value