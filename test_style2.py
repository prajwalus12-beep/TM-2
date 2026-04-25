import streamlit as st
import pandas as pd

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "name": ["A", "B"],
        "name_updated": [True, False],
        "age": [20, 30],
        "age_updated": [False, True]
    })

def highlight_cells(data):
    styles_df = pd.DataFrame('', index=data.index, columns=data.columns)
    for col in data.columns:
        updated_col = f"{col}_updated"
        if updated_col in data.columns:
            mask = data[updated_col].astype(str).str.lower().isin(['true', '1', 't', 'y', 'yes'])
            styles_df.loc[mask, col] = 'background-color: #fee2e2; color: #dc2626;'
    return styles_df

styled = st.session_state.df.style.apply(highlight_cells, axis=None)

st.data_editor(styled, key="editor")
