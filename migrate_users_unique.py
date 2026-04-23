import streamlit as st
from database.connection import run_transaction

def migrate():
    print("Starting migration: Adding UNIQUE constraint to users(employee_id)...")
    # First, handle any potential duplicates if they exist (delete older entries)
    # Using a CTE to keep the record with the smallest ID (usually the original)
    cleanup_sql = """
    DELETE FROM users a USING (
      SELECT MIN(id) as keep_id, employee_id
      FROM users
      WHERE employee_id IS NOT NULL
      GROUP BY employee_id
      HAVING COUNT(*) > 1
    ) b
    WHERE a.employee_id = b.employee_id
    AND a.id != b.keep_id;
    """
    run_transaction(cleanup_sql)
    
    # Now add the unique constraint
    sql = "ALTER TABLE users ADD CONSTRAINT unique_employee_id UNIQUE (employee_id);"
    success, msg = run_transaction(sql)
    if success:
        print("Successfully added UNIQUE constraint to users(employee_id).")
    else:
        # If it already exists, just log it
        if "already exists" in msg.lower():
            print("Constraint unique_employee_id already exists.")
        else:
            print(f"Failed to add UNIQUE constraint: {msg}")

if __name__ == "__main__":
    migrate()
