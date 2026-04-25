import streamlit as st
import pandas as pd

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'name_updated': [False, True, False]
})

def style_cells(row):
    styles = [''] * len(row)
    if row['name_updated']:
        styles[0] = 'background-color: #fee2e2; color: #dc2626;'
    return styles

styled_df = df.style.apply(style_cells, axis=1)

column_config = {
    'name': st.column_config.TextColumn("Name", disabled=False)
}

st.write("st.data_editor with column_config:")
st.data_editor(styled_df, column_config=column_config, key="editor2")
