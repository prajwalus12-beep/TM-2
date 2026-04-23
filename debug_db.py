
import pandas as pd

from database import get_db_connection, get_all_employees, get_projects_by_employee

def debug_db():
    print("--- Checking get_all_employees types ---")
    df_emps = get_all_employees()
    print(df_emps.head())
    print(df_emps.dtypes)
    
    # Check specific employee 32
    emp_32 = df_emps[df_emps['employee_id'].astype(str) == '32']
    if not emp_32.empty:
        val = emp_32.iloc[0]['employee_id']
        print(f"Emp 32 value: {val!r}, type: {type(val)}")
        
        print("\n--- Calling get_projects_by_employee with value from DF ---")
        res1 = get_projects_by_employee(val)
        print(res1)
        
    print("\n--- Calling get_projects_by_employee with str '32' ---")
    res2 = get_projects_by_employee('32')
    print(res2)

    print("\n--- Calling get_projects_by_employee with int 32 ---")
    res3 = get_projects_by_employee(32)
    print(res3)

if __name__ == "__main__":
    debug_db()
