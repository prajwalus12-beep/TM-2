import streamlit as st
from contextlib import contextmanager

# Load secrets
DB_CONFIG = st.secrets.get("postgres", {})

@st.cache_resource
def get_supabase_client():
    """Initialize and return a cached Supabase Client."""
    try:
        from supabase import create_client
        url = DB_CONFIG.get("SUPABASE_URL")
        key = DB_CONFIG.get("SUPABASE_ANON_KEY")
        if not url or not key:
            st.error("""
            **Supabase configuration missing!**
            
            Since you (correctly) added `secrets.toml` to `.gitignore`, it is not on GitHub. 
            You must manually add your secrets to the **Streamlit Cloud Dashboard**:
            1. Go to your app settings on Streamlit Cloud.
            2. Open the **Secrets** section.
            3. Paste your `[postgres]` configuration there.
            """)
            return None
        return create_client(url, key)
    except ImportError:
        st.error("Supabase library not installed. Please run: pip install supabase")
        return None

# Placeholder functions to maintain compatibility during migration
# These will be phased out as queries.py is updated
def run_query(query, params=None, fetch_all=True):
    st.error("Direct SQL queries are deprecated. Please update this call to use Supabase SDK.")
    return None

def run_transaction(query, params=None):
    st.error("Direct SQL transactions are deprecated. Please update this call to use Supabase SDK.")
    return False, "Deprecated"

@contextmanager
def get_db_connection():
    st.error("get_db_connection is deprecated. Use get_supabase_client() instead.")
    yield None
