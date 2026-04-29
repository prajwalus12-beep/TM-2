import psycopg2
import toml
import os

def migrate_add_access_column():
    """Add project_update_access column to employee table."""
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    secrets = toml.load(secrets_path)
    DB_CONFIG = secrets["postgres"]

    print("Connecting to database...")
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    cur = conn.cursor()
    
    try:
        print("Checking if column exists...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='employee' AND column_name='project_update_access';
        """)
        exists = cur.fetchone()
        
        if not exists:
            print("Adding column 'project_update_access' to 'employee' table...")
            cur.execute("ALTER TABLE employee ADD COLUMN project_update_access BOOLEAN DEFAULT FALSE;")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column already exists.")
            
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate_add_access_column()
