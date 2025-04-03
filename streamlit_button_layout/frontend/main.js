function applyButtonLayout(formId) {
    // Find the form element using the formId
    const form = document.querySelector(`div[data-testid="stForm"][key="${formId}"] div[data-testid="stHorizontalBlock"]`) ||
                 document.querySelector(`div[data-testid="stForm"][key="${formId}"] div[data-testid="column"]`);
    
    if (form) {
        // Apply Flexbox styles for row with wrapping
        form.style.display = "flex";
        form.style.flexDirection = "row";
        form.style.flexWrap = "wrap";
        form.style.gap = "8px";

        // Style the child columns
        const columns = form.children;
        for (let i = 0; i < columns.length; i++) {
            columns[i].style.flex = "0 0 auto";
            columns[i].style.minWidth = "60px";
            // Special styling for the selectbox column (5th column)
            if (i === 4) { // 0-based index, so 4 is the 5th column
                columns[i].style.flex = "1 1 120px";
            }
        }
    }
}

// Streamlit component logic
function onRender(event) {
    const { form_id } = event.detail.args;
    applyButtonLayout(form_id);

    // Tell Streamlit the component is ready
    Streamlit.setComponentValue(null);
    Streamlit.setFrameHeight(0); // This component doesn't render any visible content
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();