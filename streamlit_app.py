import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

st.title("My First Streamlit App")

name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}!")

if st.button("Click me!"):
    st.write("Button clicked!")

st.write("This is some text.")

# Example of displaying a dataframe:
import pandas as pd
data = {'col1': [1, 2, 3], 'col2': [4, 5, 6]}
df = pd.DataFrame(data)
st.dataframe(df)