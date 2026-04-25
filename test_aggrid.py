import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from st_aggrid.shared import JsCode

st.set_page_config(layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "project_code": [1, 2],
        "project_name": ["Alpha", "Beta"],
        "project_name_updated": [False, True],
        "status": ["In progress", "Complete"],
        "status_updated": [False, False]
    })

df = st.session_state.df

gb = GridOptionsBuilder.from_dataframe(df)

# Hide _updated columns
gb.configure_column("project_name_updated", hide=True)
gb.configure_column("status_updated", hide=True)

# Make other columns editable
gb.configure_column("project_name", editable=True, cellStyle=JsCode("""
function(params) {
    if (params.data.project_name_updated === true) {
        return {'backgroundColor': '#fee2e2', 'color': '#dc2626'};
    }
    return null;
}
"""))
gb.configure_column("status", editable=True, cellStyle=JsCode("""
function(params) {
    if (params.data.status_updated === true) {
        return {'backgroundColor': '#fee2e2', 'color': '#dc2626'};
    }
    return null;
}
"""))

go = gb.build()

response = AgGrid(
    df,
    gridOptions=go,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True
)

edited_df = response['data']
if not edited_df.equals(df):
    st.write("Data changed!")
    st.session_state.df = edited_df
    # In real code, we would set project_name_updated = True here and save
    st.rerun()
