import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import datetime

st.write("Test AgGrid with string dates")
df = pd.DataFrame({
    "A": [1, 2], 
    "Date": [datetime.date(2023, 1, 1), datetime.date(2023, 1, 2)]
})

# Convert datetime to string
for col in df.columns:
    if pd.api.types.is_datetime64_any_dtype(df[col]) or isinstance(df[col].dropna().iloc[0] if not df[col].empty else None, (datetime.date, datetime.datetime)):
        df[col] = df[col].astype(str)

gb = GridOptionsBuilder.from_dataframe(df)
go = gb.build()

st.write("Before AgGrid")
AgGrid(df, gridOptions=go)
st.write("After AgGrid")
