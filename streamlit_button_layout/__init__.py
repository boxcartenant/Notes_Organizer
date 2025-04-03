import os
import streamlit.components.v1 as components


# When deploying to production, point to the built frontend files
parent_dir = os.path.dirname(os.path.abspath(__file__))
#build_dir = os.path.join(parent_dir, "frontend", "build")
_button_layout = components.declare_component("button_layout")

def button_layout(form_id, key=None):
    """
    A custom component to apply a row-with-wrapping layout to buttons in a form.

    Args:
        form_id (str): The ID of the form to target (e.g., "actions_{block_id}_{idx}").
        key (str, optional): A unique key for the component.
    """
    return _button_layout(form_id=form_id, key=key, default=None)