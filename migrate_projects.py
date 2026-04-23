import streamlit as st
import psycopg2
import pandas as pd
from contextlib import contextmanager

# Load secrets manually because standalone script might not pick them up correctly
import toml
import os

secrets_path = os.path.join(".streamlit", "secrets.toml")
secrets = toml.load(secrets_path)

DB_CONFIG = secrets["postgres"]
ENCRYPTION_KEY = DB_CONFIG["encryption_key"]

from cryptography.fernet import Fernet

def get_fernet():
    return Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(text):
    if not text: return text
    return get_fernet().encrypt(text.encode()).decode()

def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )

def migrate():
    print("Starting migration...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Migrate Project table
        cur.execute("SELECT project_code, project_name FROM Project")
        projects = cur.fetchall()
        p_count = 0
        for code, name in projects:
            if name and not name.startswith("gAAAAA"):
                enc_name = encrypt_data(name)
                cur.execute("UPDATE Project SET project_name = %s WHERE project_code = %s", (enc_name, code))
                p_count += 1
        
        # Migrate Timesheet table
        cur.execute("SELECT id, project_name FROM Timesheet")
        entries = cur.fetchall()
        t_count = 0
        for eid, name in entries:
            if name and not name.startswith("gAAAAA"):
                enc_name = encrypt_data(name)
                cur.execute("UPDATE Timesheet SET project_name = %s WHERE id = %s", (enc_name, eid))
                t_count += 1
        
        conn.commit()
        print(f"Migration complete! Encrypted {p_count} projects and {t_count} timesheet entries.")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
