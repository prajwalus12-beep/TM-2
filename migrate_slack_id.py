import streamlit as st
from database.connection import run_transaction

def migrate():
    print("Starting migration: Adding slack_id to employee table...")
    # Add slack_id to employee table
    sql = "ALTER TABLE employee ADD COLUMN IF NOT EXISTS slack_id VARCHAR(100);"
    success, msg = run_transaction(sql)
    if success:
        print("Successfully added slack_id column to employee table.")
    else:
        print(f"Failed to add slack_id column: {msg}")

if __name__ == "__main__":
    migrate()
