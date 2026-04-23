
import psycopg2
import streamlit as st

# Load secrets
try:
    DB_CONFIG = st.secrets["postgres"]
except FileNotFoundError:
    # Fallback for manual run if secrets missing, but user environment implies secrets.toml exists
    # If running as script, might need to mock st.secrets or read file directly.
    # Assuming running via 'streamlit run' or similar context where secrets are available
    # Or just hardcoding/reading toml.
    import toml
    with open(".streamlit/secrets.toml", "r") as f:
        config = toml.load(f)
        DB_CONFIG = config["postgres"]

def run_migration():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cur = conn.cursor()
        
        print("Altering Project table...")
        cur.execute("ALTER TABLE Project ALTER COLUMN project_name TYPE VARCHAR(255);")
        
        print("Altering Timesheet table...")
        cur.execute("ALTER TABLE Timesheet ALTER COLUMN project_name TYPE VARCHAR(255);")
        
        conn.commit()
        cur.close()
        conn.close()
        print("Migration successful: project_name columns updated to VARCHAR(255).")
        
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    run_migration()
